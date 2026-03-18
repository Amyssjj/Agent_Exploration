"""Tests for the OA dashboard server."""
import json
import sqlite3
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from oa.core.config import AgentConfig, GoalConfig, MetricConfig, ProjectConfig
from oa.core.schema import create_schema
from oa.server import OAHandler, serve

PORT = 18456  # single port for all tests


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
        GoalConfig(id="cron_reliability", name="Cron Reliability", builtin=True,
                   metrics=[MetricConfig(name="success_rate", unit="%", healthy=95, warning=80)]),
        GoalConfig(id="team_health", name="Team Health", builtin=True,
                   metrics=[
                       MetricConfig(name="active_agent_count", unit="count", healthy=2, warning=1),
                       MetricConfig(name="memory_discipline", unit="%", healthy=80, warning=50),
                   ]),
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
               ("2026-03-15", "team_health", "active_agent_count", 2, "count"))
    db.execute("INSERT INTO goal_metrics (date, goal, metric, value, unit) VALUES (?, ?, ?, ?, ?)",
               ("2026-03-15", "team_health", "memory_discipline", 100, "%"))
    db.execute("INSERT INTO cron_runs (date, cron_name, status, job_id) VALUES (?, ?, ?, ?)",
               ("2026-03-15", "daily-job", "success", "job-1"))
    db.execute("INSERT INTO daily_agent_activity (date, agent_id, session_count, memory_logged) VALUES (?, ?, ?, ?)",
               ("2026-03-15", "researcher", 5, 1))
    db.commit()
    db.close()

    return str(config_path)


def _get(path: str) -> dict | list | str:
    """Fetch from the test server."""
    url = f"http://localhost:{PORT}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode()
        ct = resp.headers.get("Content-Type", "")
        if "json" in ct:
            return json.loads(body)
        return body


def _get_raw(path: str):
    """Fetch raw response from the test server."""
    url = f"http://localhost:{PORT}{path}"
    req = urllib.request.Request(url)
    return urllib.request.urlopen(req, timeout=10)


@pytest.fixture(scope="module")
def server():
    """Start a single server for all tests in this module."""
    tmpdir = tempfile.mkdtemp()
    config_path = _setup_project(tmpdir)

    from http.server import HTTPServer
    OAHandler.config_path = config_path
    OAHandler._config_cache = None

    httpd = HTTPServer(("127.0.0.1", PORT), OAHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(1.0)  # wait for server to be ready
    yield httpd
    httpd.shutdown()


class TestServerAPI:
    def test_api_goals(self, server):
        goals = _get("/api/goals")
        assert len(goals) == 2
        assert goals[0]["id"] == "cron_reliability"
        assert goals[0]["metrics"]["success_rate"]["value"] == 92.5
        assert goals[0]["metrics"]["success_rate"]["status"] == "warning"  # 92.5 < 95
        assert goals[0]["healthStatus"] == "warning"

    def test_api_goals_trend(self, server):
        goals = _get("/api/goals")
        trend = goals[0]["metrics"]["success_rate"]["trend"]
        assert trend == 4.5  # 92.5 - 88.0

    def test_api_goals_sparkline(self, server):
        goals = _get("/api/goals")
        assert len(goals[0]["sparkline"]) == 2  # 2 dates of data

    def test_api_goals_team_health(self, server):
        goals = _get("/api/goals")
        th = goals[1]
        assert th["id"] == "team_health"
        assert th["metrics"]["active_agent_count"]["value"] == 2
        assert th["metrics"]["memory_discipline"]["value"] == 100
        assert th["healthStatus"] == "healthy"

    def test_api_health_summary(self, server):
        health = _get("/api/health")
        assert health["goals"] == 2
        assert health["overall"] in ("healthy", "warning", "critical")
        assert health["lastCollected"] == "2026-03-15"
        assert health["healthy"] >= 0
        assert health["warning"] >= 0

    def test_api_cron_chart(self, server):
        cron = _get("/api/cron-chart")
        assert len(cron) == 1
        assert cron[0]["cron_name"] == "daily-job"
        assert cron[0]["status"] == "success"

    def test_api_team_health_endpoint(self, server):
        team = _get("/api/team-health")
        assert len(team) == 1
        assert team[0]["agent_id"] == "researcher"
        assert team[0]["session_count"] == 5

    def test_api_traces_empty(self, server):
        traces = _get("/api/traces")
        assert traces == []

    def test_api_config(self, server):
        cfg = _get("/api/config")
        assert len(cfg["agents"]) == 2
        assert len(cfg["goals"]) == 2

    def test_api_goal_metrics(self, server):
        metrics = _get("/api/goals/metrics")
        assert "cron_reliability" in metrics
        assert len(metrics["cron_reliability"]) == 2  # 2 dates

    def test_static_index(self, server):
        resp = _get_raw("/")
        html = resp.read().decode()
        assert "OA Dashboard" in html
        assert resp.headers.get("Content-Type") == "text/html"

    def test_404_unknown_path(self, server):
        try:
            _get("/api/nonexistent")
            assert False, "Should have raised"
        except urllib.error.HTTPError as e:
            assert e.code == 404
