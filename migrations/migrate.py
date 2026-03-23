"""
Lightweight SQLite migration runner.

Tracks applied migrations in a `schema_migrations` table.
Migrations are numbered SQL files (e.g., 001_initial_schema.sql).

Usage:
    python -m migrations.migrate                    # uses default integrals.db
    python -m migrations.migrate path/to/db.sqlite
"""
import sqlite3
import sys
import os

MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_applied_migrations(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  filename TEXT UNIQUE NOT NULL,"
        "  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ")"
    )
    cursor = conn.execute("SELECT filename FROM schema_migrations ORDER BY filename")
    return {row[0] for row in cursor.fetchall()}


def get_pending_migrations(applied):
    pending: list[str] = []
    for file in os.listdir(MIGRATIONS_DIR):
        if file.endswith('.sql') and file not in applied:
            pending.append(file)

    pending.sort()
    return pending


def run_migrations(db_path):
    conn = sqlite3.connect(db_path)
    applied = get_applied_migrations(conn)

    pending = get_pending_migrations(applied)

    if not pending:
        print("Database is up to date.")
        conn.close()
        return

    for filename in pending:
        filepath = os.path.join(MIGRATIONS_DIR, filename)
        print(f"Applying {filename}...")
        with open(filepath) as f:
            sql = f.read()
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_migrations (filename) VALUES (?)", (filename,))
        conn.commit()
        print(f"  Done.")

    print(f"Applied {len(pending)} migration(s).")
    conn.close()


if __name__ == "__main__":
    base_dir = os.path.dirname(MIGRATIONS_DIR)
    db = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, "integrals.db")
    print(f"Running migrations on {db}")
    run_migrations(db)
