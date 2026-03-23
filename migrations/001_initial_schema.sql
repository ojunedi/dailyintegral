-- Initial schema: baseline from existing database
-- This migration is already applied to existing databases.

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
);
