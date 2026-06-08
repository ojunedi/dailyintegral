r"""
One-shot repair for problem display LaTeX that was corrupted by the old
generator (_prettify ate \frac denominator braces, e.g.
``\frac{x^{3}}(x^{2} + 1)^{2}}``). The integrand field is the source of truth and
was never affected, so the correct display string is regenerated from it.

Both the registry file AND the live Supabase rows are updated in the SAME run,
using one ``old -> new`` mapping, so the two stay byte-identical. (If they
diverged, the next normal ``add_problems`` upload — which matches rows by problem
text — would treat the fixed registry entries as new and create duplicates.)
The Supabase rows are matched by their current (still-broken) problem text, which
is exactly what the registry holds before this script edits it.

Usage:
    uv run python -m migrations.fix_problem_latex --check          # show fixes, write nothing
    uv run python -m migrations.fix_problem_latex                   # fix registry + Supabase
    uv run python -m migrations.fix_problem_latex --registry-only   # fix the file + save map
    uv run python -m migrations.fix_problem_latex --supabase-only   # apply saved map to Supabase

The old->new map is saved to _latex_fix_map.json so the Supabase update can run
(byte-identically) even after the registry has already been fixed.
"""
import json
import os
import sys

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "problems_registry.py")
MAP_PATH = os.path.join(HERE, "_latex_fix_map.json")


def _build_fixes() -> list[tuple[str, str]]:
    """Return (old_problem, new_problem) for every entry whose display LaTeX does
    not render its integrand. Regenerates each from the integrand and re-checks."""
    from migrations._generate_candidates import _problem_latex
    from migrations.problems_registry import PROBLEMS

    fixes: list[tuple[str, str]] = []
    for p in PROBLEMS:
        ok, _ = p.problem_matches_integrand()
        if ok:
            continue
        new_problem = _problem_latex(p.integrand, p.integral_type, p.lower, p.upper)
        # Re-verify the regenerated string against the same integrand.
        check = p.model_copy(update={"problem": new_problem})
        ok2, msg2 = check.problem_matches_integrand()
        if not ok2:
            sys.exit(f"ERROR: regenerated LaTeX still fails for {p.problem!r}: {msg2}")
        if new_problem != p.problem:
            fixes.append((p.problem, new_problem))
    return fixes


def _rewrite_registry(fixes: list[tuple[str, str]]) -> None:
    with open(REGISTRY) as f:
        src = f.read()
    for old, new in fixes:
        # Entries with no quotes are emitted as raw strings: problem=r"...".
        old_lit, new_lit = f'r"{old}"', f'r"{new}"'
        count = src.count(old_lit)
        if count != 1:
            sys.exit(f"ERROR: expected exactly one occurrence of {old_lit} in registry, found {count}")
        src = src.replace(old_lit, new_lit)
    with open(REGISTRY, "w") as f:
        f.write(src)


def _update_supabase(fixes: list[tuple[str, str]]) -> None:
    load_dotenv(os.path.join(BASE_DIR, ".env.local"))
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not service_key:
        sys.exit("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env.local")

    from supabase import create_client

    client = create_client(url, service_key)
    updated = 0
    for old, new in fixes:
        resp = (
            client.table("integrals")
            .update({"problem": new, "latex_problem": new})
            .eq("problem", old)
            .execute()
        )
        n = len(resp.data)
        updated += n
        print(f"  {'updated' if n else 'NO MATCH'} ({n}): {old[:50]}")
    print(f"\nUpdated {updated} Supabase row(s).")


def main() -> None:
    check_only = "--check" in sys.argv
    registry_only = "--registry-only" in sys.argv
    supabase_only = "--supabase-only" in sys.argv

    # Supabase-only re-runs from the saved map (registry is already fixed by then).
    if supabase_only:
        if not os.path.exists(MAP_PATH):
            sys.exit(f"ERROR: {os.path.relpath(MAP_PATH)} not found — run the registry fix first.")
        with open(MAP_PATH) as f:
            fixes = [tuple(pair) for pair in json.load(f)]
        print(f"Applying {len(fixes)} saved fix(es) to Supabase…")
        _update_supabase(fixes)
        return

    fixes = _build_fixes()
    if not fixes:
        print("Nothing to fix — every problem statement already renders its integrand.")
        return

    print(f"{len(fixes)} problem statement(s) to repair:\n")
    for old, new in fixes:
        print(f"  OLD: {old}")
        print(f"  NEW: {new}\n")

    if check_only:
        print("--check: nothing written.")
        return

    _rewrite_registry(fixes)
    with open(MAP_PATH, "w") as f:
        json.dump([list(pair) for pair in fixes], f, indent=2, ensure_ascii=False)
    print(f"Rewrote {len(fixes)} entries in {os.path.relpath(REGISTRY)}; "
          f"saved map to {os.path.relpath(MAP_PATH)}.")

    if registry_only:
        print("--registry-only: skipped Supabase (run --supabase-only to apply).")
        return

    print("\nUpdating Supabase rows in place…")
    _update_supabase(fixes)


if __name__ == "__main__":
    main()
