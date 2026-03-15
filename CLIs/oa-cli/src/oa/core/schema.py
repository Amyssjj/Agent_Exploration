"""SQLite schema creation for OA."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
-- Goal metrics: daily goal values
CREATE TABLE IF NOT EXISTS goal_metrics (
    date       TEXT NOT NULL,
    goal       TEXT NOT NULL,
    metric     TEXT NOT NULL,
    value      REAL,
    unit       TEXT DEFAULT '',
    breakdown  TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, goal, metric)
);

-- Cron run outcomes: per-slot results
CREATE TABLE IF NOT EXISTS cron_runs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT NOT NULL,
    cron_name  TEXT NOT NULL,
    slot_time  TEXT,
    status     TEXT NOT NULL DEFAULT 'unknown',
    job_id     TEXT,
    run_id     TEXT,
    error      TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Daily agent activity: per-agent daily snapshot
CREATE TABLE IF NOT EXISTS daily_agent_activity (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT NOT NULL,
    agent_id       TEXT NOT NULL,
    session_count  INTEGER DEFAULT 0,
    memory_logged  INTEGER DEFAULT 0,
    last_active    TEXT,
    created_at     TEXT DEFAULT (datetime('now')),
    UNIQUE(date, agent_id)
);

-- OTel-compatible trace spans
CREATE TABLE IF NOT EXISTS spans (
    span_id        TEXT PRIMARY KEY,
    trace_id       TEXT NOT NULL,
    parent_span_id TEXT,
    name           TEXT NOT NULL,
    service        TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'ok',
    start_time     TEXT NOT NULL,
    end_time       TEXT,
    duration_ms    REAL,
    attributes     TEXT,
    events         TEXT,
    created_at     TEXT DEFAULT (datetime('now'))
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_goal_metrics_date ON goal_metrics(date);
CREATE INDEX IF NOT EXISTS idx_goal_metrics_goal ON goal_metrics(goal);
CREATE INDEX IF NOT EXISTS idx_cron_runs_date ON cron_runs(date);
CREATE INDEX IF NOT EXISTS idx_cron_runs_name ON cron_runs(cron_name);
CREATE INDEX IF NOT EXISTS idx_daa_date ON daily_agent_activity(date);
CREATE INDEX IF NOT EXISTS idx_daa_agent ON daily_agent_activity(agent_id);
CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_time ON spans(start_time);
CREATE INDEX IF NOT EXISTS idx_spans_service ON spans(service);
"""


def create_schema(db_path: Path | str) -> None:
    """Create all OA tables and indexes. Idempotent (uses IF NOT EXISTS)."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(str(db_path))
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA_SQL)
    db.executescript(INDEX_SQL)
    db.close()
