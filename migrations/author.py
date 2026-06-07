"""
Append verified problems to the registry from a JSON file.

The JSON holds a list (or a single object) whose keys are the same fields as
NewProblem. The SymPy-valued fields — integrand, lower, upper — are written as
Python source strings in `x` and `sp` (SymPy), since JSON can't carry
expressions:

    [
      {
        "integrand": "sp.sec(x)**5",
        "topic": "Trigonometric Powers",
        "difficulty": "hard",
        "progressive_hints": ["reduction formula for sec^n", "sec^5 -> sec^3 -> sec"],
        "solution": "optional LaTeX; auto-computed from the integrand if omitted",
        "problem": "optional LaTeX; auto-generated from the integrand if omitted",
        "integral_type": "indefinite",
        "lower": "sp.Integer(0)",
        "upper": "sp.oo",
        "trusted": false
      }
    ]

Every entry is checked with the same gate the runner uses (d/dx == integrand for
indefinite, numeric quadrature for definite). If any entry fails verification,
nothing is written. Entries already present in the registry are skipped.

Usage:
    uv run python -m migrations.author new_problems.json
    uv run python -m migrations.author new_problems.json --check   # verify only

After a successful append, upload with:
    uv run python -m migrations.add_problems
"""
import json
import os
import sys

from pydantic import ValidationError

from migrations._generate_candidates import _emit, _eval, build
from migrations.problem_models import NewProblem

REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "problems_registry.py")

# NewProblem field name -> the internal key build() expects.
_FIELD_MAP = {
    "integrand": "isrc",
    "lower": "lsrc",
    "upper": "usrc",
    "progressive_hints": "hints",
}
_KNOWN_FIELDS = set(_FIELD_MAP) | {
    "problem", "solution", "integral_type", "topic", "difficulty", "trusted",
}


def _to_candidate(entry: dict) -> dict:
    """Translate a NewProblem-shaped JSON object into a build() candidate."""
    if not isinstance(entry, dict):
        raise ValueError(f"each entry must be a JSON object, got {type(entry).__name__}: {entry}")
    if "integrand" not in entry:
        raise ValueError(f"entry is missing required field 'integrand': {entry}")
    unknown = set(entry) - _KNOWN_FIELDS
    if unknown:
        raise ValueError(f"unknown field(s) {sorted(unknown)} in entry: {entry}")
    return {_FIELD_MAP.get(k, k): v for k, v in entry.items()}


def load_candidates(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("top-level JSON must be an object or a list of objects")
    return [_to_candidate(e) for e in data]


def validate_metadata(v: dict) -> str | None:
    """Build the real NewProblem to validate metadata (topic/difficulty/hints/
    bounds). Returns an error message, or None if valid."""
    try:
        NewProblem(
            problem=v["problem"],
            solution=v["solution"],
            integrand=_eval(v["isrc"]),
            integral_type=v.get("integral_type", "indefinite"),
            lower=_eval(v["lsrc"]) if v.get("lsrc") else None,
            upper=_eval(v["usrc"]) if v.get("usrc") else None,
            topic=v["topic"],
            difficulty=v["difficulty"],
            progressive_hints=v["hints"],
            trusted=v.get("trusted", False),
        )
    except (ValidationError, KeyError) as e:
        return str(e)
    return None


def append_to_registry(blocks: list[str], path: str = REGISTRY) -> None:
    with open(path) as f:
        src = f.read()
    idx = src.rstrip().rfind("\n]")
    if idx == -1:
        raise RuntimeError("could not find the end of the PROBLEMS list in the registry")
    new = src[:idx] + "\n" + "\n".join(blocks) + "\n]\n"
    with open(path, "w") as f:
        f.write(new)


def main() -> None:
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv
    if not positional:
        sys.exit("usage: python -m migrations.author <file.json> [--check]")

    candidates = load_candidates(positional[0])
    verified, failed = build(candidates)

    dups = [f for f in failed if f.get("reason") == "duplicate problem text"]
    errors = [f for f in failed if f.get("reason") != "duplicate problem text"]

    # Math passed; now confirm metadata (difficulty/hints/topic/bounds) is valid.
    for v in verified:
        msg = validate_metadata(v)
        if msg:
            errors.append({"isrc": v["isrc"], "reason": f"invalid metadata: {msg}"})
    if errors:
        verified = []  # all-or-nothing: a real error blocks the whole batch

    for v in verified:
        print(f"[OK]   {v['problem']}")
    for d in dups:
        print(f"[SKIP] already in registry: {d.get('isrc')}")
    for e in errors:
        print(f"[FAIL] {e.get('isrc')}: {e.get('reason')}")

    if errors:
        sys.exit(f"\n{len(errors)} entr(y/ies) failed — nothing written. Fix and retry.")

    if not verified:
        print("\nNothing new to add (all entries were already in the registry).")
        return

    if check_only:
        print(f"\n--check: {len(verified)} entr(y/ies) verified, nothing written.")
        return

    append_to_registry([_emit(v) for v in verified])
    print(f"\nAppended {len(verified)} problem(s) to {os.path.relpath(REGISTRY)}.")
    print("Upload with: uv run python -m migrations.add_problems")


if __name__ == "__main__":
    main()
