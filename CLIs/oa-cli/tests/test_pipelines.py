"""Tests for built-in pipelines."""
import json
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from oa.core.config import AgentConfig, GoalConfig, MetricConfig, ProjectConfig
from oa.core.schema import create_schema
from oa.pipelines.cron_reliability import CronReliabilityPipeline
from oa.pipelines.team_health import TeamHealthPipeline


def _make_project(tmpdir: str) -> ProjectConfig:
    oc_home = Path(tmpdir) / "openclaw"
    db_path = Path(tmpdir) / "data" / "monitor.db"
    workspace_root = Path(tmpdir) / "workspace"

    cron_dir = oc_home / "cron"
    cron_dir.mkdir(parents=True)
    (cron_dir / "runs").mkdir()
    (oc_home / "sessions").mkdir()
    workspace_root.mkdir(parents=True)
    create_schema(db_path)

    config = ProjectConfig(openclaw_home=oc_home, workspace_root=workspace_root, db_path=db_path)
    config.memory_paths = ["memory/{date}.md", "MEMORY.md"]
    config.agents = [
        AgentConfig(id="main", name="Main"),
        AgentConfig(id="researcher", name="Researcher"),
    ]
    config.goals = [
        GoalConfig(
            id="cron_reliability",
            name="Cron Reliability",
            builtin=True,
            metrics=[
                MetricConfig(name="success_rate", unit="%", healthy=95, warning=80, direction="higher"),
                MetricConfig(name="failed_runs", unit="count", healthy=0, warning=1, direction="lower"),
                MetricConfig(name="unknown_runs", unit="count", healthy=0, warning=1, direction="lower"),
            ],
        ),
        GoalConfig(
            id="team_health",
            name="Team Health",
            builtin=True,
            metrics=[
                MetricConfig(name="active_agent_count", unit="count", healthy=2, warning=1, direction="higher"),
                MetricConfig(name="inactive_agent_count", unit="count", healthy=0, warning=1, direction="lower"),
                MetricConfig(name="memory_discipline", unit="%", healthy=80, warning=50, direction="higher"),
            ],
        ),
    ]
    return config


