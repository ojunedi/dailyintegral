#pyright: basic
import logging
import re
import signal
import threading
from contextlib import contextmanager
from typing import Optional

import sympy as sp

logger = logging.getLogger(__name__)

# Hard wall-clock ceiling for a single grade. SymPy's diff/simplify run on
# attacker-controlled expressions; deeply nested inputs can spin for many
# seconds, tying up request workers. 5s is far more than any legitimate answer
# needs. NOTE: this only bounds *interruptible* (pure-Python) work — a giant
# bignum power computes in a C routine that ignores the signal, so the
# complexity guard below is the primary defense and this is the backstop.
_GRADE_TIMEOUT_SECONDS = 5.0

# Structural limits on a user-supplied expression, checked before any expensive
# SymPy work. These reject denial-of-service payloads (e.g. 9^{9^{9999999}},
# 999999!) whose cost is in materializing an astronomically large number — work
# that happens in C and cannot be interrupted by the wall-clock guard. The
# thresholds sit far above any legitimate integral answer.
_MAX_OPS = 200          # total operation count of the parsed expression
_MAX_EXPONENT = 1000    # magnitude of a numeric power exponent
_MAX_FACTORIAL_ARG = 1000


def _warmup_latex_parser() -> None:
    """Force SymPy's lazy imports to load in a normal (evaluated) context.

    The DoS gate parses inside ``with sp.evaluate(False)``. On a cold process
    that very first call triggers a lazy ``sympy.physics.units`` import that
    raises under disabled evaluation. Doing one ordinary parse at import time
    loads those modules so the gate is safe. Best-effort — never blocks import.
    """
    try:
        from sympy.parsing.latex import parse_latex
        parse_latex(r'x^2 + 1')
    except Exception as e:  # noqa: BLE001
        logger.warning(f"LaTeX parser warmup failed: {e}")


_warmup_latex_parser()


def _is_safe_small_number(e: sp.Expr) -> bool:
    """True iff a constant (free-symbol-less) expression is a small, bounded
    value that cannot blow up when evaluated.

    Inspected structurally — never evaluated — so it is safe to call on a power
    tower. Allows arithmetic over bounded numeric literals and *negative*-integer
    inner powers (the q^{-1} denominators that fractional exponents like 3/2
    decompose into under disabled evaluation), but rejects positive nested powers
    and factorials (the 9^9 / 999999! blow-ups).
    """
    if e.is_Number:
        try:
            return abs(float(e)) <= _MAX_EXPONENT
        except (TypeError, ValueError, OverflowError):
            return False
    if isinstance(e, (sp.Add, sp.Mul)):
        return all(_is_safe_small_number(a) for a in e.args)
    if isinstance(e, sp.Pow):
        base, exp = e.base, e.exp
        # Only denominator-style inversions: a negative integer exponent keeps
        # the value in (0, 1] for |base| >= 1, so it can never blow up.
        if exp.is_Integer and int(exp) < 0:
            return _is_safe_small_number(base)
        return False
    return False


def _within_complexity_budget(expr: Optional[sp.Expr]) -> bool:
    """Reject expressions whose evaluation would be pathologically expensive.

    Must be called on an expression parsed with evaluation DISABLED, so that a
    power tower like 9^{9^{9999999}} (or the single-digit 9^{9^9}) is still an
    un-collapsed ``Pow`` tree we can inspect — rather than an astronomically
    large integer that already hung the parser while being built.

    A power node is dangerous when its exponent evaluates to a large number.
    We distinguish three exponent shapes without ever materializing a huge value:
      - atomic literal (x^2, x^1000)      → bound its magnitude directly;
      - composite numeric (3/2, or 9^9)   → allow only small rationals;
      - symbolic (e^{x^2}, 2^x)           → always safe, never materializes.
    """
    if expr is None:
        return True
    try:
        if expr.count_ops() > _MAX_OPS:
            return False

        for node in sp.preorder_traversal(expr):
            if isinstance(node, sp.Pow):
                exp = node.exp
                if exp.is_Number:
                    try:
                        if abs(float(exp)) > _MAX_EXPONENT:
                            return False
                    except (TypeError, ValueError, OverflowError):
                        return False
                elif exp.is_number and not _is_safe_small_number(exp):
                    # Composite constant exponent that isn't a small rational —
                    # i.e. a numeric tower like 9^9. Would materialize a huge number.
                    return False
            elif isinstance(node, sp.factorial):
                arg = node.args[0]
                if arg.is_Number:
                    try:
                        if abs(float(arg)) > _MAX_FACTORIAL_ARG:
                            return False
                    except (TypeError, ValueError, OverflowError):
                        return False
                elif arg.is_number and not _is_safe_small_number(arg):
                    return False
        return True
    except Exception as e:  # noqa: BLE001 — any analysis failure ⇒ refuse to grade
        logger.warning(f"Complexity analysis failed; rejecting expression: {e}")
        return False


