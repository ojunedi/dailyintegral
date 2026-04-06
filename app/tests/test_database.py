"""
Tests for DatabaseProblemSource.

Tests the database layer directly without going through Flask routes.
"""
import json
import os
import sqlite3
from datetime import date

import pytest

from app.problem_source import DatabaseProblemSource

TEST_DB = os.path.join(os.path.dirname(__file__), 'test_problem_source.db')


def _create_db(problems=None):
    """Create a test database with optional problem rows."""
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
    if problems:
        for p in problems:
            conn.execute(
                "INSERT INTO integrals (date, problem, solution, hint, difficulty, topic, "
                "progressive_hints, integral_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (p['date'], p['problem'], p['solution'], p.get('hint'),
                 p['difficulty'], p.get('topic'), p.get('progressive_hints', '[]'),
                 p.get('integral_type', 'indefinite')),
            )
    conn.commit()
    conn.close()


TODAY = date.today().strftime('%Y-%m-%d')

SAMPLE = {
    'date': TODAY,
    'problem': r'\int x^2 dx',
    'solution': r'\frac{x^3}{3}',
    'hint': 'Power rule',
    'difficulty': 'easy',
    'topic': 'polynomials',
    'progressive_hints': json.dumps(['Hint 1', 'Hint 2']),
    'integral_type': 'indefinite',
}
MALFORMED_SAMPLE = {**SAMPLE, 'progressive_hints': 'not valid json {{'}


@pytest.fixture(autouse=True)
def cleanup():
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestGetTodayProblem:

    def test_returns_problem_for_today(self):
        _create_db([SAMPLE])
        source = DatabaseProblemSource(TEST_DB)
        problem = source.get_today_problem()
        assert problem is not None
        assert problem['date'] == TODAY

    def test_returns_none_when_no_match(self):
        _create_db([{**SAMPLE, 'date': '2000-01-01'}])
        source = DatabaseProblemSource(TEST_DB)
        assert source.get_today_problem() is None

    def test_returns_none_on_empty_db(self):
        _create_db()
        source = DatabaseProblemSource(TEST_DB)
        assert source.get_today_problem() is None


class TestGetDailyProblem:

    def test_returns_a_problem(self):
        _create_db([SAMPLE])
        source = DatabaseProblemSource(TEST_DB)
        problem = source.get_daily_problem()
        assert problem is not None

    def test_deterministic_same_day(self):
        """Same day should always return the same problem."""
        _create_db([
            {**SAMPLE, 'date': '2025-01-01'},
            {**SAMPLE, 'date': '2025-01-02'},
            {**SAMPLE, 'date': '2025-01-03'},
        ])
        source = DatabaseProblemSource(TEST_DB)
        results = [source.get_daily_problem()['id'] for _ in range(5)]
        assert len(set(results)) == 1

    def test_returns_none_on_empty_db(self):
        _create_db()
        source = DatabaseProblemSource(TEST_DB)
        assert source.get_daily_problem() is None


class TestGetRandomProblem:

    def test_returns_a_problem(self):
        _create_db([SAMPLE])
        source = DatabaseProblemSource(TEST_DB)
        problem = source.get_random_problem()
        assert problem is not None
        assert 'solution' in problem

    def test_returns_none_on_empty_db(self):
        _create_db()
        source = DatabaseProblemSource(TEST_DB)
        assert source.get_random_problem() is None


class TestFormatProblem:

    def test_parses_progressive_hints_json(self):
        _create_db([SAMPLE])
        source = DatabaseProblemSource(TEST_DB)
        problem = source.get_today_problem()
        assert isinstance(problem['progressive_hints'], list)
        assert problem['progressive_hints'] == ['Hint 1', 'Hint 2']

    def test_handles_invalid_progressive_hints(self):
        _create_db([MALFORMED_SAMPLE])
        source = DatabaseProblemSource(TEST_DB)
        problem = source.get_today_problem()
        assert problem['progressive_hints'] == []


class TestErrorHandling:

    def test_missing_db_returns_none(self):
        source = DatabaseProblemSource('/nonexistent/path/db.sqlite')
        assert source.get_today_problem() is None
        assert source.get_daily_problem() is None
        assert source.get_random_problem() is None
