"""
OA Dashboard Server — Pure Python HTTP server.

Serves:
- API endpoints (JSON) reading from SQLite
- Pre-built dashboard (static HTML/JS/CSS files)

Usage:
    from oa.server import serve
    serve(port=3460, config_path="config.yaml")
"""
from __future__ import annotations

import json
import sqlite3
import webbrowser
from datetime import datetime
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml


DASHBOARD_DIR = Path(__file__).parent / "dashboard"


class OAHandler(SimpleHTTPRequestHandler):
    """HTTP handler for OA dashboard — API routes + static files."""

    config_path: str = "config.yaml"
    _config_cache: dict | None = None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # API routes
        api_routes: dict[str, Any] = {
            "/api/goals": self._api_goals,
            "/api/goals/metrics": self._api_goal_metrics,
            "/api/cron-chart": self._api_cron_chart,
            "/api/team-health": self._api_team_health,
            "/api/traces": self._api_traces,
            "/api/health": self._api_health_summary,
            "/api/config": self._api_config,
        }

        if path in api_routes:
            try:
                data = api_routes[path](params)
                self._json_response(200, data)
            except Exception as e:
                self._json_response(500, {"error": str(e)})
            return

        # Static file serving from dashboard directory
        if path == "" or path == "/":
            path = "/index.html"

        file_path = DASHBOARD_DIR / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            self._serve_file(file_path)
        else:
            self._json_response(404, {"error": "not found"})

    def _json_response(self, status: int, data: Any) -> None:
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path) -> None:
        content_types = {
            ".html": "text/html",
            ".js": "application/javascript",
            ".css": "text/css",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".json": "application/json",
        }
        ct = content_types.get(file_path.suffix, "application/octet-stream")
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_config(self) -> dict:
        if OAHandler._config_cache is not None:
            return OAHandler._config_cache
        config_path = Path(OAHandler.config_path)
        if config_path.exists():
            with open(config_path) as f:
                OAHandler._config_cache = yaml.safe_load(f) or {}
        else:
            OAHandler._config_cache = {}
        return OAHandler._config_cache

    def _get_db(self) -> sqlite3.Connection:
        config = self._get_config()
        db_path = config.get("db_path", "data/monitor.db")
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        return db

    # ━━━ API Endpoints ━━━

    def _api_config(self, params: dict) -> dict:
        """Return project config (goals, agents)."""
        config = self._get_config()
        return {
            "agents": config.get("agents", []),
            "goals": config.get("goals", []),
        }

    def _api_goals(self, params: dict) -> list:
        """Return all goals with latest metrics and health status."""
        config = self._get_config()
        db = self._get_db()
        goals = []

        for goal_cfg in config.get("goals", []):
            goal_id = goal_cfg["id"]
            metrics_cfg = goal_cfg.get("metrics", [])

            goal_data: dict[str, Any] = {
                "id": goal_id,
                "name": goal_cfg.get("name", goal_id),
                "builtin": goal_cfg.get("builtin", False),
                "metrics": {},
                "sparkline": [],
                "healthStatus": "unknown",
            }

            primary_metric = metrics_cfg[0]["name"] if metrics_cfg else None

            for m_cfg in metrics_cfg:
                # Latest value
                row = db.execute(
                    "SELECT value, date FROM goal_metrics WHERE goal=? AND metric=? ORDER BY date DESC LIMIT 1",
                    (goal_id, m_cfg["name"]),
                ).fetchone()

                # Previous value for trend
                prev = db.execute(
                    "SELECT value FROM goal_metrics WHERE goal=? AND metric=? ORDER BY date DESC LIMIT 1 OFFSET 1",
                    (goal_id, m_cfg["name"]),
                ).fetchone()

                value = row["value"] if row else None
                trend = round(value - prev["value"], 1) if (row and prev) else None

                goal_data["metrics"][m_cfg["name"]] = {
                    "value": value,
                    "unit": m_cfg.get("unit", ""),
                    "healthy": m_cfg.get("healthy", 0),
                    "warning": m_cfg.get("warning", 0),
                    "trend": trend,
                    "date": row["date"] if row else None,
                    "status": _health_status(value, m_cfg.get("healthy", 0), m_cfg.get("warning", 0)),
                }

                if m_cfg["name"] == primary_metric:
                    goal_data["healthStatus"] = _health_status(
                        value, m_cfg.get("healthy", 0), m_cfg.get("warning", 0)
                    )

            # Sparkline: last 30 days of primary metric
            if primary_metric:
                rows = db.execute(
                    "SELECT date, value FROM goal_metrics WHERE goal=? AND metric=? ORDER BY date ASC",
                    (goal_id, primary_metric),
                ).fetchall()
                goal_data["sparkline"] = [{"date": r["date"], "value": r["value"]} for r in rows]

            goals.append(goal_data)

        db.close()
        return goals

    def _api_goal_metrics(self, params: dict) -> dict:
        """Return time-series metrics for all goals."""
        db = self._get_db()
        days = int(params.get("days", [30])[0])

        rows = db.execute(
            "SELECT goal, date, metric, value, unit, breakdown FROM goal_metrics "
            "WHERE date >= date('now', ?) ORDER BY goal, date ASC",
            (f"-{days} days",),
        ).fetchall()

        grouped: dict[str, list] = {}
        for r in rows:
            goal = r["goal"]
            if goal not in grouped:
                grouped[goal] = []
            breakdown = json.loads(r["breakdown"]) if r["breakdown"] else None
            grouped[goal].append({
                "date": r["date"], "metric": r["metric"],
                "value": r["value"], "unit": r["unit"],
                "breakdown": breakdown,
            })

        db.close()
        return grouped

    def _api_cron_chart(self, params: dict) -> list:
        """Return cron run data for charts."""
        db = self._get_db()
        days = int(params.get("days", [30])[0])

        rows = db.execute(
            "SELECT date, cron_name, status, job_id FROM cron_runs "
            "WHERE date >= date('now', ?) ORDER BY date ASC",
            (f"-{days} days",),
        ).fetchall()

        result = [dict(r) for r in rows]
        db.close()
        return result

    def _api_team_health(self, params: dict) -> list:
        """Return daily agent activity data."""
        db = self._get_db()
        days = int(params.get("days", [30])[0])

        rows = db.execute(
            "SELECT date, agent_id, session_count, memory_logged, last_active "
            "FROM daily_agent_activity WHERE date >= date('now', ?) ORDER BY date ASC",
            (f"-{days} days",),
        ).fetchall()

        result = [dict(r) for r in rows]
        db.close()
        return result

    def _api_traces(self, params: dict) -> list:
        """Return recent execution traces."""
        db = self._get_db()
        limit = int(params.get("limit", [50])[0])

        rows = db.execute(
            "SELECT span_id, trace_id, parent_span_id, name, service, status, "
            "start_time, end_time, duration_ms, attributes "
            "FROM spans ORDER BY start_time DESC LIMIT ?",
            (limit,),
        ).fetchall()

        result = []
        for r in rows:
            d = dict(r)
            if d["attributes"]:
                d["attributes"] = json.loads(d["attributes"])
            result.append(d)

        db.close()
        return result

    def _api_health_summary(self, params: dict) -> dict:
        """Return overall system health summary."""
        goals = self._api_goals(params)
        statuses = [g["healthStatus"] for g in goals]

        if "critical" in statuses:
            overall = "critical"
        elif "warning" in statuses:
            overall = "warning"
        elif all(s == "healthy" for s in statuses):
            overall = "healthy"
        else:
            overall = "unknown"

        return {
            "overall": overall,
            "goals": len(goals),
            "healthy": statuses.count("healthy"),
            "warning": statuses.count("warning"),
            "critical": statuses.count("critical"),
            "lastCollected": _get_last_collected(self._get_db()),
        }

    def log_message(self, format, *args):
        """Suppress default request logging for cleaner output."""
        pass


