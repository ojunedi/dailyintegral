"""
Integration tests for authenticated progress endpoints and auth middleware.

Supabase calls (auth token validation and DB operations) are mocked so these
tests run fully offline without any network or real credentials.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from app import create_app

# Use a dummy path — progress endpoints only touch Supabase, not SQLite.
TEST_DB = os.path.join(os.path.dirname(__file__), 'test_auth_progress_dummy.db')

VALID_ENTRY = {
    'date': '2025-01-01',
    'problem_id': 1,
    'is_correct': True,
    'difficulty': 'easy',
}

AUTH_HEADER = {'Authorization': 'Bearer valid-test-token'}


@pytest.fixture()
def client():
    os.environ['DATABASE_PATH'] = TEST_DB
    app = create_app('testing')
    app.config['DATABASE_PATH'] = TEST_DB
    with app.test_client() as c:
        yield c


def _mock_auth_client(user_id='test-user-123'):
    """Returns a mock supabase client that accepts any Bearer token."""
    mock = MagicMock()
    mock.auth.get_user.return_value.user.id = user_id
    return mock


def _mock_service_client(progress_rows=None):
    """Returns a mock service client. progress_rows used for get_progress response."""
    mock = MagicMock()
    rows = progress_rows if progress_rows is not None else []
    (
        mock.table.return_value
            .select.return_value
            .eq.return_value
            .order.return_value
            .execute.return_value
            .data
    )
    mock.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = rows
    return mock


# ── Auth middleware ──────────────────────────────────────────────────

class TestAuthMiddleware:

    def test_no_auth_header_returns_401(self, client):
        resp = client.post('/api/progress', json=VALID_ENTRY)
        assert resp.status_code == 401
        assert resp.get_json()['success'] is False

    def test_non_bearer_scheme_returns_401(self, client):
        resp = client.post(
            '/api/progress',
            json=VALID_ENTRY,
            headers={'Authorization': 'Basic abc123'},
        )
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        with patch('app.auth.get_supabase_client') as mock_get:
            mock_get.return_value.auth.get_user.side_effect = Exception('token expired')
            resp = client.post(
                '/api/progress',
                json=VALID_ENTRY,
                headers={'Authorization': 'Bearer bad-token'},
            )
        assert resp.status_code == 401
        assert 'invalid' in resp.get_json()['error'].lower()

    def test_get_progress_requires_auth(self, client):
        resp = client.get('/api/progress')
        assert resp.status_code == 401

    def test_sync_requires_auth(self, client):
        resp = client.post('/api/progress/sync', json={'entries': [VALID_ENTRY]})
        assert resp.status_code == 401


# ── Progress endpoints (authenticated) ──────────────────────────────

class TestProgressEndpoints:

    def test_save_progress_success(self, client):
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()), \
             patch('app.progress.get_service_client', return_value=_mock_service_client()):
            resp = client.post('/api/progress', json=VALID_ENTRY, headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'saved' in data['message'].lower()

    def test_save_progress_invalid_date(self, client):
        bad_entry = {**VALID_ENTRY, 'date': 'not-a-date'}
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()):
            resp = client.post('/api/progress', json=bad_entry, headers=AUTH_HEADER)
        assert resp.status_code == 400
        assert resp.get_json()['success'] is False

    def test_save_progress_invalid_difficulty(self, client):
        bad_entry = {**VALID_ENTRY, 'difficulty': 'ultra-hard'}
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()):
            resp = client.post('/api/progress', json=bad_entry, headers=AUTH_HEADER)
        assert resp.status_code == 400

    def test_save_progress_no_body_returns_400(self, client):
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()):
            resp = client.post('/api/progress', content_type='application/json', headers=AUTH_HEADER)
        assert resp.status_code == 400

    def test_get_progress_returns_results(self, client):
        rows = [
            {'date': '2025-01-01', 'problem_id': 1, 'is_correct': True,
             'difficulty': 'easy', 'submitted_at': None},
        ]
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()), \
             patch('app.progress.get_service_client', return_value=_mock_service_client(rows)):
            resp = client.get('/api/progress', headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert isinstance(data['results'], list)
        assert len(data['results']) == 1

    def test_get_progress_empty(self, client):
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()), \
             patch('app.progress.get_service_client', return_value=_mock_service_client([])):
            resp = client.get('/api/progress', headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.get_json()['results'] == []

    def test_sync_progress_success(self, client):
        payload = {'entries': [VALID_ENTRY]}
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()), \
             patch('app.progress.get_service_client', return_value=_mock_service_client()):
            resp = client.post('/api/progress/sync', json=payload, headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert '1' in data['message']  # "Synced 1 entries"

    def test_sync_progress_multiple_entries(self, client):
        entries = [
            {**VALID_ENTRY, 'date': '2025-01-01'},
            {**VALID_ENTRY, 'date': '2025-01-02', 'is_correct': False},
            {**VALID_ENTRY, 'date': '2025-01-03', 'difficulty': 'hard'},
        ]
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()), \
             patch('app.progress.get_service_client', return_value=_mock_service_client()):
            resp = client.post('/api/progress/sync', json={'entries': entries}, headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_sync_empty_entries_rejected(self, client):
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()):
            resp = client.post('/api/progress/sync', json={'entries': []}, headers=AUTH_HEADER)
        assert resp.status_code == 400

    def test_sync_no_body_returns_400(self, client):
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()):
            resp = client.post('/api/progress/sync', content_type='application/json', headers=AUTH_HEADER)
        assert resp.status_code == 400

    def test_sync_invalid_entry_rejected(self, client):
        bad_entries = [{'date': 'bad', 'problem_id': 1, 'is_correct': True, 'difficulty': 'easy'}]
        with patch('app.auth.get_supabase_client', return_value=_mock_auth_client()):
            resp = client.post('/api/progress/sync', json={'entries': bad_entries}, headers=AUTH_HEADER)
        assert resp.status_code == 400