class TestCronReliabilityPipeline:
    def test_no_cron_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            pipeline = CronReliabilityPipeline()
            metrics = pipeline.collect("2026-03-15", config)
            names = {m.name for m in metrics}
            assert {"success_rate", "failed_runs", "unknown_runs"}.issubset(names)
            success = next(m for m in metrics if m.name == "success_rate")
            failed = next(m for m in metrics if m.name == "failed_runs")
            unknown = next(m for m in metrics if m.name == "unknown_runs")
            assert success.unit == "%"
            assert success.breakdown["mode"] == "no_data"
            assert failed.value == 0
            assert unknown.value == 0

    def test_with_observed_runs_from_realish_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            runs_dir = config.openclaw_home / "cron" / "runs"
            with open(runs_dir / "job-1.jsonl", "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": 1742022000000,
                    "jobId": "job-1",
                    "action": "finished",
                    "status": "ok",
                    "sessionKey": "agent:main:cron:job-1:run:abc",
                    "runAtMs": 1742022000000,
                    "durationMs": 5000,
                    "deliveryStatus": "not-delivered",
                    "usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
                }) + "\n")
                f.write(json.dumps({
                    "ts": 1742025600000,
                    "jobId": "job-1",
                    "action": "finished",
                    "status": "error",
                    "error": {"message": "cron: job execution timed out"},
                    "sessionKey": "agent:main:cron:job-1:run:def",
                    "runAtMs": 1742025600000,
                    "durationMs": 7000,
                }) + "\n")

            metrics = CronReliabilityPipeline().collect("2025-03-15", config)
            success = next(m for m in metrics if m.name == "success_rate")
            failed = next(m for m in metrics if m.name == "failed_runs")
            unknown = next(m for m in metrics if m.name == "unknown_runs")
            assert success.value == 50.0
            assert success.breakdown["mode"] == "observed_only"
            assert success.breakdown["failed"] == 1
            assert success.breakdown["failure_types"] == {"timeout": 1}
            assert success.breakdown["status_details"] == {"success": 1, "timeout": 1}
            assert failed.value == 1
            assert unknown.value == 0

            db = sqlite3.connect(str(config.db_path))
            rows = db.execute(
                "SELECT status, error, delivery_status FROM cron_runs ORDER BY run_at_ms ASC"
            ).fetchall()
            db.close()
            assert rows == [
                ("success", None, "not-delivered"),
                ("timeout", '{"message": "cron: job execution timed out"}', None),
            ]

    def test_classifies_delivery_errors_from_error_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            runs_dir = config.openclaw_home / "cron" / "runs"
            with open(runs_dir / "job-1.jsonl", "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": 1742022000000,
                    "jobId": "job-1",
                    "action": "finished",
                    "status": "error",
                    "error": "Delivering to QQ Bot requires target QQ Bot 目标格式: qqbot:c2c:openid (私聊) 或 qqbot:group:groupid (群聊)",
                    "deliveryStatus": "unknown",
                    "runAtMs": 1742022000000,
                }) + "\n")

            metrics = CronReliabilityPipeline().collect("2025-03-15", config)
            success = next(m for m in metrics if m.name == "success_rate")
            failed = next(m for m in metrics if m.name == "failed_runs")
            assert success.value == 0.0
            assert success.breakdown["failure_types"] == {"delivery_error": 1}
            assert success.breakdown["status_details"] == {"delivery_error": 1}
            assert failed.value == 1

            db = sqlite3.connect(str(config.db_path))
            row = db.execute(
                "SELECT status, error, delivery_status FROM cron_runs ORDER BY run_at_ms ASC"
            ).fetchone()
            db.close()
            assert row == (
                "delivery_error",
                "Delivering to QQ Bot requires target QQ Bot 目标格式: qqbot:c2c:openid (私聊) 或 qqbot:group:groupid (群聊)",
                "unknown",
            )

    def test_with_jobs_json_and_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            cron_dir = config.openclaw_home / "cron"
            jobs = {
                "jobs": [
                    {
                        "id": "test-job",
                        "name": "Test Job",
                        "schedule": {"kind": "cron", "expr": "0 7 * * *"},
                        "enabled": True,
                    }
                ]
            }
            (cron_dir / "jobs.json").write_text(json.dumps(jobs), encoding="utf-8")
            with open(cron_dir / "runs" / "test-job.jsonl", "w", encoding="utf-8") as f:
                f.write(json.dumps({"startedAt": "2026-03-15T07:00:00", "action": "finished", "status": "completed", "jobId": "test-job"}) + "\n")
                f.write(json.dumps({"startedAt": "2026-03-15T12:00:00", "action": "finished", "status": "failed", "jobId": "test-job"}) + "\n")
            metrics = CronReliabilityPipeline().collect("2026-03-15", config)
            success = next(m for m in metrics if m.name == "success_rate")
            failed = next(m for m in metrics if m.name == "failed_runs")
            unknown = next(m for m in metrics if m.name == "unknown_runs")
            assert abs(success.value - 50.0) < 0.1
            assert success.breakdown["mode"] == "scheduled_mode"
            assert success.breakdown["expected_slots"] == 1
            assert success.breakdown["observed_slots"] == 1
            assert success.breakdown["missed"] == 0
            assert success.breakdown["unexpected_runs"] == 1
            assert success.breakdown["success_rate_denominator"] == 2
            assert failed.value == 1
            assert unknown.value == 0

            per_job = success.breakdown["per_job"]["Test Job"]
            assert per_job["expected_slots"] == 1
            assert per_job["observed_slots"] == 1
            assert per_job["missed"] == 0
            assert per_job["unexpected_runs"] == 1

    def test_reports_expected_and_missed_slots_from_jobs_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            cron_dir = config.openclaw_home / "cron"
            jobs = {
                "jobs": [
                    {
                        "id": "test-job",
                        "name": "Test Job",
                        "schedule": {"kind": "cron", "expr": "0 7,12,19 * * *"},
                        "enabled": True,
                    }
                ]
            }
            (cron_dir / "jobs.json").write_text(json.dumps(jobs), encoding="utf-8")
            with open(cron_dir / "runs" / "test-job.jsonl", "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "startedAt": "2026-03-15T07:00:00",
                    "action": "finished",
                    "status": "completed",
                    "jobId": "test-job",
                }) + "\n")
                f.write(json.dumps({
                    "startedAt": "2026-03-15T12:00:00",
                    "action": "finished",
                    "status": "failed",
                    "jobId": "test-job",
                }) + "\n")

            metrics = CronReliabilityPipeline().collect("2026-03-15", config)
            success = next(m for m in metrics if m.name == "success_rate")

            assert abs(success.value - 33.3) < 0.1
            assert success.breakdown["mode"] == "scheduled_mode"
            assert success.breakdown["expected_slots"] == 3
            assert success.breakdown["observed_slots"] == 2
            assert success.breakdown["missed"] == 1
            assert success.breakdown["unexpected_runs"] == 0
            assert success.breakdown["success_rate_denominator"] == 3
            assert success.breakdown["missed_slots"] == [
                {"cron_name": "Test Job", "job_id": "test-job", "slot_time": "19:00:00"}
            ]

            per_job = success.breakdown["per_job"]["Test Job"]
            assert per_job["expected_slots"] == 3
            assert per_job["observed_slots"] == 2
            assert per_job["missed"] == 1
            assert per_job["missed_slot_times"] == ["19:00:00"]

    def test_reports_expected_and_missed_slots_from_every_schedule_with_anchor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            cron_dir = config.openclaw_home / "cron"
            anchor_ms = int(datetime(2026, 3, 14, 23, 0, 0).timestamp() * 1000)
            jobs = {
                "jobs": [
                    {
                        "id": "interval-job",
                        "name": "Interval Job",
                        "schedule": {"kind": "every", "everyMs": 6 * 60 * 60 * 1000, "anchorMs": anchor_ms},
                        "enabled": True,
                    }
                ]
            }
            (cron_dir / "jobs.json").write_text(json.dumps(jobs), encoding="utf-8")
            with open(cron_dir / "runs" / "interval-job.jsonl", "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "startedAt": "2026-03-15T05:00:00",
                    "action": "finished",
                    "status": "completed",
                    "jobId": "interval-job",
                }) + "\n")
                f.write(json.dumps({
                    "startedAt": "2026-03-15T17:00:00",
                    "action": "finished",
                    "status": "failed",
                    "jobId": "interval-job",
                }) + "\n")

            metrics = CronReliabilityPipeline().collect("2026-03-15", config)
            success = next(m for m in metrics if m.name == "success_rate")

            assert abs(success.value - 25.0) < 0.1
            assert success.breakdown["mode"] == "scheduled_mode"
            assert success.breakdown["expected_slots"] == 4
            assert success.breakdown["observed_slots"] == 2
            assert success.breakdown["missed"] == 2
            assert success.breakdown["unexpected_runs"] == 0
            assert success.breakdown["success_rate_denominator"] == 4
            assert success.breakdown["missed_slots"] == [
                {"cron_name": "Interval Job", "job_id": "interval-job", "slot_time": "11:00:00"},
                {"cron_name": "Interval Job", "job_id": "interval-job", "slot_time": "23:00:00"},
            ]

            per_job = success.breakdown["per_job"]["Interval Job"]
            assert per_job["expected_slots"] == 4
            assert per_job["observed_slots"] == 2
            assert per_job["missed"] == 2
            assert per_job["missed_slot_times"] == ["11:00:00", "23:00:00"]

    def test_reports_unanchored_every_schedule_using_epoch_alignment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            cron_dir = config.openclaw_home / "cron"
            jobs = {
                "jobs": [
                    {
                        "id": "daily-interval",
                        "name": "Daily Interval",
                        "schedule": {"kind": "every", "everyMs": 24 * 60 * 60 * 1000},
                        "enabled": True,
                    }
                ]
            }
            (cron_dir / "jobs.json").write_text(json.dumps(jobs), encoding="utf-8")

            metrics = CronReliabilityPipeline().collect("2026-03-15", config)
            success = next(m for m in metrics if m.name == "success_rate")
            expected_slot_time = datetime.fromtimestamp(0).strftime("%H:%M:%S")

            assert success.breakdown["expected_slots"] == 1
            assert success.breakdown["observed_slots"] == 0
            assert success.breakdown["missed"] == 1
            assert success.breakdown["unexpected_runs"] == 0
            assert success.breakdown["missed_slots"] == [
                {"cron_name": "Daily Interval", "job_id": "daily-interval", "slot_time": expected_slot_time}
            ]

            per_job = success.breakdown["per_job"]["Daily Interval"]
            assert per_job["expected_slots"] == 1
            assert per_job["missed_slot_times"] == [expected_slot_time]

    def test_marks_subminute_every_schedule_unsupported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            cron_dir = config.openclaw_home / "cron"
            jobs = {
                "jobs": [
                    {
                        "id": "fast-interval",
                        "name": "Fast Interval",
                        "schedule": {"kind": "every", "everyMs": 30 * 1000},
                        "enabled": True,
                    }
                ]
            }
            (cron_dir / "jobs.json").write_text(json.dumps(jobs), encoding="utf-8")

            metrics = CronReliabilityPipeline().collect("2026-03-15", config)
            success = next(m for m in metrics if m.name == "success_rate")

            assert success.breakdown["expected_slots"] == 0
            assert success.breakdown["observed_slots"] == 0
            assert success.breakdown["missed"] == 0
            assert success.breakdown["unsupported_schedules"] == [
                {
                    "job_id": "fast-interval",
                    "cron_name": "Fast Interval",
                    "schedule_kind": "every",
                    "expr": None,
                    "reason": "every schedule under 60000ms not supported at current minute slot precision",
                }
            ]

    def test_unknown_statuses_are_counted_separately(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            runs_dir = config.openclaw_home / "cron" / "runs"
            with open(runs_dir / "job-unknown.jsonl", "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "startedAt": "2026-03-15T07:00:00",
                    "action": "finished",
                    "status": "mystery",
                    "jobId": "job-unknown",
                }) + "\n")

            metrics = CronReliabilityPipeline().collect("2026-03-15", config)
            success = next(m for m in metrics if m.name == "success_rate")
            failed = next(m for m in metrics if m.name == "failed_runs")
            unknown = next(m for m in metrics if m.name == "unknown_runs")
            assert success.value == 0.0
            assert failed.value == 0
            assert unknown.value == 1
            assert success.breakdown["unknown"] == 1


