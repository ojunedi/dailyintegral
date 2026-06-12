# pyright: basic
"""
AI-generated, attempt-aware hints.

Two stages:
  1. SymPy diagnostics: compare the user's attempt against the stored solution
     and produce grounded findings (missing +C, coefficient off by a factor,
     sign flip, derivative mismatch, ...). This runs locally and never guesses.
  2. Claude turns those findings into a single targeted nudge. The model never
     sees the solution itself — only the integrand and the diagnostic facts —
     so it cannot leak the answer verbatim.
"""
import logging
from typing import Optional

import sympy as sp
from pydantic import BaseModel, Field

from app.models import ProblemModel
from app.utils import (
    has_constant_of_integration,
    is_equivalent_up_to_constant,
    parse_latex_safely,
)

logger = logging.getLogger(__name__)

HINT_MODEL = "claude-opus-4-8"

_SYSTEM_PROMPT = """You are the hint engine for Daily Integral, a calculus practice app. \
The user is working on an integral and asked for help. You receive the problem, their \
current attempt (possibly empty or malformed), and diagnostic facts computed symbolically \
with SymPy. Produce exactly ONE targeted nudge.

Hard rules:
- NEVER state the antiderivative, the value of a definite integral, or any expression \
equivalent to either. Never write the corrected version of the user's attempt.
- Give the smallest piece of information that unblocks them — name the kind of mistake \
or the technique to reconsider, not the fix itself.
- 1-3 sentences, friendly but direct. Wrap all math in $...$ (inline LaTeX).
- Treat the diagnostic facts as ground truth; never contradict them or speculate beyond them.
- If the facts say the attempt is already mathematically correct, say so and point at \
formatting instead (e.g. the missing $+C$).
- If the attempt could not be parsed, point at the likely LaTeX/notation issue rather \
than the calculus.
- Do not repeat a hint the user has already seen (the static hints are provided)."""


class HintOutput(BaseModel):
    """Schema the model must return."""

    hint: str = Field(
        description=(
            "One targeted hint, 1-3 sentences, inline math wrapped in $...$, "
            "never revealing the antiderivative or definite-integral value"
        )
    )


def _main_var(*exprs: Optional[sp.Expr]) -> sp.Symbol:
    """Pick the integration variable (usually x), ignoring constant symbols."""
    free: set = set()
    for e in exprs:
        if e is not None:
            free |= e.free_symbols
    free -= {sp.Symbol('C'), sp.Symbol('e'), sp.Symbol('pi')}
    return sorted(free, key=str)[0] if free else sp.Symbol('x')


def _constant_ratio(a: sp.Expr, b: sp.Expr) -> Optional[sp.Expr]:
    """Return r if a == r*b for a nonzero constant r, else None."""
    try:
        ratio = sp.simplify(a / b)
        if ratio.free_symbols:
            return None
        if ratio == 0 or ratio == sp.zoo or ratio == sp.nan:
            return None
        return ratio
    except Exception:  # noqa: BLE001 — simplify can choke on hairy expressions
        return None


def _diagnose_indefinite(attempt: sp.Expr, solution: sp.Expr) -> list[str]:
    facts = []
    var = _main_var(solution, attempt)
    integrand = sp.simplify(sp.diff(solution, var))
    d_attempt = sp.diff(attempt.subs(sp.Symbol('C'), 0), var)

    facts.append(f"The integrand is ${sp.latex(integrand)}$.")
    facts.append(
        f"Differentiating the user's attempt gives ${sp.latex(d_attempt)}$, "
        "which does NOT match the integrand."
    )

    ratio = _constant_ratio(d_attempt, integrand)
    if ratio is not None and ratio != 1:
        facts.append(
            f"The derivative of the attempt equals ${sp.latex(ratio)}$ times the integrand — "
            "the structure/technique is right but a constant coefficient is wrong "
            f"(off by a factor of ${sp.latex(ratio)}$)."
        )
        if ratio == -1:
            facts.append("Specifically, the attempt has the wrong overall sign.")
    else:
        try:
            diff_expr = sp.simplify(d_attempt - integrand)
            facts.append(
                "The derivative of the attempt differs from the integrand by "
                f"${sp.latex(diff_expr)}$."
            )
        except Exception:  # noqa: BLE001
            pass
    return facts