class GradingTimeout(BaseException):
    """Raised when a grading computation exceeds the wall-clock ceiling.

    Subclasses BaseException (not Exception) so the broad ``except Exception``
    guards inside the grading core can't swallow the alarm and let a
    pathological computation run past its budget.
    """


@contextmanager
def _time_limit(seconds: float):
    """Bound a CPU-bound block with a wall-clock timeout.

    Uses SIGALRM, which only fires on Unix and only in the main thread — that
    covers the production path (gunicorn sync workers, Vercel) and the test
    runner. Where SIGALRM is unavailable (Windows dev, threaded workers) it
    degrades to a no-op so grading never breaks; input is still bounded to
    1000 chars upstream.
    """
    if not hasattr(signal, "SIGALRM") or threading.current_thread() is not threading.main_thread():
        yield
        return

    def _handler(signum, frame):
        raise GradingTimeout()

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)

# Real sample points and tolerance for the numeric equality fallback. These are
# the same values used by the upload gate's derivative check, so the gate and the
# production grader agree by construction.
_SAMPLE_POINTS = [-0.8, -0.5, -0.2, 0.2, 0.5, 0.8, 1.3, 1.7, 2.1, 2.6]
_REL_TOL = 1e-6
_MIN_SAMPLES = 4


def _is_finite_complex(z: complex) -> bool:
    import math
    return math.isfinite(z.real) and math.isfinite(z.imag)


def expressions_match_numerically(a: sp.Expr, b: sp.Expr) -> bool:
    """Robust, conservative numeric equality test for two SymPy expressions.

    Used as a fallback when sp.simplify() can't decide — differentiation and
    simplification are incomplete, so a correct-but-hairy expression can slip
    through symbolically. This evaluates instead:

      - if either side has a free variable: sample real points and require enough
        agreeing finite samples, with a single finite mismatch failing fast;
      - if both are constants: compare evalf() directly.

    A non-decidable / all-non-finite situation returns False (never a pass).
    """
    a = sp.sympify(a)
    b = sp.sympify(b)
    free = (a.free_symbols | b.free_symbols) - {sp.Symbol("C")}

    if not free:
        try:
            av, bv = complex(a.evalf()), complex(b.evalf())
        except (TypeError, ValueError):
            return False
        if not (_is_finite_complex(av) and _is_finite_complex(bv)):
            return False
        return abs(av - bv) <= _REL_TOL * max(1.0, abs(bv))

    var = sorted(free, key=str)[0]
    matched = 0
    for p in _SAMPLE_POINTS:
        try:
            av = complex(a.subs(var, p).evalf())
            bv = complex(b.subs(var, p).evalf())
        except (TypeError, ValueError):
            continue
        if not (_is_finite_complex(av) and _is_finite_complex(bv)):
            continue
        if abs(av - bv) > _REL_TOL * max(1.0, abs(bv)):
            return False
        matched += 1
    return matched >= _MIN_SAMPLES


def is_equivalent_up_to_constant(
    user_answer: Optional[sp.Expr],
    correct_answer: Optional[sp.Expr],
    is_indefinite: bool = True,
) -> bool:
    """
    Check if the user's answer is equivalent to the correct answer up to a constant.

    Args:
        user_answer (sympy.Expr or None): The answer provided by the user
        correct_answer (sympy.Expr or None): The correct answer from the problem source

    Returns:
        bool: True if the answers are equivalent up to a constant, False otherwise
    """
    if user_answer is None or correct_answer is None:
        logger.warning("One of the answers is None")
        return False

    try:
        with _time_limit(_GRADE_TIMEOUT_SECONDS):
            return _equivalence_core(user_answer, correct_answer, is_indefinite)
    except GradingTimeout:
        logger.warning("Grading timed out; treating answer as incorrect")
        return False
    except Exception as e:
        logger.error(f"Error in equivalence checking: {e}")
        return False