class TestTeamHealthPipeline:
    def test_no_sessions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            metrics = TeamHealthPipeline().collect("2026-03-15", config)
            names = {m.name for m in metrics}
            assert {"active_agent_count", "inactive_agent_count", "memory_discipline"}.issubset(names)
            active = next(m for m in metrics if m.name == "active_agent_count")
            inactive = next(m for m in metrics if m.name == "inactive_agent_count")
            assert active.value == 0
            assert inactive.value == 2

    def test_with_active_agent_and_workspace_memory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            sessions_dir = config.openclaw_home / "sessions"
            session_file = sessions_dir / "agent:main:main.json"
            session_file.write_text("{}", encoding="utf-8")
            target_ts = datetime(2026, 3, 15, 9, 0, 0).timestamp()
            os.utime(session_file, (target_ts, target_ts))

            memory_dir = config.workspace_root / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "2026-03-15.md").write_text("- did work\n", encoding="utf-8")

            metrics = TeamHealthPipeline().collect("2026-03-15", config)
            active = next(m for m in metrics if m.name == "active_agent_count")
            inactive = next(m for m in metrics if m.name == "inactive_agent_count")
            discipline = next(m for m in metrics if m.name == "memory_discipline")
            assert active.value >= 1
            assert inactive.value == 1
            assert discipline.value == 100.0

    def test_with_active_agent_from_agent_session_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            sessions_dir = config.openclaw_home / "agents" / "main" / "sessions"
            sessions_dir.mkdir(parents=True)
            session_file = sessions_dir / "recent.jsonl"
            session_file.write_text("{}", encoding="utf-8")
            target_ts = datetime(2026, 3, 15, 9, 0, 0).timestamp()
            os.utime(session_file, (target_ts, target_ts))

            metrics = TeamHealthPipeline().collect("2026-03-15", config)
            active = next(m for m in metrics if m.name == "active_agent_count")
            inactive = next(m for m in metrics if m.name == "inactive_agent_count")
            assert active.value >= 1
            assert inactive.value == 1

    def test_with_historical_activity_from_session_contents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            sessions_dir = config.openclaw_home / "agents" / "main" / "sessions"
            sessions_dir.mkdir(parents=True)
            session_file = sessions_dir / "recent.jsonl"
            session_file.write_text(
                json.dumps({"type": "session", "timestamp": "2026-03-14T08:00:00"}) + "\n"
                + json.dumps({"type": "message", "timestamp": "2026-03-14T09:30:00"}) + "\n",
                encoding="utf-8",
            )
            target_ts = datetime(2026, 3, 15, 12, 0, 0).timestamp()
            os.utime(session_file, (target_ts, target_ts))

            metrics = TeamHealthPipeline().collect("2026-03-14", config)
            active = next(m for m in metrics if m.name == "active_agent_count")
            inactive = next(m for m in metrics if m.name == "inactive_agent_count")
            assert active.value == 1
            assert inactive.value == 1

            db = sqlite3.connect(str(config.db_path))
            row = db.execute(
                "SELECT session_count, last_active FROM daily_agent_activity WHERE date = ? AND agent_id = ?",
                ("2026-03-14", "main"),
            ).fetchone()
            db.close()
            assert row == (1, "2026-03-14T09:30:00")
