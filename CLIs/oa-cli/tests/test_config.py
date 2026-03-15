"""Tests for config loading, saving, and generation."""
import tempfile
from pathlib import Path

import pytest

from oa.core.config import AgentConfig, GoalConfig, MetricConfig, ProjectConfig
from oa.core.scanner import ScanResult, AgentInfo, CronJobInfo


class TestMetricConfig:
    def test_defaults(self):
        m = MetricConfig(name="test")
        assert m.name == "test"
        assert m.unit == ""
        assert m.healthy == 0
        assert m.warning == 0

    def test_with_values(self):
        m = MetricConfig(name="rate", unit="%", healthy=95, warning=80)
        assert m.unit == "%"
        assert m.healthy == 95


class TestGoalConfig:
    def test_builtin_goal(self):
        g = GoalConfig(
            id="cron_reliability",
            name="Cron Reliability",
            builtin=True,
            metrics=[MetricConfig(name="success_rate", unit="%", healthy=95, warning=80)],
        )
        assert g.builtin is True
        assert len(g.metrics) == 1
        assert g.pipeline is None

    def test_custom_goal(self):
        g = GoalConfig(
            id="custom",
            name="Custom",
            builtin=False,
            pipeline="pipelines/custom.py",
        )
        assert g.builtin is False
        assert g.pipeline == "pipelines/custom.py"


class TestProjectConfig:
    def test_defaults(self):
        c = ProjectConfig()
        assert len(c.agents) == 0
        assert len(c.goals) == 0
        assert c.db_path == Path("data/monitor.db")

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            original = ProjectConfig()
            original.agents.append(AgentConfig(id="researcher", name="Researcher"))
            original.agents.append(AgentConfig(id="writer", name="Writer"))
            original.goals.append(GoalConfig(
                id="cron_reliability",
                name="Cron Reliability",
                builtin=True,
                metrics=[MetricConfig(name="success_rate", unit="%", healthy=95, warning=80)],
            ))
            original.goals.append(GoalConfig(
                id="custom",
                name="Custom Goal",
                builtin=False,
                pipeline="pipelines/custom.py",
                metrics=[MetricConfig(name="score", unit="count", healthy=10, warning=5)],
            ))

            original.save(config_path)
            loaded = ProjectConfig.load(config_path)

            assert len(loaded.agents) == 2
            assert loaded.agents[0].id == "researcher"
            assert loaded.agents[1].name == "Writer"

            assert len(loaded.goals) == 2
            assert loaded.goals[0].id == "cron_reliability"
            assert loaded.goals[0].builtin is True
            assert loaded.goals[0].metrics[0].healthy == 95

            assert loaded.goals[1].pipeline == "pipelines/custom.py"
            assert loaded.goals[1].builtin is False

    def test_from_scan_with_agents(self):
        scan = ScanResult(
            openclaw_home=Path("/tmp/fake-openclaw"),
            found=True,
            agents=[
                AgentInfo(id="researcher", name="Researcher"),
                AgentInfo(id="writer", name="Writer"),
                AgentInfo(id="reviewer", name="Reviewer"),
                AgentInfo(id="publisher", name="Publisher"),
            ],
            cron_jobs=[
                CronJobInfo(id="job1", name="Daily Job", schedule="0 7 * * *"),
            ],
            session_count=100,
        )

        config = ProjectConfig.from_scan(scan)

        assert len(config.agents) == 4
        assert config.agents[0].id == "researcher"

        # Should have 2 built-in goals
        assert len(config.goals) == 2
        assert config.goals[0].id == "cron_reliability"
        assert config.goals[0].builtin is True
        assert config.goals[1].id == "team_health"
        assert config.goals[1].builtin is True

        # Team health threshold should be based on agent count
        active_metric = config.goals[1].metrics[0]
        assert active_metric.name == "active_agent_count"
        assert active_metric.healthy == 3  # 75% of 4

    def test_from_scan_empty(self):
        scan = ScanResult(openclaw_home=Path("/tmp/fake"), found=False)
        config = ProjectConfig.from_scan(scan)
        assert len(config.agents) == 0
        assert len(config.goals) == 2  # built-ins still added