def _equivalence_core(
    user_answer: sp.Expr,
    correct_answer: sp.Expr,
    is_indefinite: bool,
) -> bool:
    """Symbolic equivalence check. Run only inside is_equivalent_up_to_constant,
    which bounds it with a wall-clock timeout."""
    try:
        # Convert to sympy expressions if they're not already
        user_answer = sp.sympify(user_answer)
        correct_answer = sp.sympify(correct_answer)

        # Definite integrals evaluate to a single number, so compare VALUES — never
        # "up to a constant". parse_latex renders pi/e as plain symbols, so a value
        # like pi/4 looks like it has a free variable; without normalizing it first,
        # it would fall into the derivative path below, which is vacuously true for
        # constants (d/d(pi) ignores any added constant, accepting wrong answers like
        # pi/4 + 1 as equal to pi/4).
        if not is_indefinite:
            norm = {sp.Symbol('e'): sp.E, sp.Symbol('pi'): sp.pi}
            u = user_answer.subs(norm)
            c = correct_answer.subs(norm)
            try:
                if sp.simplify(u - c) == 0:
                    return True
            except Exception:  # noqa: BLE001 — simplify can choke on hairy constants
                pass
            # Numeric fallback for equal-but-messy constants (nested radicals, etc.).
            return expressions_match_numerically(u, c)

        # ---- Indefinite: equivalence up to an additive constant ----
        # Check if derivatives are equal (eliminates constants).
        # Find the variable in the expression (usually 'x' for integrals)
        variables = user_answer.free_symbols.union(correct_answer.free_symbols)
        if not variables:
            # Two bare constants both fold into +C, so they're interchangeable.
            return True

        # Filter out constant symbols and use main variable (typically 'x')
        main_variables = variables - {sp.Symbol('C')}
        if not main_variables:
            # If only constant symbols, they're equivalent up to a constant
            return True

        # Use the first main variable found (typically 'x')
        var = list(main_variables)[0]

        user_derivative = sp.diff(user_answer, var)
        correct_derivative = sp.diff(correct_answer, var)

        # Simplify and check if derivatives are equal
        difference = sp.simplify(user_derivative - correct_derivative)

        logger.info(f"User derivative: {user_derivative}")
        logger.info(f"Correct derivative: {correct_derivative}")
        logger.info(f"Derivative difference: {difference}")

        # Check if the difference is zero
        if difference == 0:
            return True

        # Method 2: check if the answers themselves differ only by a constant
        expr_difference = sp.simplify(user_answer - correct_answer)
        logger.info(f"Expression difference: {expr_difference}")

        # Exclude the constant symbol 'C' from consideration
        difference_vars = expr_difference.free_symbols - {sp.Symbol('C')}
        if len(difference_vars) == 0:
            return True

        # Method 3: numeric fallback — simplify is incomplete and can fail to
        # crush an equal derivative difference to 0. Equivalence up to a constant
        # means the derivatives match, so compare them numerically.
        return expressions_match_numerically(user_derivative, correct_derivative)

    except Exception as e:
        logger.error(f"Error in equivalence checking: {e}")
        return False


