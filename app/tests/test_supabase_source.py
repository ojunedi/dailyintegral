"""
Tests for SupabaseProblemSource using a fake postgrest client.

No network: `supabase.create_client` is monkeypatched to return a FakeClient that
emulates the slice of the query builder the source uses (select/order/range/eq/limit
and count='exact').
"""
from datetime import date

import pytest

from app.problem_source import SupabaseProblemSource

# ── Fake postgrest client ────────────────────────────────────────────


class FakeResponse:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class FakeQuery:
    def __init__(self, rows):
        self._rows = rows
        self._count_mode = False
        self._range = None
        self._limit = None

    def select(self, *_args, count=None):
        self._count_mode = count == 'exact'
        return self

    def order(self, col):
        self._rows = sorted(self._rows, key=lambda r: r[col])
        return self

    def range(self, start, end):
        self._range = (start, end)
        return self

    def eq(self, col, val):
        self._rows = [r for r in self._rows if str(r[col]) == str(val)]
        return self

    def limit(self, n):
        self._limit = n
        return self

    def execute(self):
        if self._count_mode:
            return FakeResponse([], count=len(self._rows))
        rows = self._rows
        if self._range is not None:
            s, e = self._range
            rows = rows[s:e + 1]
        if self._limit is not None:
            rows = rows[:self._limit]
        return FakeResponse([dict(r) for r in rows])


class FakeClient:
    def __init__(self, rows):
        self._rows = rows

    def table(self, _name):
        # Fresh copy per call so filters/ordering don't mutate the source data.
        return FakeQuery([dict(r) for r in self._rows])


def _row(id, date_str, **overrides):
    base = {
        'id': id,
        'date': date_str,
        'problem': r'\int x^2 dx',
        'solution': r'\frac{x^3}{3}',
        'hint': 'Power rule',
        'difficulty': 'easy',
        'topic': 'polynomials',
        'latex_problem': None,
        'latex_solution': None,
        'progressive_hints': ['Hint 1', 'Hint 2'],
        'integral_type': 'indefinite',
    }
    base.update(overrides)
    return base


@pytest.fixture
def source():
    return SupabaseProblemSource('https://example.supabase.co', 'anon-key')


def _patch_client(monkeypatch, rows):
    """Make SupabaseProblemSource._client return a FakeClient over `rows`."""
    import supabase
    monkeypatch.setattr(supabase, 'create_client', lambda url, key: FakeClient(rows))


# ── get_daily_problem ────────────────────────────────────────────────


def test_daily_problem_is_deterministic_by_offset(source, monkeypatch):
    rows = [_row(i, f'2025-01-0{i}') for i in range(1, 6)]  # ids 1..5
    _patch_client(monkeypatch, rows)

    total = len(rows)
    expected_offset = (date.today() - date(1970, 1, 1)).days % total
    expected_id = sorted(rows, key=lambda r: r['id'])[expected_offset]['id']

    problem = source.get_daily_problem()
    assert problem is not None
    assert problem['id'] == expected_id


def test_daily_problem_empty_table_returns_none(source, monkeypatch):
    _patch_client(monkeypatch, [])
    assert source.get_daily_problem() is None


# ── get_random_problem ───────────────────────────────────────────────


def test_random_problem_uses_offset(source, monkeypatch):
    rows = [_row(i, f'2025-01-0{i}') for i in range(1, 6)]
    _patch_client(monkeypatch, rows)
    # Force the "random" offset to a known value.
    monkeypatch.setattr('app.problem_source.random.randint', lambda a, b: 2)

    problem = source.get_random_problem()
    assert problem is not None
    assert problem['id'] == sorted(rows, key=lambda r: r['id'])[2]['id']


def test_random_problem_empty_table_returns_none(source, monkeypatch):
    _patch_client(monkeypatch, [])
    assert source.get_random_problem() is None


# ── get_today_problem ────────────────────────────────────────────────


def test_today_problem_matches_date(source, monkeypatch):
    today = date.today().strftime('%Y-%m-%d')
    rows = [_row(1, '2025-01-01'), _row(2, today), _row(3, '2025-01-03')]
    _patch_client(monkeypatch, rows)

    problem = source.get_today_problem()
    assert problem is not None
    assert problem['id'] == 2


def test_today_problem_no_match_returns_none(source, monkeypatch):
    rows = [_row(1, '2025-01-01')]
    _patch_client(monkeypatch, rows)
    assert source.get_today_problem() is None


# ── format_problem ───────────────────────────────────────────────────


def test_format_applies_backslash_fix(source):
    problem = source.format_problem({
        'solution': r'\\frac{x^3}{3}',
        'latex_problem': r'\\int x^2 \\, dx',
        'progressive_hints': [],
    })
    assert problem['solution'] == r'\frac{x^3}{3}'
    assert problem['latex_problem'] == r'\int x^2 \, dx'


def test_format_preserves_native_hints_list(source):
    # jsonb returns a real list — it must NOT be json-decoded again.
    hints = [r'\text{step 1}', r'\text{step 2}']
    problem = source.format_problem({'solution': 'x', 'progressive_hints': hints})
    assert problem['progressive_hints'] == hints


def test_format_none_hints_becomes_empty_list(source):
    problem = source.format_problem({'solution': 'x', 'progressive_hints': None})
    assert problem['progressive_hints'] == []