def _diagnose_definite(attempt: sp.Expr, solution: sp.Expr) -> list[str]:
    facts = []
    norm = {sp.Symbol('e'): sp.E, sp.Symbol('pi'): sp.pi}
    try:
        av = complex(attempt.subs(norm).evalf())
        cv = complex(solution.subs(norm).evalf())
    except (TypeError, ValueError):
        facts.append("The attempt does not evaluate to a number, but this definite integral has a numeric value.")
        return facts

    facts.append("The attempt evaluates to a number, but not the correct one.")
    if abs(cv) > 1e-12:
        r = av / cv
        if abs(r.imag) < 1e-9:
            if abs(r.real + 1) < 1e-6:
                facts.append("The attempt is exactly the NEGATIVE of the correct value — a sign error.")
            elif abs(r.real) > 1e-9 and abs(r.real - 1) > 1e-6 and abs(round(1 / r.real) - 1 / r.real) < 1e-6:
                facts.append(
                    f"The attempt is the correct value divided by {round(1 / r.real)} — "
                    "a constant factor was likely dropped."
                )
            elif abs(round(r.real) - r.real) < 1e-6 and abs(r.real) > 1:
                facts.append(
                    f"The attempt is {round(r.real)} times the correct value — "
                    "an extra constant factor crept in."
                )
    return facts


def diagnose_attempt(attempt_latex: str, problem: ProblemModel) -> list[str]:
    """Produce grounded findings about the user's attempt. Never raises."""
    facts: list[str] = []
    is_indefinite = problem.integral_type != 'definite'

    attempt = parse_latex_safely(attempt_latex)
    if attempt is None:
        facts.append(
            "The attempt could not be parsed as a mathematical expression — "
            "most likely malformed LaTeX or notation the parser doesn't accept."
        )
        return facts

    if is_indefinite and not has_constant_of_integration(attempt_latex):
        facts.append("The attempt is missing the constant of integration ($+C$).")

    solution = parse_latex_safely(problem.solution)
    if solution is None:
        return facts

    try:
        if is_equivalent_up_to_constant(attempt, solution, is_indefinite=is_indefinite):
            facts.append(
                "The attempt is mathematically EQUIVALENT to the correct answer. "
                "Any remaining issue is formatting, not calculus."
            )
            return facts

        if is_indefinite:
            facts.extend(_diagnose_indefinite(attempt, solution))
        else:
            facts.extend(_diagnose_definite(attempt, solution))
    except Exception as e:  # noqa: BLE001 — diagnostics are best-effort
        logger.warning(f"Hint diagnostics failed: {e}")

    return facts


def _build_user_message(problem: ProblemModel, attempt: Optional[str], facts: list[str]) -> str:
    lines = [
        f"Problem: ${problem.latex_problem or problem.problem}$",
        f"Integral type: {problem.integral_type}",
        f"Difficulty: {problem.difficulty}",
    ]
    if problem.topic:
        lines.append(f"Topic: {problem.topic}")
    if problem.progressive_hints:
        lines.append("Static hints the user may have already seen:")
        lines.extend(f"  - {h}" for h in problem.progressive_hints)

    if attempt and attempt.strip():
        lines.append(f"User's current attempt (raw LaTeX): {attempt.strip()}")
    else:
        lines.append("The user has not entered an attempt yet — give a strategy-level nudge "
                     "(which technique or substitution to consider) that goes beyond the static hints.")

    if facts:
        lines.append("Diagnostic facts (SymPy, ground truth):")
        lines.extend(f"  - {f}" for f in facts)

    lines.append("Write the single best hint for this user right now.")
    return "\n".join(lines)


def generate_hint(
    problem: ProblemModel,
    attempt: Optional[str],
    api_key: str,
    timeout: float = 30.0,
) -> Optional[str]:
    """Generate one targeted hint. Returns None if the model declined or returned nothing."""
    import anthropic

    facts = diagnose_attempt(attempt, problem) if attempt and attempt.strip() else []
    user_message = _build_user_message(problem, attempt, facts)

    client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=1)
    response = client.messages.parse(
        model=HINT_MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_format=HintOutput,
    )

    if response.stop_reason == "refusal":
        logger.warning("Hint model refused the request")
        return None

    parsed = response.parsed_output
    return parsed.hint if parsed else None
