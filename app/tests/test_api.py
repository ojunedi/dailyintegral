"""
Integration tests for API endpoints.

Uses Flask's test client with a real SQLite test database.
"""
import json
import os
import sqlite3
from datetime import date

import pytest

from app import create_app

TEST_DB = os.path.join(os.path.dirname(__file__), 'test_integrals.db')

SAMPLE_PROBLEM = {
    'date': date.today().strftime('%Y-%m-%d'),
    'problem': r'\int x^2 dx',
    'solution': r'\frac{x^3}{3}',
    'hint': 'Use the power rule',
    'difficulty': 'easy',
    'topic': 'polynomials',
    'latex_problem': r'\int x^2 \, dx',
    'latex_solution': r'\frac{x^3}{3} + C',
    'progressive_hints': json.dumps([
        'Look at the form of the integrand',
        'Use the power rule',
    ]),
    'integral_type': 'indefinite',
}


def _seed_db():
    """Create a test database with one sample problem."""
    conn = sqlite3.connect(TEST_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS integrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE NOT NULL,
            problem TEXT NOT NULL,
            solution TEXT NOT NULL,
            hint TEXT,
            difficulty TEXT,
            topic TEXT,
            latex_problem TEXT,
            latex_solution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progressive_hints JSON,
            integral_type TEXT DEFAULT "indefinite"
        )
    """)
    conn.execute("DELETE FROM integrals")
    conn.execute(
        "INSERT INTO integrals (date, problem, solution, hint, difficulty, topic, "
        "latex_problem, latex_solution, progressive_hints, integral_type) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            SAMPLE_PROBLEM['date'], SAMPLE_PROBLEM['problem'],
            SAMPLE_PROBLEM['solution'], SAMPLE_PROBLEM['hint'],
            SAMPLE_PROBLEM['difficulty'], SAMPLE_PROBLEM['topic'],
            SAMPLE_PROBLEM['latex_problem'], SAMPLE_PROBLEM['latex_solution'],
            SAMPLE_PROBLEM['progressive_hints'], SAMPLE_PROBLEM['integral_type'],
        )
    )
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Create test DB before each test, remove after."""
    _seed_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture()
def client():
    os.environ['TEST_DATABASE_PATH'] = TEST_DB
    os.environ['DATABASE_PATH'] = TEST_DB
    app = create_app('testing')
    app.config['DATABASE_PATH'] = TEST_DB
    with app.test_client() as c:
        yield c


@pytest.fixture()
def rate_limited_client():
    """Client with rate limiting enabled (normally disabled in testing)."""
    os.environ['TEST_DATABASE_PATH'] = TEST_DB
    os.environ['DATABASE_PATH'] = TEST_DB
    app = create_app('testing')
    app.config['DATABASE_PATH'] = TEST_DB
    app.config['RATELIMIT_ENABLED'] = True
    with app.test_client() as c:
        yield c


# ── Health endpoint ──────────────────────────────────────────────────

class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200

    def test_health_body(self, client):
        data = client.get('/api/health').get_json()
        assert data['success'] is True
        assert 'healthy' in data['message'].lower()


# ── Problem endpoint ─────────────────────────────────────────────────

class TestProblemEndpoint:

    def test_get_problem_returns_200(self, client):
        resp = client.get('/api/problem')
        assert resp.status_code == 200

    def test_problem_has_required_fields(self, client):
        data = client.get('/api/problem').get_json()
        assert data['success'] is True
        problem = data['problem']
        assert 'id' in problem
        assert 'problem' in problem
        assert 'solution' in problem
        assert 'difficulty' in problem

    def test_problem_difficulty_is_valid(self, client):
        problem = client.get('/api/problem').get_json()['problem']
        assert problem['difficulty'] in ('easy', 'medium', 'hard')

    def test_empty_db_returns_404(self, client):
        # Wipe the test DB
        conn = sqlite3.connect(TEST_DB)
        conn.execute("DELETE FROM integrals")
        conn.commit()
        conn.close()

        resp = client.get('/api/problem')
        assert resp.status_code == 404
        assert resp.get_json()['success'] is False


# ── Practice problem endpoint ────────────────────────────────────────

