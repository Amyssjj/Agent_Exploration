"""Tests for SQLite schema creation."""
import sqlite3
import tempfile
from pathlib import Path

from oa.core.schema import create_schema


class TestSchema:
    def test_create_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            create_schema(db_path)

            assert db_path.exists()

            db = sqlite3.connect(str(db_path))
            tables = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            table_names = [t[0] for t in tables]

            assert "goal_metrics" in table_names
            assert "cron_runs" in table_names
            assert "daily_agent_activity" in table_names
            assert "spans" in table_names
            db.close()

    def test_schema_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            create_schema(db_path)
            create_schema(db_path)  # should not raise

    def test_goal_metrics_unique_constraint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            create_schema(db_path)

            db = sqlite3.connect(str(db_path))
            db.execute(
                "INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
                ("2026-03-15", "cron_reliability", "success_rate", 95.0, "%"),
            )
            db.commit()

            # Same key should conflict
            with __import__("pytest").raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
                    ("2026-03-15", "cron_reliability", "success_rate", 99.0, "%"),
                )
            db.close()

    def test_daily_agent_activity_unique_constraint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            create_schema(db_path)

            db = sqlite3.connect(str(db_path))
            db.execute(
                "INSERT INTO daily_agent_activity (date, agent_id, session_count, memory_logged) "
                "VALUES (?, ?, ?, ?)",
                ("2026-03-15", "researcher", 5, 1),
            )
            db.commit()

            with __import__("pytest").raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO daily_agent_activity (date, agent_id, session_count, memory_logged) "
                    "VALUES (?, ?, ?, ?)",
                    ("2026-03-15", "researcher", 10, 1),
                )
            db.close()

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nested" / "deep" / "test.db"
            create_schema(db_path)
            assert db_path.exists()
