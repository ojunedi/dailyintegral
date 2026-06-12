"""
Tests for AI hint generation: SymPy diagnostics and the /api/hint endpoint.

The Claude call is always mocked — no test hits the network.
"""
from datetime import date

import pytest

from app import create_app
from app.ai_hint import diagnose_attempt
from app.models import ProblemModel


def make_problem(**overrides):
    data = {
        'id': 1,
        'date': date.today().strftime('%Y-%m-%d'),
        'problem': r'\int 2x \, dx',
        'solution': r'x^2 + C',
        'difficulty': 'easy',
        'topic': 'polynomials',
        'integral_type': 'indefinite',
        'progressive_hints': ['Use the power rule'],
    }
    data.update(overrides)
    return ProblemModel(**data)


# ── Diagnostics (pure SymPy, no network) ─────────────────────────────

class TestDiagnoseAttempt:

    def test_unparseable_attempt(self):
        facts = diagnose_attempt(r'\frac{x^2', make_problem())
        assert any('could not be parsed' in f for f in facts)

    def test_missing_constant_of_integration(self):
        facts = diagnose_attempt(r'x^2', make_problem())
        assert any('constant of integration' in f for f in facts)

    def test_correct_attempt_reported_equivalent(self):
        facts = diagnose_attempt(r'x^2 + C', make_problem())
        assert any('EQUIVALENT' in f for f in facts)

    def test_coefficient_error_detected(self):
        # d/dx(x^2/2) = x = (1/2) * integrand(2x) → off by a factor of 1/2
        facts = diagnose_attempt(r'\frac{x^2}{2} + C', make_problem())
        assert any('factor' in f for f in facts)

    def test_sign_error_detected_indefinite(self):
        facts = diagnose_attempt(r'-x^2 + C', make_problem())
        assert any('sign' in f for f in facts)

    def test_definite_sign_error_detected(self):
        problem = make_problem(
            problem=r'\int_0^1 2x \, dx',
            solution='1',
            integral_type='definite',
        )
        facts = diagnose_attempt('-1', problem)
        assert any('sign error' in f for f in facts)

    def test_definite_correct_value(self):
        problem = make_problem(
            problem=r'\int_0^1 2x \, dx',
            solution='1',
            integral_type='definite',
        )
        facts = diagnose_attempt('1', problem)
        assert any('EQUIVALENT' in f for f in facts)

    def test_diagnostics_never_raise_on_weird_input(self):
        # Best-effort: any input should produce a list, not an exception.
        facts = diagnose_attempt(r'\ln|x| + \frac{1}{0} + C', make_problem())
        assert isinstance(facts, list)


# ── /api/hint endpoint (Claude mocked) ───────────────────────────────

@pytest.fixture()
def client():
    app = create_app('testing')
    with app.test_client() as c:
        yield c


@pytest.fixture()
def seeded_db(client):
    """Seed the test SQLite DB with one problem for today (for /api/problem)."""
    import json
    import os
    import sqlite3

    db_path = client.application.config['DATABASE_PATH']
    conn = sqlite3.connect(db_path)
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
        "progressive_hints, integral_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            date.today().strftime('%Y-%m-%d'), r'\int 2x \, dx', r'x^2 + C',
            'Power rule', 'easy', 'polynomials',
            json.dumps(['Use the power rule']), 'indefinite',
        )
    )
    conn.commit()
    conn.close()
    yield
    if os.path.exists(db_path):
        os.remove(db_path)


def hint_payload(attempt=r'x^2'):
    return {
        'attempt': attempt,
        'problem': make_problem().model_dump(),
    }


class TestAiHintsEnabledFlag:
    """The /api/problem response advertises whether AI hints are configured,
    so the frontend only renders the button when the feature can work."""

    def test_flag_false_without_api_key(self, client, seeded_db):
        client.application.config['ANTHROPIC_API_KEY'] = ''
        resp = client.get('/api/problem')
        assert resp.status_code == 200
        assert resp.get_json()['ai_hints_enabled'] is False

    def test_flag_true_with_api_key(self, client, seeded_db):
        client.application.config['ANTHROPIC_API_KEY'] = 'test-key'
        resp = client.get('/api/problem')
        assert resp.status_code == 200
        assert resp.get_json()['ai_hints_enabled'] is True


class TestHintEndpoint:

    def test_returns_503_without_api_key(self, client):
        client.application.config['ANTHROPIC_API_KEY'] = ''
        resp = client.post('/api/hint', json=hint_payload())
        assert resp.status_code == 503
        assert resp.get_json()['success'] is False

    def test_returns_400_without_body(self, client):
        client.application.config['ANTHROPIC_API_KEY'] = 'test-key'
        resp = client.post('/api/hint', json={})
        assert resp.status_code == 400

    def test_returns_400_on_invalid_problem(self, client):
        client.application.config['ANTHROPIC_API_KEY'] = 'test-key'
        resp = client.post('/api/hint', json={'attempt': 'x', 'problem': {'id': 1}})
        assert resp.status_code == 400

    def test_success_with_mocked_model(self, client, monkeypatch):
        client.application.config['ANTHROPIC_API_KEY'] = 'test-key'
        monkeypatch.setattr(
            'app.api.generate_hint',
            lambda problem, attempt, api_key: 'Check your coefficient: what is $\\frac{d}{dx} x^2$?',
        )
        resp = client.post('/api/hint', json=hint_payload())
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert 'coefficient' in body['hint']

    def test_model_error_returns_502(self, client, monkeypatch):
        client.application.config['ANTHROPIC_API_KEY'] = 'test-key'

        def boom(problem, attempt, api_key):
            raise RuntimeError('api down')

        monkeypatch.setattr('app.api.generate_hint', boom)
        resp = client.post('/api/hint', json=hint_payload())
        assert resp.status_code == 502
        assert resp.get_json()['success'] is False

    def test_model_refusal_returns_502(self, client, monkeypatch):
        client.application.config['ANTHROPIC_API_KEY'] = 'test-key'
        monkeypatch.setattr('app.api.generate_hint', lambda problem, attempt, api_key: None)
        resp = client.post('/api/hint', json=hint_payload())
        assert resp.status_code == 502
