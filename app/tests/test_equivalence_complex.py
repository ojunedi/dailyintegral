"""
Equivalence tests for complicated integrals, driven through the REAL grading
path the app uses: POST /api/submit.

The endpoint receives the user's LaTeX answer plus the problem (whose stored
`solution` is one correct antiderivative), then runs exactly what production
runs: the +C check, parse_latex_safely on both sides, and
is_equivalent_up_to_constant. Each case submits a *different but equivalent*
form of a hard integral's answer and asserts the grader accepts it — and that
genuinely wrong answers are rejected.
"""
import os

import pytest

from app import create_app

TEST_DB = os.path.join(os.path.dirname(__file__), "_equiv_test.db")


@pytest.fixture()
def client():
    # submit_answer reads the problem from the request body, not the DB, but the
    # app still needs a configured DB path to start.
    os.environ["TEST_DATABASE_PATH"] = TEST_DB
    os.environ["DATABASE_PATH"] = TEST_DB
    app = create_app("testing")
    app.config["DATABASE_PATH"] = TEST_DB
    with app.test_client() as c:
        yield c


def _problem(solution: str, integral_type: str = "indefinite") -> dict:
    """A minimal valid problem payload carrying the stored solution to grade against."""
    return {
        "id": 1,
        "date": "2025-01-01",
        "problem": "placeholder",
        "solution": solution,
        "difficulty": "hard",
        "integral_type": integral_type,
    }


def _grade(client, answer: str, solution: str, integral_type: str = "indefinite") -> dict:
    resp = client.post(
        "/api/submit",
        json={"answer": answer, "problem": _problem(solution, integral_type)},
    )
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["success"] is True, data
    return data


# ── Equivalent forms of the same hard integral — grader must accept ─────────────
# (stored solution, user-submitted equivalent form). The two differ by a
# constant or are algebraically equal but written via a different method.
EQUIVALENT = [
    # ∫ sin(x)cos(x) dx
    (r"\frac{\sin^2(x)}{2}", r"-\frac{\cos^2(x)}{2} + C"),
    (r"\frac{\sin^2(x)}{2}", r"-\frac{\cos(2x)}{4} + C"),
    # ∫ tan^3(x) dx — u=tan vs u=sec form (off by 1/2)
    (r"\frac{1}{2}\tan^2(x)", r"\frac{1}{2}\sec^2(x) + C"),
    # ∫ sec^2(x) dx
    (r"\tan(x)", r"\frac{\sin(x)}{\cos(x)} + C"),
    # ∫ 1/(1+x^2) dx — arctan vs -arccot (off by pi/2)
    (r"\arctan(x)", r"-\cot^{-1}(x) + C"),
    # ∫ 1/(x^2-1) dx — combined vs split logarithm (partial fractions)
    (r"\frac{1}{2}\ln\frac{x-1}{x+1}", r"\frac{1}{2}\ln(x-1) - \frac{1}{2}\ln(x+1) + C"),
    # ∫ x e^x dx — factored vs expanded
    (r"(x-1)e^x", r"x e^x - e^x + C"),
    # ∫ sin^2(x) dx — power-reduction vs sin*cos form
    (r"\frac{x}{2} - \frac{\sin(2x)}{4}", r"\frac{x}{2} - \frac{\sin(x)\cos(x)}{2} + C"),
    # ∫ x/(1+x^4) dx — arctan(x^2)/2, accepted with any added constant
    (r"\frac{1}{2}\arctan(x^2)", r"\frac{1}{2}\arctan(x^2) + 7 + C"),
]


@pytest.mark.parametrize("solution, answer", EQUIVALENT)
def test_equivalent_answer_accepted(client, solution, answer):
    data = _grade(client, answer, solution)
    assert data["is_correct"] is True, f"{answer!r} should match {solution!r}"


# ── Genuinely wrong answers — grader must reject ────────────────────────────────
WRONG = [
    # right shape, wrong coefficient
    (r"\frac{\sin^2(x)}{2}", r"\sin^2(x) + C"),
    (r"\frac{1}{2}\tan^2(x)", r"\tan^2(x) + C"),
    (r"\frac{x^3}{3}", r"\frac{x^3}{2} + C"),
    # wrong argument
    (r"\arctan(x)", r"\arctan(2x) + C"),
    # derivative instead of antiderivative
    (r"\frac{x^3}{3}", r"x^2 + C"),
]


@pytest.mark.parametrize("solution, answer", WRONG)
def test_wrong_answer_rejected(client, solution, answer):
    data = _grade(client, answer, solution)
    assert data["is_correct"] is False, f"{answer!r} should NOT match {solution!r}"


# ── Missing +C on an indefinite integral is always incorrect ────────────────────
def test_missing_plus_c_is_incorrect(client):
    # Correct antiderivative, but no constant of integration → rejected.
    data = _grade(client, r"-\frac{\cos^2(x)}{2}", r"\frac{\sin^2(x)}{2}")
    assert data["is_correct"] is False


# ── Definite integrals — exact value, different forms, no +C ─────────────────────
EQUIVALENT_DEFINITE = [
    # ∫_0^inf 1/(1+x^4) dx = pi/(2 sqrt2) = sqrt2 pi/4
    (r"\frac{\sqrt{2}\pi}{4}", r"\frac{\pi}{2\sqrt{2}}"),
    # ∫_0^inf x^2 e^{-x} dx = 2
    (r"2", r"2"),
    # ∫_0^inf x^4 e^{-x^2} dx = 3 sqrt(pi)/8, written two ways
    (r"\frac{3\sqrt{\pi}}{8}", r"\frac{3}{8}\sqrt{\pi}"),
]

WRONG_DEFINITE = [
    (r"\frac{\pi}{2}", r"\frac{\pi}{3}"),
    (r"\frac{\sqrt{2}\pi}{4}", r"\frac{\pi}{4}"),
    (r"2", r"3"),
]


@pytest.mark.parametrize("solution, answer", EQUIVALENT_DEFINITE)
def test_definite_equal_value_accepted(client, solution, answer):
    data = _grade(client, answer, solution, integral_type="definite")
    assert data["is_correct"] is True, f"{answer!r} should equal {solution!r}"


@pytest.mark.parametrize("solution, answer", WRONG_DEFINITE)
def test_definite_wrong_value_rejected(client, solution, answer):
    data = _grade(client, answer, solution, integral_type="definite")
    assert data["is_correct"] is False, f"{answer!r} should NOT equal {solution!r}"
