"""
Verify every problem in the registry and upload new/updated ones to Supabase.

Pipeline:
  1. Verify all registry entries against SymPy (hard gate — if anything fails,
     nothing is uploaded).
  2. Fetch existing rows from Supabase; match by problem text.
       - already present → reuse its id + date, update all other fields
       - new             → assign next available id and date
  3. Construct ProblemModel for each row (guarantees the API can serve it).
  4. Upsert all rows on the id primary key (idempotent; safe to re-run).

Usage:
    uv run python -m migrations.add_problems            # verify + upload
    uv run python -m migrations.add_problems --check    # verify only, no upload
"""
import os
import sys
from datetime import date, timedelta

from dotenv import load_dotenv
from pydantic import ValidationError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def verify_all() -> bool:
    from migrations.problems_registry import PROBLEMS

    failures = []
    for p in PROBLEMS:
        ok, msg = p.verify()
        if ok:
            # Also confirm the displayed problem LaTeX renders the declared
            # integrand — verify() only checks the solution.
            ok, msg = p.problem_matches_integrand()
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {p.integral_type:10s} {p.problem[:45]:45s} {msg}")
        if not ok:
            failures.append(p.problem)

    print(f"\n{len(PROBLEMS) - len(failures)}/{len(PROBLEMS)} passed")
    if failures:
        print("FAILED:", failures)
    return not failures


def _independent_antiderivative(integrand, x):
    """A SymPy antiderivative confirmed correct independently (d/dx == integrand),
    usable as a *different form* to exercise the grader without being tautological.
    Returns None when SymPy can't produce a trustworthy one."""
    import sympy as sp

    try:
        g = sp.integrate(integrand, x)
        if g is None or g.has(sp.Integral):
            return None
        return g if sp.diff(g, x).equals(integrand) else None
    except Exception:  # noqa: BLE001
        return None


def _independent_value(integrand, lower, upper, x):
    """Numeric quadrature value of a definite integral, or None if it doesn't converge."""
    import sympy as sp

    try:
        v = sp.Integral(integrand, (x, lower, upper)).evalf()
    except Exception:  # noqa: BLE001
        return None
    if not getattr(v, "is_number", False) or v.has(sp.Integral, sp.nan, sp.zoo):
        return None
    return v


def grade_all() -> bool:
    """Second gate: confirm the app's answer-checker (is_equivalent_up_to_constant)
    accepts each stored solution — opportunistically against an independently
    derived form so the check isn't tautological. Catches any divergence between
    verify() (d/dx vs integrand) and the production grader."""
    import sympy as sp

    from app.utils import is_equivalent_up_to_constant, parse_latex_safely
    from migrations.problems_registry import PROBLEMS

    x = sp.Symbol("x")
    norm = {sp.Symbol("e"): sp.E, sp.Symbol("pi"): sp.pi}
    failures = []

    for p in PROBLEMS:
        is_indef = p.integral_type == "indefinite"
        parsed = parse_latex_safely(p.solution, is_indefinite=is_indef)
        if parsed is None:
            ok, msg = False, "solution did not parse"
        elif is_indef:
            ref = _independent_antiderivative(p.integrand, x)
            form = ref if ref is not None else parsed.subs(norm)
            ok = is_equivalent_up_to_constant(form, parsed.subs(norm), is_indefinite=True)
            msg = ("OK (independent form)" if ref is not None else "OK (smoke)") if ok \
                else "grader rejected a correct form"
        else:
            # `trusted` marks definites whose numeric quadrature is unreliable
            # (Dirichlet etc. — mpmath can even return a bogus finite value), so
            # don't use a numeric reference for them; fall back to a smoke test.
            ref = None if p.trusted else _independent_value(p.integrand, p.lower, p.upper, x)
            target = parsed.subs(norm)
            if ref is not None:
                ok = is_equivalent_up_to_constant(ref, target, is_indefinite=False)
                msg = "OK (numeric ref)" if ok else "grader rejected numeric value"
            else:
                ok = is_equivalent_up_to_constant(target, target, is_indefinite=False)
                msg = "OK (smoke/trusted)" if ok else "grader rejected own value"

        print(f"[{'PASS' if ok else 'FAIL'}] {p.integral_type:10s} {p.problem[:45]:45s} {msg}")
        if not ok:
            failures.append(p.problem)

    print(f"\n{len(PROBLEMS) - len(failures)}/{len(PROBLEMS)} accepted by the app grader")
    if failures:
        print("FAILED:", failures)
    return not failures


def _next_date(taken: set[str], after: str) -> str:
    """First calendar date strictly after `after` not already in `taken`."""
    cur = date.fromisoformat(after)
    while True:
        cur += timedelta(days=1)
        key = cur.isoformat()
        if key not in taken:
            return key


def main() -> None:
    check_only = "--check" in sys.argv

    if not verify_all():
        sys.exit("\nVerification failed — nothing uploaded. Fix the registry first.")

    print("\n── App-grader gate (is_equivalent_up_to_constant) ──")
    if not grade_all():
        sys.exit("\nApp-grader gate failed — nothing uploaded. The production grader "
                 "rejects a correct solution; harden is_equivalent_up_to_constant.")

    if check_only:
        print("\n--check mode: verification + grader gate passed, nothing uploaded.")
        return

    load_dotenv(os.path.join(BASE_DIR, ".env.local"))
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not service_key:
        sys.exit("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env.local")

    from supabase import create_client

    from app.models import ProblemModel
    from migrations.problems_registry import PROBLEMS

    client = create_client(url, service_key)

    existing = client.table("integrals").select("id,date,problem").execute().data
    by_problem: dict[str, dict] = {row["problem"]: row for row in existing}
    taken_dates: set[str] = {row["date"] for row in existing}
    next_id = max((row["id"] for row in existing), default=0) + 1
    last_date = max((row["date"] for row in existing), default="1970-01-01")

    rows = []
    added = updated = 0

    for p in PROBLEMS:
        match = by_problem.get(p.problem)
        if match:
            row_id, row_date = match["id"], match["date"]
            updated += 1
        else:
            row_date = _next_date(taken_dates, last_date)
            taken_dates.add(row_date)
            last_date = row_date
            row_id = next_id
            next_id += 1
            added += 1

        raw = p.to_row(id=row_id, date=row_date)

        # Validate the row shape against ProblemModel — guarantees the API can
        # serve it without a 500. Catches missing required fields, bad difficulty
        # values, etc. before anything touches Supabase.
        try:
            ProblemModel(**raw)
        except ValidationError as e:
            sys.exit(f"\nProblemModel validation failed for '{p.problem}':\n{e}")

        rows.append(raw)

    client.table("integrals").upsert(rows, on_conflict="id").execute()

    total = client.table("integrals").select("id", count="exact").execute()
    print(f"\nUpserted {len(rows)} rows ({added} new, {updated} updated). "
          f"Supabase now has {total.count} integrals.")


if __name__ == "__main__":
    main()
