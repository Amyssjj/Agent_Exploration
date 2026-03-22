"""G2: Team Health Pipeline — tracks daily execution activity and memory discipline."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .base import Metric, Pipeline

if TYPE_CHECKING:
    from oa.core.config import ProjectConfig


class TeamHealthPipeline(Pipeline):
    """Built-in pipeline: scans OpenClaw sessions / cron runs and workspace memory files."""

    goal_id = "team_health"

    def collect(self, date: str, config: "ProjectConfig") -> list[Metric]:
        from oa.core.tracing import Tracer

        tracer = Tracer(service="g2_team_health", db_path=config.db_path)

        with tracer.span("G2: Team Health", {"goal": "G2", "date": date}) as root:
            total_agents = len(config.agents)
            active_agents = 0
            memory_logged = 0

            with tracer.span("Scan Agent Activity") as scan:
                for agent in config.agents:
                    sessions = self._count_agent_sessions(config.openclaw_home, agent.id, date)
                    last_active = self._last_active_for_agent(config.openclaw_home, agent.id, date)
                    has_memory = self._check_memory_logged(config, date)

                    if sessions > 0:
                        active_agents += 1
                    if has_memory:
                        memory_logged += 1

                    self._write_activity(
                        config.db_path,
                        date,
                        agent.id,
                        sessions,
                        has_memory,
                        last_active,
                    )

                scan.set_attribute("active_agents", active_agents)
                scan.set_attribute("memory_logged", memory_logged)
                scan.set_attribute("total_agents", total_agents)

            with tracer.span("Compute Metrics"):
                inactive_agents = max(total_agents - active_agents, 0)
                discipline = round(memory_logged / total_agents * 100, 1) if total_agents > 0 else 0

            root.set_attribute("active_agent_count", active_agents)
            root.set_attribute("inactive_agent_count", inactive_agents)
            root.set_attribute("memory_discipline", discipline)

        tracer.flush()
        return [
            Metric(
                "active_agent_count",
                active_agents,
                unit="count",
                breakdown={"total_agents": total_agents, "active": active_agents},
            ),
            Metric(
                "inactive_agent_count",
                inactive_agents,
                unit="count",
                breakdown={"total_agents": total_agents, "inactive": inactive_agents},
            ),
            Metric(
                "memory_discipline",
                discipline,
                unit="%",
                breakdown={"logged": memory_logged, "total": total_agents},
            ),
        ]

    def _count_agent_sessions(self, openclaw_home: Path, agent_id: str, date: str) -> int:
        count = 0
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        sessions_dir = openclaw_home / "sessions"

        if sessions_dir.exists():
            for path in sessions_dir.iterdir():
                if not path.is_file():
                    continue
                if f"agent:{agent_id}:" not in path.name:
                    continue
                try:
                    if datetime.fromtimestamp(path.stat().st_mtime).date() == target_date:
                        count += 1
                except OSError:
                    continue

        runs_dir = openclaw_home / "cron" / "runs"
        if runs_dir.exists():
            for path in runs_dir.glob("*.jsonl"):
                try:
                    with open(path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            session_key = str(entry.get("sessionKey", ""))
                            if f"agent:{agent_id}:" not in session_key:
                                continue
                            event_date = self._entry_date(entry)
                            if event_date == date:
                                count += 1
                except OSError:
                    continue

        return count

    def _last_active_for_agent(self, openclaw_home: Path, agent_id: str, date: str) -> str | None:
        timestamps: list[str] = []
        sessions_dir = openclaw_home / "sessions"
        if sessions_dir.exists():
            for path in sessions_dir.iterdir():
                if not path.is_file() or f"agent:{agent_id}:" not in path.name:
                    continue
                try:
                    ts = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                    if ts.startswith(date):
                        timestamps.append(ts)
                except OSError:
                    continue

        runs_dir = openclaw_home / "cron" / "runs"
        if runs_dir.exists():
            for path in runs_dir.glob("*.jsonl"):
                try:
                    with open(path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            session_key = str(entry.get("sessionKey", ""))
                            if f"agent:{agent_id}:" not in session_key:
                                continue
                            iso_ts = self._entry_iso(entry)
                            if iso_ts and iso_ts.startswith(date):
                                timestamps.append(iso_ts)
                except OSError:
                    continue

        return max(timestamps) if timestamps else None

    def _check_memory_logged(self, config: "ProjectConfig", date: str) -> bool:
        workspace_root = config.workspace_root
        for template in config.memory_paths:
            rel = template.format(date=date)
            path = (workspace_root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
            if not path.exists() or not path.is_file():
                continue
            try:
                if path.stat().st_size > 0:
                    return True
            except OSError:
                continue
        return False

    def _entry_date(self, entry: dict) -> str | None:
        for key in ("runAtMs", "ts"):
            value = entry.get(key)
            if isinstance(value, (int, float)):
                try:
                    return datetime.fromtimestamp(value / 1000).strftime("%Y-%m-%d")
                except (OverflowError, OSError, ValueError):
                    pass
        for key in ("startedAt", "completedAt"):
            value = entry.get(key)
            if isinstance(value, str) and len(value) >= 10:
                return value[:10]
        return None

    def _entry_iso(self, entry: dict) -> str | None:
        for key in ("runAtMs", "ts"):
            value = entry.get(key)
            if isinstance(value, (int, float)):
                try:
                    return datetime.fromtimestamp(value / 1000).isoformat()
                except (OverflowError, OSError, ValueError):
                    pass
        for key in ("startedAt", "completedAt"):
            value = entry.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    def _write_activity(
        self,
        db_path: Path,
        date: str,
        agent_id: str,
        session_count: int,
        memory_logged: bool,
        last_active: str | None,
    ) -> None:
        db = sqlite3.connect(str(db_path))
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(
            """INSERT INTO daily_agent_activity
               (date, agent_id, session_count, memory_logged, last_active, created_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(date, agent_id) DO UPDATE SET
                   session_count = excluded.session_count,
                   memory_logged = excluded.memory_logged,
                   last_active = excluded.last_active""",
            (date, agent_id, session_count, 1 if memory_logged else 0, last_active),
        )
        db.commit()
        db.close()