def _health_status(value: float | None, healthy: float, warning: float) -> str:
    if value is None:
        return "unknown"
    if value >= healthy:
        return "healthy"
    if value >= warning:
        return "warning"
    return "critical"


def _get_last_collected(db: sqlite3.Connection) -> str | None:
    row = db.execute("SELECT MAX(date) as d FROM goal_metrics").fetchone()
    db.close()
    return row["d"] if row else None


def serve(port: int = 3460, config_path: str = "config.yaml", open_browser: bool = True) -> None:
    """Start the OA dashboard server."""
    OAHandler.config_path = config_path
    OAHandler._config_cache = None  # reset cache

    if not DASHBOARD_DIR.exists() or not (DASHBOARD_DIR / "index.html").exists():
        print("Error: Dashboard files not found. Package may be incomplete.")
        return

    try:
        server = HTTPServer(("127.0.0.1", port), OAHandler)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Error: Port {port} is already in use.")
            print(f"  Try: oa serve --port {port + 1}")
            print(f"  Or:  lsof -i :{port} | grep LISTEN  (to find the process)")
            return
        raise
    url = f"http://localhost:{port}"

    print(f"\n🖥️  OA Dashboard running at {url}\n")

    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file) as f:
            cfg = yaml.safe_load(f) or {}
        goals = cfg.get("goals", [])
        agents = cfg.get("agents", [])
        print(f"  Goals:     {len(goals)} tracked")
        print(f"  Agents:    {len(agents)} configured")
    print(f"\n  Press Ctrl+C to stop\n")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.shutdown()
