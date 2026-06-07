"""
End-to-end guarantee: for EVERY integral in the problems registry (every one
added to the DB), the live POST /api/submit endpoint accepts the stored solution
as correct.

This is stronger than the migration gate (NewProblem.verify(), which uses a
d/dx-vs-integrand check). Here we drive the *actual* submission path a user hits:
the +C policy, parse_latex_safely on both sides, then is_equivalent_up_to_constant.
If the listed answer ever fails to grade as correct through that path, this test
names the exact integral.

One faithful adjustment: a real correct submission for an indefinite integral
must include the constant of integration, so we append "+ C" when the stored
solution doesn't already carry one (the endpoint rejects indefinite answers
without it before any math happens).
"""
import os

import pytest

from app import create_app
from app.utils import has_constant_of_integration
from migrations.problems_registry import PROBLEMS

TEST_DB = os.path.join(os.path.dirname(__file__), "_submit_registry_test.db")


@pytest.fixture()
def client():
    os.environ["TEST_DATABASE_PATH"] = TEST_DB
    os.environ["DATABASE_PATH"] = TEST_DB
    app = create_app("testing")
    app.config["DATABASE_PATH"] = TEST_DB
    with app.test_client() as c:
        yield c


def _submittable_answer(problem) -> str:
    """The listed solution as a user would submit it (with +C for indefinite)."""
    answer = problem.solution
    if problem.integral_type != "definite" and not has_constant_of_integration(answer):
        answer = answer + " + C"
    return answer


@pytest.mark.parametrize(
    "problem", PROBLEMS, ids=[f"{p.integral_type[:3]}|{p.problem}" for p in PROBLEMS]
)
def test_submit_accepts_listed_answer(client, problem):
    row = problem.to_row(id=1, date="2025-01-01")
    answer = _submittable_answer(problem)

    resp = client.post("/api/submit", json={"answer": answer, "problem": row})
    assert resp.status_code == 200, resp.get_json()
    data = resp.get_json()
    assert data["success"] is True, data
    assert data["is_correct"] is True, (
        f"/api/submit rejected the listed answer for {problem.problem!r} "
        f"(submitted {answer!r}): {data}"
    )