def parse_latex_safely(latex_str: str) -> Optional[sp.Expr]:
    """
    Safely parse LaTeX string to sympy expression with error handling.

    Parsing is identical for definite and indefinite integrals; the caller
    enforces the +C rule separately via has_constant_of_integration().

    Args:
        latex_str (str): LaTeX string to parse

    Returns:
        sympy.Expr or None: Parsed expression or None if parsing fails
    """
    if not latex_str or not latex_str.strip():
        return None

    # Input validation - check for potentially dangerous content
    latex_str = latex_str.strip()

    # Check length to prevent DoS attacks
    if len(latex_str) > 1000:
        logger.warning(f"LaTeX input too long: {len(latex_str)} characters")
        return None

    # Check for potentially dangerous patterns
    dangerous_patterns = [
        '\\input', '\\include', '\\write', '\\read', '\\openin', '\\openout',
        '\\immediate', '\\special', '\\catcode', '\\def', '\\let'
    ]
    latex_lower = latex_str.lower()
    for pattern in dangerous_patterns:
        if pattern in latex_lower:
            logger.warning(f"Potentially dangerous LaTeX command detected: {pattern}")
            return None

    try:
        from sympy.parsing.latex import parse_latex

        # Clean up common LaTeX issues
        latex_str = latex_str.strip()

        # mathlive renders absolute values as \left|...\right|, but sympy's LaTeX
        # parser fails to apply a preceding function to them (e.g. \ln\left|x+1\right|
        # errors, and \frac{1}{2}\left(\ln\left|x+1\right|\right) silently drops the
        # log and returns just 1/2). Plain | | bars parse correctly, so normalize.
        latex_str = latex_str.replace(r'\left|', '|').replace(r'\right|', '|')

        # Normalize function names to proper LaTeX commands using regex, avoiding overlaps
        # Fix \sqrt without braces: \sqrt2 -> \sqrt{2}, \sqrtx -> \sqrt{x}
        latex_str = re.sub(r'\\sqrt([^{\[\s\\])', r'\\sqrt{\1}', latex_str)

        # Fix previously split forms like "\arc\sin(x)" -> "\arcsin(x)"
        latex_str = re.sub(r"\\arc\\(sin|cos|tan|sec|csc|cot)\b", r"\\arc\1", latex_str)

        # Add backslashes for inverse trig functions when missing (e.g., arcsin(x) -> \arcsin(x))
        for fname in ["arcsin", "arccos", "arctan", "arcsec", "arccsc", "arccot"]:
            pattern = rf"(?<!\\){fname}\("
            replacement = rf"\\{fname}("
            latex_str = re.sub(pattern, replacement, latex_str, flags=re.IGNORECASE)

        # Add backslashes for basic functions only when not part of a longer word (avoid 'arc' prefix)
        for fname in ["sin", "cos", "tan", "ln", "log"]:
            pattern = rf"(?<![\\A-Za-z]){fname}\("
            replacement = rf"\\{fname}("
            latex_str = re.sub(pattern, replacement, latex_str, flags=re.IGNORECASE)

        # For indefinite integrals, if user included +C we keep it;
        # if they didn't, we still parse but the caller should reject via
        # has_constant_of_integration() check.

        # DoS gate: parse first with evaluation DISABLED so a power tower like
        # 9^{9^{9999999}} stays an inspectable Pow tree instead of being
        # materialized into an astronomically large integer (which hangs the
        # parser, in uninterruptible C code, before grading even starts). Only
        # if the structure is within budget do we parse normally (evaluated).
        with sp.evaluate(False):
            unevaluated = parse_latex(latex_str)
        if not _within_complexity_budget(unevaluated):
            logger.warning(f"Rejected over-complex LaTeX input: {latex_str}")
            return None

        parsed_expr = parse_latex(latex_str)
        logger.info(f"Successfully parsed LaTeX: {latex_str} -> {parsed_expr}")
        return parsed_expr

    except Exception as e:
        logger.error(f"Failed to parse LaTeX '{latex_str}': {e}")
        return None


def has_constant_of_integration(latex_str: str) -> bool:
    """
    Check if a LaTeX string contains a constant of integration (+C or -C).
    Returns False if C only appears as part of another token (e.g. \\cos).
    """
    if not latex_str:
        return False
    # Match standalone C preceded by + or - (with optional spaces)
    # Negative lookbehind: not preceded by a backslash or letter
    # Negative lookahead: not followed by a letter, digit, or underscore
    return bool(re.search(r'(?<![\\A-Za-z])[+-]\s*C(?![A-Za-z0-9_])', latex_str))


def sympy_to_latex(expr: sp.Expr, is_indefinite: bool = True) -> str:
    """
    Convert a SymPy expression to LaTeX format for display.
    For indefinite integrals, ensures constant of integration (C) appears at the end.
    For definite integrals, strips any C that may have been parsed.

    Args:
        expr (sympy.Expr): SymPy expression to convert
        is_indefinite (bool): Whether this is an indefinite integral (default True)

    Returns:
        str: LaTeX representation of the expression
    """
    try:
        C_symbol = sp.Symbol('C')

        # For definite integrals, remove C if present
        if not is_indefinite and C_symbol in expr.free_symbols:
            expr = expr.subs(C_symbol, 0)
            return sp.latex(expr)

        # Check if the expression contains the constant C
        if C_symbol in expr.free_symbols:
            # Separate the constant C from the rest of the expression
            expr_without_C = expr.subs(C_symbol, 0)
            C_coeff = expr.coeff(C_symbol, 1)  # Get coefficient of C

            if C_coeff is not None:
                # Format as: main_expression + C (or - C if negative)
                main_latex = sp.latex(expr_without_C)

                if C_coeff == 1:
                    return f"{main_latex} + C"
                elif C_coeff == -1:
                    return f"{main_latex} - C"
                else:
                    # Handle cases like 2*C or -3*C
                    C_latex = sp.latex(C_coeff)
                    if C_coeff > 0:
                        return f"{main_latex} + {C_latex} C"
                    else:
                        return f"{main_latex} {C_latex} C"  # C_latex already has the minus

        # If no C or couldn't separate it, use default latex
        return sp.latex(expr)
    except Exception as e:
        logger.error(f"Error converting SymPy expression to LaTeX: {e}")
        return str(expr)
