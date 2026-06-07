"""
Scratch generator: turns a pool of candidate integrands into verified
NewProblem(...) source code, ready to paste into problems_registry.py.

Each candidate stores its integrand (and any bounds) as a *source string* —
e.g. "x**2 * sp.log(x)" — so we can both eval it for verification and emit it
back verbatim. For each candidate we:
  1. Compute the true antiderivative (or definite value) with SymPy.
  2. Render it to LaTeX, prettify it, and KEEP the prettified form only if it
     still passes the same verify() gate the runner uses. Otherwise fall back to
     raw SymPy LaTeX (guaranteeing every emitted entry verifies).
  3. Skip anything whose problem text already exists in the registry.

Run:  uv run python -m migrations._generate_candidates          # emit registry source
      uv run python -m migrations._generate_candidates --stats  # just counts
"""
import sys

import sympy as sp

from app.utils import sympy_to_latex
from migrations.problem_models import NewProblem
from migrations.problems_registry import PROBLEMS as EXISTING

x = sp.Symbol("x")

_OPNAME = {
    "atan": "arctan", "asin": "arcsin", "acos": "arccos",
    "acot": "arccot", "asec": "arcsec", "acsc": "arccsc",
}


def _fix_inverse(s: str) -> str:
    """Map SymPy's \\operatorname{atan} etc. to forms the app parser accepts."""
    for k, v in _OPNAME.items():
        s = s.replace(rf"\operatorname{{{k}}}", rf"\{v}")
    return s


def _prettify(s: str) -> str:
    """Cosmetic cleanup for display: collapse \\left(\\right), \\log -> \\ln,
    and \\int\\limits -> \\int to match the existing hand-authored entries."""
    s = s.replace(r"{\left(", "(").replace(r"\right)}", ")")
    s = s.replace(r"\left(", "(").replace(r"\right)", ")")
    s = s.replace(r"\log", r"\ln")
    s = s.replace(r"\int\limits", r"\int")
    s = s.replace("( ", "(").replace(" )", ")")  # tidy spacing from collapsed \left\right
    return s


def _eval(src: str):
    return eval(src, {"sp": sp, "x": x})  # noqa: S307 — trusted local source


def _candidate_forms(truth: sp.Expr, is_indef: bool) -> list[str]:
    """Displayable LaTeX forms for `truth`, best (prettiest) first.

    Includes a log-rewritten variant so asinh/acosh/atanh results, which the
    LaTeX parser can't read, come through as logarithms.
    """
    exprs = [truth]
    try:
        log_form = truth.rewrite(sp.log)
        if log_form != truth:
            exprs.append(log_form)
    except Exception:  # noqa: BLE001, S110
        pass

    forms: list[str] = []
    for form in exprs:
        forms.append(_fix_inverse(_prettify(sympy_to_latex(form, is_indefinite=is_indef))))
        forms.append(_fix_inverse(sympy_to_latex(form, is_indefinite=is_indef)))
    return forms


def _verify_solution(solution: str, *, integrand, itype, lower, upper, trusted) -> bool:
    """Single source of truth: does this (solution, integrand) pass NewProblem.verify()?"""
    try:
        np = NewProblem(
            problem="placeholder", solution=solution, integrand=integrand,
            integral_type=itype, lower=lower, upper=upper,
            topic="placeholder", difficulty="easy",
            progressive_hints=["placeholder"], trusted=trusted,
        )
    except Exception:  # noqa: BLE001
        return False
    ok, _ = np.verify()
    return ok


def _problem_latex(integrand, integral_type, lower, upper) -> str:
    if integral_type == "definite":
        expr = sp.Integral(integrand, (x, lower, upper))
    else:
        expr = sp.Integral(integrand, x)
    return _fix_inverse(_prettify(sp.latex(expr)))


