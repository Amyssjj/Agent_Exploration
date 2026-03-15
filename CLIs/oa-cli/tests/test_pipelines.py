"""Tests for built-in pipelines."""
import json
import tempfile
from pathlib import Path

from oa.core.config import AgentConfig, GoalConfig, MetricConfig, ProjectConfig
from oa.core.schema import create_schema
from oa.pipelines.cron_reliability import CronReliabilityPipeline
from oa.pipelines.team_health import TeamHealthPipeline


def _make_project(tmpdir: str) -> ProjectConfig:
    """Create a test project config with mock OpenClaw structure."""
    oc_home = Path(tmpdir) / "openclaw"
    db_path = Path(tmpdir) / "data" / "monitor.db"

    # Create OpenClaw structure
    cron_dir = oc_home / "cron"
    cron_dir.mkdir(parents=True)
    runs_dir = cron_dir / "runs"
    runs_dir.mkdir()
    sessions_dir = oc_home / "sessions"
    sessions_dir.mkdir()

    create_schema(db_path)

    config = ProjectConfig(openclaw_home=oc_home, db_path=db_path)
    config.agents = [
        AgentConfig(id="researcher", name="Researcher"),
        AgentConfig(id="writer", name="Writer"),
    ]
    config.goals = [
        GoalConfig(id="cron_reliability", name="Cron Reliability", builtin=True,
                   metrics=[MetricConfig(name="success_rate", unit="%", healthy=95, warning=80)]),
        GoalConfig(id="team_health", name="Team Health", builtin=True,
                   metrics=[MetricConfig(name="active_agent_count", unit="count", healthy=2, warning=1)]),
    ]
    return config


class TestCronReliabilityPipeline:
    def test_no_cron_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            pipeline = CronReliabilityPipeline()
            metrics = pipeline.collect("2026-03-15", config)

            assert len(metrics) == 1
            assert metrics[0].name == "success_rate"
            assert metrics[0].unit == "%"

    def test_with_cron_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            cron_dir = config.openclaw_home / "cron"

            # Create jobs.json
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
            (cron_dir / "jobs.json").write_text(json.dumps(jobs))

            # Create JSONL runs
            runs_dir = cron_dir / "runs"
            with open(runs_dir / "test-job.jsonl", "w") as f:
                f.write(json.dumps({"jobId": "test-job", "runId": "r1", "startedAt": "2026-03-15T07:00:00", "status": "completed"}) + "\n")
                f.write(json.dumps({"jobId": "test-job", "runId": "r2", "startedAt": "2026-03-15T12:00:00", "status": "completed"}) + "\n")
                f.write(json.dumps({"jobId": "test-job", "runId": "r3", "startedAt": "2026-03-15T19:00:00", "status": "failed"}) + "\n")

            pipeline = CronReliabilityPipeline()
            metrics = pipeline.collect("2026-03-15", config)

            assert len(metrics) == 1
            assert metrics[0].name == "success_rate"
            # 2 out of 3 succeeded = 66.7%
            assert abs(metrics[0].value - 66.7) < 0.1


class TestTeamHealthPipeline:
    def test_no_sessions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            pipeline = TeamHealthPipeline()
            metrics = pipeline.collect("2026-03-15", config)

            names = {m.name for m in metrics}
            assert "active_agent_count" in names
            assert "memory_discipline" in names

            active = next(m for m in metrics if m.name == "active_agent_count")
            assert active.value == 0

    def test_with_active_agents(self):
        import time
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_project(tmpdir)
            sessions_dir = config.openclaw_home / "sessions"

            # Create session files for today (matching agent pattern)
            (sessions_dir / "agent:researcher:discord:channel:123.json").write_text("{}")

            pipeline = TeamHealthPipeline()
            today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
            metrics = pipeline.collect(today, config)

            active = next(m for m in metrics if m.name == "active_agent_count")
            assert active.value >= 1