# A handful of problems spanning difficulties/topics, with distinct dates
# (the `date` column is UNIQUE). Used to exercise the practice filters.
PRACTICE_PROBLEMS = [
    ('2001-01-01', r'\int x dx', r'\frac{x^2}{2}', 'easy', 'polynomials'),
    ('2001-01-02', r'\int x^2 dx', r'\frac{x^3}{3}', 'easy', 'polynomials'),
    ('2001-01-03', r'\int e^x dx', r'e^x', 'medium', 'exponentials'),
    ('2001-01-04', r'\int \sec^2 x dx', r'\tan x', 'hard', 'trigonometry'),
]


def _seed_practice_problems():
    """Add several problems with varied difficulty/topic for filter tests."""
    conn = sqlite3.connect(TEST_DB)
    for d, prob, sol, diff, topic in PRACTICE_PROBLEMS:
        conn.execute(
            "INSERT INTO integrals (date, problem, solution, difficulty, topic, "
            "progressive_hints, integral_type) VALUES (?, ?, ?, ?, ?, '[]', 'indefinite')",
            (d, prob, sol, diff, topic),
        )
    conn.commit()
    conn.close()


class TestPracticeProblemEndpoint:

    def test_practice_returns_200(self, client):
        resp = client.get('/api/practice/problem')
        assert resp.status_code == 200

    def test_practice_has_valid_problem(self, client):
        data = client.get('/api/practice/problem').get_json()
        assert data['success'] is True
        problem = data['problem']
        assert problem['id'] >= 1
        assert 'problem' in problem
        assert 'solution' in problem
        assert problem['difficulty'] in ('easy', 'medium', 'hard')

    def test_practice_respects_difficulty_filter(self, client):
        _seed_practice_problems()
        for _ in range(10):
            data = client.get('/api/practice/problem?difficulty=hard').get_json()
            assert data['success'] is True
            assert data['problem']['difficulty'] == 'hard'

    def test_practice_respects_topic_filter(self, client):
        _seed_practice_problems()
        for _ in range(10):
            data = client.get('/api/practice/problem?topic=exponentials').get_json()
            assert data['success'] is True
            assert data['problem']['topic'] == 'exponentials'

    def test_practice_invalid_difficulty_returns_400(self, client):
        resp = client.get('/api/practice/problem?difficulty=impossible')
        assert resp.status_code == 400
        assert resp.get_json()['success'] is False

    def test_practice_no_match_returns_404(self, client):
        # The base seed has only an 'easy' problem; nothing matches a bogus topic.
        resp = client.get('/api/practice/problem?topic=nonexistent_topic_xyz')
        assert resp.status_code == 404
        assert resp.get_json()['success'] is False

    def test_practice_empty_db_returns_404(self, client):
        conn = sqlite3.connect(TEST_DB)
        conn.execute("DELETE FROM integrals")
        conn.commit()
        conn.close()
        resp = client.get('/api/practice/problem')
        assert resp.status_code == 404
        assert resp.get_json()['success'] is False


# ── Submit endpoint ──────────────────────────────────────────────────

