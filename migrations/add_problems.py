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
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {p.integral_type:10s} {p.problem[:45]:45s} {msg}")
        if not ok:
            failures.append(p.problem)

    print(f"\n{len(PROBLEMS) - len(failures)}/{len(PROBLEMS)} passed")
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

    if check_only:
        print("\n--check mode: verification passed, nothing uploaded.")
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
