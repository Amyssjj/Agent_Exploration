"""Tests for the OA dashboard server."""
import io
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from oa.core.config import AgentConfig, GoalConfig, MetricConfig, ProjectConfig
from oa.core.schema import create_schema
from oa.server import OAHandler, _health_status


def _setup_project(tmpdir: str) -> str:
    """Create a test project with config + data."""
    project = Path(tmpdir)
    db_path = project / "data" / "monitor.db"
    config_path = project / "config.yaml"

    config = ProjectConfig(db_path=db_path)
    config.agents = [
        AgentConfig(id="researcher", name="Researcher"),
        AgentConfig(id="writer", name="Writer"),
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
    config.save(config_path)
    create_schema(db_path)

    # Insert test data
    db = sqlite3.connect(str(db_path))
    db.execute("INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
               ("2026-03-15", "cron_reliability", "success_rate", 92.5, "%"))
    db.execute("INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
               ("2026-03-14", "cron_reliability", "success_rate", 88.0, "%"))
    db.execute("INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
               ("2026-03-15", "cron_reliability", "failed_runs", 1, "count"))
    db.execute("INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
               ("2026-03-15", "cron_reliability", "unknown_runs", 0, "count"))
    db.execute("INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
               ("2026-03-15", "team_health", "active_agent_count", 2, "count"))
    db.execute("INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
               ("2026-03-15", "team_health", "inactive_agent_count", 0, "count"))
    db.execute("INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
               ("2026-03-15", "team_health", "memory_discipline", 100, "%"))
    db.execute("INSERT INTO cron_runs (date, cron_name, status, job_id, delivery_status, error) VALUES (?, ?, ?, ?, ?, ?)",
               ("2026-03-15", "daily-job", "timeout", "job-1", "not-delivered", "cron: job execution timed out"))
    db.execute("INSERT INTO daily_agent_activity (date, agent_id, session_count, memory_logged) VALUES (?, ?, ?, ?)",
               ("2026-03-15", "researcher", 5, 1))
    db.commit()
    db.close()

    return str(config_path)


def _dispatch(config_path: str, path: str) -> tuple[int | None, dict[str, str], bytes]:
    OAHandler.config_path = config_path
    OAHandler._config_cache = None

    handler = object.__new__(OAHandler)
    handler.path = path
    handler.command = "GET"
    handler.request_version = "HTTP/1.1"
    handler.wfile = io.BytesIO()
    handler._status = None
    handler._headers = {}
    handler.send_response = lambda status: setattr(handler, "_status", status)
    handler.send_header = lambda key, value: handler._headers.__setitem__(key, value)
    handler.end_headers = lambda: None

    handler.do_GET()
    return handler._status, handler._headers, handler.wfile.getvalue()


def _get(config_path: str, path: str) -> dict | list | str:
    """Fetch from the test server handler without opening a socket."""
    status, headers, body = _dispatch(config_path, path)
    assert status == 200
    text = body.decode()
    ct = headers.get("Content-Type", "")
    if "json" in ct:
        return json.loads(text)
    return text


def _get_raw(config_path: str, path: str) -> tuple[int | None, dict[str, str], bytes]:
    """Fetch raw response details from the test server handler."""
    return _dispatch(config_path, path)


@pytest.fixture(scope="module")
def server():
    """Prepare a test project config for direct handler execution."""
    tmpdir = tempfile.mkdtemp()
    config_path = _setup_project(tmpdir)
    yield config_path


class TestServerAPI:
    def test_api_goals(self, server):
        goals = _get(server, "/api/goals")
        assert len(goals) == 2
        assert goals[0]["id"] == "cron_reliability"
        assert goals[0]["metrics"]["success_rate"]["value"] == 92.5
        assert goals[0]["metrics"]["success_rate"]["status"] == "warning"  # 92.5 < 95
        assert goals[0]["metrics"]["failed_runs"]["value"] == 1
        assert goals[0]["metrics"]["failed_runs"]["status"] == "warning"
        assert goals[0]["metrics"]["unknown_runs"]["value"] == 0
        assert goals[0]["metrics"]["unknown_runs"]["status"] == "healthy"
        assert goals[0]["healthStatus"] == "warning"

    def test_api_goals_trend(self, server):
        goals = _get(server, "/api/goals")
        trend = goals[0]["metrics"]["success_rate"]["trend"]
        assert trend == 4.5  # 92.5 - 88.0

    def test_api_goals_sparkline(self, server):
        goals = _get(server, "/api/goals")
        assert len(goals[0]["sparkline"]) == 2  # 2 dates of data

    def test_api_goals_team_health(self, server):
        goals = _get(server, "/api/goals")
        th = goals[1]
        assert th["id"] == "team_health"
        assert th["metrics"]["active_agent_count"]["value"] == 2
        assert th["metrics"]["memory_discipline"]["value"] == 100
        assert th["healthStatus"] == "healthy"

    def test_api_health_summary(self, server):
        health = _get(server, "/api/health")
        assert health["goals"] == 2
        assert health["overall"] in ("healthy", "warning", "critical")
        assert health["lastCollected"] == "2026-03-15"
        assert health["healthy"] >= 0
        assert health["warning"] >= 0

    def test_api_cron_chart(self, server):
        cron = _get(server, "/api/cron-chart")
        assert len(cron) == 1
        assert cron[0]["cron_name"] == "daily-job"
        assert cron[0]["status"] == "failure"
        assert cron[0]["status_detail"] == "timeout"
        assert cron[0]["delivery_status"] == "not-delivered"

    def test_api_team_health_endpoint(self, server):
        team = _get(server, "/api/team-health")
        assert len(team) == 1
        assert team[0]["agent_id"] == "researcher"
        assert team[0]["session_count"] == 5

    def test_api_traces_empty(self, server):
        traces = _get(server, "/api/traces")
        assert traces == []

    def test_api_config(self, server):
        cfg = _get(server, "/api/config")
        assert len(cfg["agents"]) == 2
        assert len(cfg["goals"]) == 2
        cron_metrics = {m["name"]: m for m in cfg["goals"][0]["metrics"]}
        assert cron_metrics["unknown_runs"]["direction"] == "lower"

    def test_api_goal_metrics(self, server):
        metrics = _get(server, "/api/goals/metrics")
        assert "cron_reliability" in metrics

        cron_rows = metrics["cron_reliability"]
        assert len(cron_rows) == 4
        assert {(row["date"], row["metric"]) for row in cron_rows} == {
            ("2026-03-14", "success_rate"),
            ("2026-03-15", "success_rate"),
            ("2026-03-15", "failed_runs"),
            ("2026-03-15", "unknown_runs"),
        }

    def test_static_index(self, server):
        status, headers, body = _get_raw(server, "/")
        html = body.decode()
        assert status == 200
        assert "OA Dashboard" in html
        assert headers.get("Content-Type") == "text/html"

    def test_404_unknown_path(self, server):
        status, headers, body = _get_raw(server, "/api/nonexistent")
        assert status == 404
        assert headers.get("Content-Type") == "application/json"
        assert json.loads(body.decode()) == {"error": "not found"}
