"""Tests for migrations/add_problems.py helpers and the problems registry."""
from migrations.add_problems import _next_date, verify_all
from migrations.problems_registry import PROBLEMS

# ── _next_date ────────────────────────────────────────────────────────────────

class TestNextDate:
    def test_simple_next_day(self):
        assert _next_date(set(), "2025-01-01") == "2025-01-02"

    def test_skips_single_taken_date(self):
        assert _next_date({"2025-01-02"}, "2025-01-01") == "2025-01-03"

    def test_skips_multiple_consecutive_taken(self):
        taken = {"2025-01-02", "2025-01-03", "2025-01-04"}
        assert _next_date(taken, "2025-01-01") == "2025-01-05"

    def test_skips_non_consecutive_taken(self):
        # Only 02 is taken; 03 is free
        assert _next_date({"2025-01-02"}, "2025-01-01") == "2025-01-03"

    def test_month_boundary(self):
        assert _next_date(set(), "2025-01-31") == "2025-02-01"

    def test_year_boundary(self):
        assert _next_date(set(), "2024-12-31") == "2025-01-01"

    def test_leap_year_february(self):
        assert _next_date(set(), "2024-02-28") == "2024-02-29"

    def test_non_leap_year_february(self):
        assert _next_date(set(), "2025-02-28") == "2025-03-01"

    def test_does_not_mutate_taken_set(self):
        taken = {"2025-01-02"}
        snapshot = set(taken)
        _next_date(taken, "2025-01-01")
        assert taken == snapshot

    def test_returns_iso_formatted_string(self):
        result = _next_date(set(), "2025-06-01")
        parts = result.split("-")
        assert len(parts) == 3 and all(p.isdigit() for p in parts)


# ── Registry smoke tests ──────────────────────────────────────────────────────

class TestRegistry:
    def test_registry_is_nonempty(self):
        assert len(PROBLEMS) > 0

    def test_problem_texts_are_unique(self):
        texts = [p.problem for p in PROBLEMS]
        assert len(texts) == len(set(texts)), "Duplicate problem text in registry"

    def test_all_difficulties_are_valid(self):
        allowed = {"easy", "medium", "hard"}
        bad = [p.problem for p in PROBLEMS if p.difficulty not in allowed]
        assert not bad, f"Invalid difficulties: {bad}"

    def test_definite_problems_have_bounds(self):
        bad = [
            p.problem for p in PROBLEMS
            if p.integral_type == "definite" and (p.lower is None or p.upper is None)
        ]
        assert not bad, f"Definite problems missing bounds: {bad}"

    def test_indefinite_problems_have_no_bounds(self):
        bad = [
            p.problem for p in PROBLEMS
            if p.integral_type == "indefinite" and (p.lower is not None or p.upper is not None)
        ]
        assert not bad, f"Indefinite problems have unexpected bounds: {bad}"

    def test_all_problems_have_at_least_one_hint(self):
        bad = [p.problem for p in PROBLEMS if not p.progressive_hints]
        assert not bad, f"Problems missing hints: {bad}"

    def test_all_problems_have_nonempty_topic(self):
        bad = [p.problem for p in PROBLEMS if not p.topic.strip()]
        assert not bad, f"Problems missing topic: {bad}"

    def test_all_problems_have_nonempty_solution(self):
        bad = [p.problem for p in PROBLEMS if not p.solution.strip()]
        assert not bad, f"Problems missing solution: {bad}"


# ── verify_all ────────────────────────────────────────────────────────────────

class TestVerifyAll:
    def test_verify_all_returns_true_for_current_registry(self):
        """Every problem in the registry must pass SymPy verification."""
        result = verify_all()
        assert result, "verify_all() failed — check captured output for details"
