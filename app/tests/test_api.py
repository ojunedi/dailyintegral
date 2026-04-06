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