def build(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (verified, failed) candidate dicts with computed LaTeX."""
    existing_texts = {p.problem for p in EXISTING}
    verified, failed = [], []
    seen = set()

    for c in candidates:
        itype = c.get("integral_type", "indefinite")
        is_indef = itype == "indefinite"
        trusted = c.get("trusted", False)
        try:
            ig = _eval(c["isrc"])
            lower = _eval(c["lsrc"]) if c.get("lsrc") else None
            upper = _eval(c["usrc"]) if c.get("usrc") else None
        except Exception as e:  # noqa: BLE001
            failed.append({**c, "reason": f"eval failed: {e}"})
            continue

        vargs = dict(integrand=ig, itype=itype, lower=lower, upper=upper, trusted=trusted)

        # A candidate may supply a hand-authored solution (for integrals SymPy
        # can't do, or whose auto-form is ugly). Otherwise generate from SymPy.
        if c.get("solution"):
            sol = c["solution"] if _verify_solution(c["solution"], **vargs) else None
        else:
            try:
                truth = sp.integrate(ig, x) if is_indef else sp.integrate(ig, (x, lower, upper))
            except Exception as e:  # noqa: BLE001
                failed.append({**c, "reason": f"integrate raised: {e}"})
                continue
            if truth is None or truth.has(sp.Integral):
                failed.append({**c, "reason": "no closed form"})
                continue
            sol = next(
                (f for f in _candidate_forms(truth, is_indef) if _verify_solution(f, **vargs)),
                None,
            )

        if sol is None:
            failed.append({**c, "reason": "solution did not verify against integrand"})
            continue

        prob = c.get("problem") or _problem_latex(ig, itype, lower, upper)
        if prob in existing_texts or prob in seen:
            failed.append({**c, "reason": "duplicate problem text"})
            continue
        seen.add(prob)

        verified.append({**c, "problem": prob, "solution": sol, "integral_type": itype})

    return verified, failed


def _lit(s: str) -> str:
    """Emit a Python string literal. Prefer a readable raw string (r"...") when
    safe; otherwise fall back to repr() (always correct)."""
    if '"' not in s and "\n" not in s and not s.endswith("\\"):
        return f'r"{s}"'
    return repr(s)


def _emit(v: dict) -> str:
    """Render one verified candidate as NewProblem(...) source."""
    lines = [
        "    NewProblem(",
        f"        problem={_lit(v['problem'])},",
        f"        solution={_lit(v['solution'])},",
        f"        integrand={v['isrc']},",
    ]
    if v["integral_type"] == "definite":
        lines.append('        integral_type="definite",')
        lines.append(f"        lower={v['lsrc']},")
        lines.append(f"        upper={v['usrc']},")
    if v.get("trusted"):
        lines.append("        trusted=True,")
    lines.append(f"        topic={_lit(v['topic'])},")
    lines.append(f"        difficulty={_lit(v['difficulty'])},")
    lines.append("        progressive_hints=[")
    for h in v["hints"]:
        lines.append(f"            {_lit(h)},")
    lines.append("        ],")
    lines.append("    ),")
    return "\n".join(lines)


if __name__ == "__main__":
    from migrations._candidate_pool import CANDIDATES

    verified, failed = build(CANDIDATES)

    if "--stats" in sys.argv:
        print(f"candidates: {len(CANDIDATES)}   verified: {len(verified)}   failed: {len(failed)}")
        by_topic: dict[str, int] = {}
        by_diff: dict[str, int] = {}
        for v in verified:
            by_topic[v["topic"]] = by_topic.get(v["topic"], 0) + 1
            by_diff[v["difficulty"]] = by_diff.get(v["difficulty"], 0) + 1
        print("\nby topic:")
        for k, n in sorted(by_topic.items()):
            print(f"  {n:3d}  {k}")
        print("\nby difficulty:")
        for k, n in sorted(by_diff.items()):
            print(f"  {n:3d}  {k}")
        if failed:
            print("\nFAILURES:")
            for f in failed:
                print(f"  - [{f['reason']}]  {f['isrc']}")
        sys.exit(0)

    print("\n".join(_emit(v) for v in verified))
