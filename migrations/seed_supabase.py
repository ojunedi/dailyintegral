"""
Seed the Supabase `integrals` table from the local SQLite database.

Reads every row from integrals.db and upserts it into Supabase Postgres,
**preserving ids verbatim** (user_progress.problem_id references them).

Faithful migration:
  - text fields are stored exactly as in SQLite (the read-time backslash fix in
    SupabaseProblemSource reproduces today's grading behavior byte-for-byte).
  - progressive_hints is stored as native jsonb: the SQLite JSON *string* is parsed
    here so postgrest returns a real list (no json.loads needed at read time).

Idempotent: upserts on the `id` primary key, so re-running is safe.

Usage:
    # requires SUPABASE_URL + SUPABASE_SERVICE_KEY in .env.local
    uv run python -m migrations.seed_supabase
    uv run python -m migrations.seed_supabase path/to/integrals.db
"""
import json
import os
import sqlite3
import sys

from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Columns copied straight through (no transformation).
PASSTHROUGH_COLUMNS = [
    "id", "date", "problem", "solution", "hint", "difficulty",
    "topic", "latex_problem", "latex_solution",
    "created_at", "updated_at", "integral_type",
]


def _parse_hints(raw):
    """SQLite stores progressive_hints as a JSON string; return a real list for jsonb."""
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


def read_rows(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT * FROM integrals ORDER BY id")
        rows = []
        for r in cursor.fetchall():
            row = {col: r[col] for col in PASSTHROUGH_COLUMNS}
            row["progressive_hints"] = _parse_hints(r["progressive_hints"])
            rows.append(row)
        return rows
    finally:
        conn.close()


def main():
    load_dotenv(os.path.join(BASE_DIR, ".env.local"))

    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not service_key:
        sys.exit("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set (.env.local).")

    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "integrals.db")
    if not os.path.exists(db_path):
        sys.exit(f"ERROR: SQLite database not found: {db_path}")

    rows = read_rows(db_path)
    print(f"Read {len(rows)} rows from {db_path}")

    client = create_client(url, service_key)
    # Upsert on the primary key so re-runs are idempotent and ids are preserved.
    client.table("integrals").upsert(rows, on_conflict="id").execute()

    count = client.table("integrals").select("id", count="exact").execute()
    print(f"Upserted {len(rows)} rows. Supabase now has {count.count} integrals.")


if __name__ == "__main__":
    main()