class TestSubmitEndpoint:

    def _get_problem(self, client):
        return client.get('/api/problem').get_json()['problem']

    def test_correct_answer(self, client):
        problem = self._get_problem(client)
        resp = client.post('/api/submit', json={
            'answer': r'\frac{x^3}{3} + C',
            'problem': problem,
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['is_correct'] is True

    def test_incorrect_answer(self, client):
        problem = self._get_problem(client)
        resp = client.post('/api/submit', json={
            'answer': r'x^2 + C',
            'problem': problem,
        })
        data = resp.get_json()
        assert data['success'] is True
        assert data['is_correct'] is False

    def test_missing_constant_of_integration(self, client):
        # missing is incorrect
        problem = self._get_problem(client)
        resp = client.post(
            '/api/submit',
            json = {
            'answer': r'\frac{x^3}{3}',
            'problem': problem
            }
        )
        data = resp.get_json()
        assert data['success'] is True
        assert data['is_correct'] is False

        # +C present is correct
        resp = client.post(
            '/api/submit',
            json = {
            'answer': r'\frac{x^3}{3} + C',
            'problem': problem
            }
        )
        data = resp.get_json()
        assert data['success'] is True
        assert data['is_correct'] is True

    def test_unparseable_answer_is_not_graded(self, client):
        # Malformed LaTeX (unbalanced brace) that still contains +C so it passes the
        # constant-of-integration check and reaches the parser. The parser fails, so the
        # response must be flagged success=False — NOT a graded incorrect answer.
        # The frontend relies on this distinction to allow a retry instead of locking
        # the daily attempt.
        problem = self._get_problem(client)
        resp = client.post('/api/submit', json={
            'answer': r'\frac{x}{ + C',
            'problem': problem,
        })
        data = resp.get_json()
        assert data['success'] is False
        assert data['is_correct'] is False
        assert 'parse' in data['error'].lower()

    def test_no_body_returns_error(self, client):
        resp = client.post('/api/submit', content_type='application/json')
        assert resp.status_code in (400, 500)
        assert resp.get_json()['success'] is False

    def test_empty_answer_returns_400(self, client):
        problem = self._get_problem(client)
        resp = client.post('/api/submit', json={
            'answer': '   ',
            'problem': problem,
        })
        assert resp.status_code == 400


# ── Rate limiting ────────────────────────────────────────────────────

class TestRateLimiting:

    def _get_problem(self, client):
        return client.get('/api/problem').get_json()['problem']

    def test_submit_rate_limit_triggers_at_21(self, rate_limited_client):
        """Submit endpoint should return 429 after 20 requests per minute."""
        client = rate_limited_client
        problem = self._get_problem(client)
        payload = {'answer': r'x + C', 'problem': problem}

        for i in range(20):
            resp = client.post('/api/submit', json=payload)
            assert resp.status_code != 429, f"Rate limited too early on request {i + 1}"

        # 21st request should be rate limited
        resp = client.post('/api/submit', json=payload)
        assert resp.status_code == 429

    def test_health_not_rate_limited_at_submit_limit(self, rate_limited_client):
        self.test_submit_rate_limit_triggers_at_21(rate_limited_client)
        resp = rate_limited_client.get('/api/health')
        assert resp.status_code == 200


# ── Definite integral submit ─────────────────────────────────────────

# A minimal problem object for a definite integral (no DB required; the submit
# endpoint takes the problem in the request body and validates with Pydantic).
DEFINITE_PROBLEM = {
    'id': 99,
    'date': '2000-01-01',
    'problem': r'\int_0^2 x\,dx',
    'solution': r'2',
    'difficulty': 'easy',
    'integral_type': 'definite',
}


class TestSubmitDefiniteIntegral:

    def test_correct_answer_without_c(self, client):
        resp = client.post('/api/submit', json={
            'answer': '2',
            'problem': DEFINITE_PROBLEM,
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['is_correct'] is True

    def test_wrong_answer(self, client):
        resp = client.post('/api/submit', json={
            'answer': '5',
            'problem': DEFINITE_PROBLEM,
        })
        data = resp.get_json()
        assert data['success'] is True
        assert data['is_correct'] is False

    def test_answer_with_c_still_accepted(self, client):
        # Definite integrals don't require +C, but having it shouldn't crash
        # (the +C gets parsed as part of the expression and compared)
        resp = client.post('/api/submit', json={
            'answer': '2 + C',
            'problem': DEFINITE_PROBLEM,
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True

    def test_numeric_expression_equivalent_form(self, client):
        resp = client.post('/api/submit', json={
            'answer': r'\frac{4}{2}',
            'problem': DEFINITE_PROBLEM,
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['is_correct'] is True


# ── Unparseable correct answer in DB ────────────────────────────────

class TestSubmitUnparseableSolution:

    def _make_problem(self, solution: str) -> dict:
        return {
            'id': 1,
            'date': date.today().strftime('%Y-%m-%d'),
            'problem': r'\int x^2 dx',
            'solution': solution,
            'difficulty': 'easy',
            'integral_type': 'indefinite',
        }

    def test_unparseable_solution_returns_500(self, client):
        """When the stored solution can't be parsed the endpoint returns 500, not a wrong verdict."""
        # r'\frac{x^3' is an incomplete fraction — confirmed to return None from parse_latex_safely.
        resp = client.post('/api/submit', json={
            'answer': r'\frac{x^3}{3} + C',
            'problem': self._make_problem(r'\frac{x^3'),
        })
        data = resp.get_json()
        assert resp.status_code == 500
        assert data['success'] is False


# ── Error handlers ───────────────────────────────────────────────────

class TestErrorHandlers:

    def test_404_returns_json(self, client):
        resp = client.get('/api/nonexistent_endpoint_xyz')
        assert resp.status_code == 404
        data = resp.get_json()
        assert data is not None
        assert data['success'] is False

    def test_method_not_allowed_on_post_only_endpoint(self, client):
        resp = client.get('/api/submit')
        assert resp.status_code in (405, 404)
