-- Daily Integral: problems table in Supabase Postgres.
--
-- Mirrors the SQLite `integrals` schema (migrations/001_initial_schema.sql) so the
-- app can fetch the daily/random problem from Postgres instead of a local SQLite file.
--
-- IMPORTANT: ids are preserved verbatim from SQLite during seeding because
-- `user_progress.problem_id` references them. The seed script inserts explicit ids,
-- so this table uses a plain bigint PK (no identity/serial) — we set the values
-- ourselves and bump the sequence afterwards if we ever switch to auto-ids.

create table if not exists public.integrals (
    id                bigint primary key,
    date              date unique not null,
    problem           text not null,
    solution          text not null,
    hint              text,
    difficulty        text,
    topic             text,
    latex_problem     text,
    latex_solution    text,
    created_at        timestamptz default now(),
    updated_at        timestamptz default now(),
    progressive_hints jsonb,
    integral_type     text default 'indefinite'
);

-- Problems are public, read-only data. Enable RLS and allow anyone (anon + authed)
-- to SELECT. No insert/update/delete policy => writes are blocked for anon/authed
-- and only possible via the service role key (used by the seed script), which
-- bypasses RLS.
alter table public.integrals enable row level security;

drop policy if exists "Public can read integrals" on public.integrals;
create policy "Public can read integrals"
    on public.integrals
    for select
    to anon, authenticated
    using (true);

-- Table-level grant: SQL-created tables are NOT automatically reachable via the
-- Data API (PostgREST). RLS controls which *rows* are visible; this GRANT controls
-- whether the table is reachable at all by the anon/authenticated roles. Both are
-- required for the app's anon-key reads to work.
grant select on public.integrals to anon, authenticated;
