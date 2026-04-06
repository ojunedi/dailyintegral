"""Supabase progress CRUD helpers."""

from supabase import Client, create_client
from flask import current_app


def get_service_client() -> Client:
    """Create a Supabase client with the service role key (bypasses RLS)."""
    url = current_app.config['SUPABASE_URL']
    key = current_app.config['SUPABASE_SERVICE_KEY']
    return create_client(url, key)


def save_progress(user_id: str, date: str, problem_id: int, is_correct: bool, difficulty: str):
    """Insert a single progress row. Uses ON CONFLICT DO NOTHING for idempotency."""
    client = get_service_client()
    client.table('user_progress').upsert(
        {
            'user_id': user_id,
            'date': date,
            'problem_id': problem_id,
            'is_correct': is_correct,
            'difficulty': difficulty,
        },
        on_conflict='user_id,date',
    ).execute()


def get_progress(user_id: str) -> list[dict]:
    """Fetch all progress rows for a user, ordered by date."""
    client = get_service_client()
    response = (
        client.table('user_progress')
        .select('date, problem_id, is_correct, difficulty, submitted_at')
        .eq('user_id', user_id)
        .order('date')
        .execute()
    )
    return response.data


def sync_progress(user_id: str, entries: list[dict]):
    """Bulk upsert progress entries. Idempotent via ON CONFLICT DO NOTHING."""
    if not entries:
        return
    rows = [
        {
            'user_id': user_id,
            'date': e['date'],
            'problem_id': e['problem_id'],
            'is_correct': e['is_correct'],
            'difficulty': e['difficulty'],
        }
        for e in entries
    ]
    client = get_service_client()
    client.table('user_progress').upsert(
        rows,
        on_conflict='user_id,date',
    ).execute()
