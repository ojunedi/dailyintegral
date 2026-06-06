"""Tests for migrations/problem_models.py (NewProblem authoring model)."""
import pytest
import sympy as sp
from pydantic import ValidationError

from migrations.problem_models import NewProblem

x = sp.Symbol("x")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _indefinite(**kw):
    return NewProblem(**{
        "problem": r"\int x^2 dx",
        "solution": r"\frac{x^3}{3} + C",
        "integrand": x**2,
        "topic": "Power Rule",
        "difficulty": "easy",
        "progressive_hints": ["Use the power rule"],
        **kw,
    })


def _definite(**kw):
    return NewProblem(**{
        "problem": r"\int_0^1 x dx",
        "solution": r"\frac{1}{2}",
        "integrand": x,
        "integral_type": "definite",
        "lower": sp.Integer(0),
        "upper": sp.Integer(1),
        "topic": "Basic",
        "difficulty": "easy",
        "progressive_hints": ["Antiderivative of x is x^2/2"],
        **kw,
    })


# ── Validation ────────────────────────────────────────────────────────────────

class TestValidation:
    def test_valid_indefinite(self):
        p = _indefinite()
        assert p.integral_type == "indefinite"
        assert p.lower is None
        assert p.upper is None

    def test_valid_definite(self):
        p = _definite()
        assert p.integral_type == "definite"
        assert p.lower == sp.Integer(0)
        assert p.upper == sp.Integer(1)

    def test_difficulty_normalized_to_lowercase(self):
        assert _indefinite(difficulty="MEDIUM").difficulty == "medium"
        assert _indefinite(difficulty="Hard").difficulty == "hard"

    def test_integral_type_normalized_to_lowercase(self):
        assert _indefinite(integral_type="INDEFINITE").integral_type == "indefinite"

    def test_invalid_difficulty(self):
        with pytest.raises(ValidationError, match="difficulty"):
            _indefinite(difficulty="extreme")

    def test_invalid_integral_type(self):
        with pytest.raises(ValidationError, match="integral_type"):
            _indefinite(integral_type="semi")

    def test_definite_without_lower_raises(self):
        with pytest.raises(ValidationError, match="bounds"):
            NewProblem(
                problem=r"\int_0^1 x dx",
                solution=r"\frac{1}{2}",
                integrand=x,
                integral_type="definite",
                upper=sp.Integer(1),
                topic="Basic",
                difficulty="easy",
                progressive_hints=["hint"],
            )

    def test_definite_without_upper_raises(self):
        with pytest.raises(ValidationError, match="bounds"):
            NewProblem(
                problem=r"\int_0^1 x dx",
                solution=r"\frac{1}{2}",
                integrand=x,
                integral_type="definite",
                lower=sp.Integer(0),
                topic="Basic",
                difficulty="easy",
                progressive_hints=["hint"],
            )

    def test_definite_without_any_bounds_raises(self):
        with pytest.raises(ValidationError, match="bounds"):
            NewProblem(
                problem=r"\int_0^1 x dx",
                solution=r"\frac{1}{2}",
                integrand=x,
                integral_type="definite",
                topic="Basic",
                difficulty="easy",
                progressive_hints=["hint"],
            )

    def test_empty_problem_text_raises(self):
        with pytest.raises(ValidationError):
            _indefinite(problem="")

    def test_empty_hints_list_raises(self):
        with pytest.raises(ValidationError):
            _indefinite(progressive_hints=[])

    def test_whitespace_only_topic_stripped_and_fails(self):
        # str_strip_whitespace=True means "  " becomes "" which fails min_length
        with pytest.raises(ValidationError):
            _indefinite(topic="   ")


# ── to_row ────────────────────────────────────────────────────────────────────

class TestToRow:
    EXPECTED_KEYS = {
        "id", "date", "problem", "solution", "hint", "topic", "difficulty",
        "integral_type", "progressive_hints", "latex_problem", "latex_solution",
    }

    def test_has_all_required_keys(self):
        row = _indefinite().to_row(id=1, date="2025-01-01")
        assert set(row.keys()) == self.EXPECTED_KEYS

    def test_id_and_date_come_from_args(self):
        row = _indefinite().to_row(id=42, date="2025-12-31")
        assert row["id"] == 42
        assert row["date"] == "2025-12-31"

    def test_hint_is_none(self):
        assert _indefinite().to_row(id=1, date="2025-01-01")["hint"] is None

    def test_latex_fields_mirror_problem_and_solution(self):
        row = _indefinite().to_row(id=1, date="2025-01-01")
        assert row["latex_problem"] == row["problem"]
        assert row["latex_solution"] == row["solution"]

    def test_core_fields_preserved(self):
        p = _indefinite(topic="Calculus", difficulty="hard")
        row = p.to_row(id=5, date="2025-06-01")
        assert row["topic"] == "Calculus"
        assert row["difficulty"] == "hard"
        assert row["integral_type"] == "indefinite"
        assert row["progressive_hints"] == ["Use the power rule"]

    def test_definite_integral_type_preserved(self):
        row = _definite().to_row(id=3, date="2025-03-01")
        assert row["integral_type"] == "definite"

    def test_different_ids_produce_different_rows(self):
        p = _indefinite()
        row_a = p.to_row(id=1, date="2025-01-01")
        row_b = p.to_row(id=2, date="2025-01-02")
        assert row_a["id"] != row_b["id"]
        assert row_a["date"] != row_b["date"]


# ── verify ────────────────────────────────────────────────────────────────────

class TestVerify:
    def test_correct_indefinite_passes(self):
        ok, msg = _indefinite().verify()
        assert ok, msg

    def test_equivalent_form_accepted(self):
        # (1/3)x^3 is algebraically equivalent to x^3/3
        p = _indefinite(solution=r"\frac{1}{3}x^3 + C")
        ok, msg = p.verify()
        assert ok, msg

    def test_wrong_solution_fails(self):
        # x^2 is the derivative of x^3/3, not the integral
        p = _indefinite(solution=r"x^2 + C")
        ok, _ = p.verify()
        assert not ok

    def test_correct_definite_passes(self):
        ok, msg = _definite().verify()
        assert ok, msg

    def test_wrong_definite_fails(self):
        # ∫₀¹ x dx = 1/2, not 1
        p = _definite(solution=r"1")
        ok, _ = p.verify()
        assert not ok

    def test_unparseable_solution_fails(self):
        # \input triggers the dangerous-pattern guard in parse_latex_safely
        p = _indefinite(solution=r"\input{secret}")
        ok, msg = p.verify()
        assert not ok
        assert "parse" in msg

    def test_verify_returns_ok_string_on_pass(self):
        ok, msg = _indefinite().verify()
        assert ok
        assert msg == "OK"

    def test_verify_returns_message_on_fail(self):
        ok, msg = _indefinite(solution=r"x^2 + C").verify()
        assert not ok
        assert msg  # non-empty message
