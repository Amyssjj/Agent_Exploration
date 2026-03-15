"""G2: Team Health Pipeline — tracks daily agent activity and memory discipline."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .base import Metric, Pipeline

if TYPE_CHECKING:
    from oa.core.config import ProjectConfig


class TeamHealthPipeline(Pipeline):
    """Built-in pipeline: scans OpenClaw sessions and memory files for agent activity."""

    goal_id = "team_health"

    def collect(self, date: str, config: "ProjectConfig") -> list[Metric]:
        from oa.core.tracing import Tracer

        tracer = Tracer(service="g2_team_health", db_path=config.db_path)

        with tracer.span("G2: Team Health", {"goal": "G2", "date": date}) as root:

            active_agents = 0
            memory_logged = 0
            total_agents = len(config.agents)

            # Step 1: Check each agent's activity
            with tracer.span("Scan Agent Activity") as scan:
                for agent in config.agents:
                    sessions = self._count_agent_sessions(
                        config.openclaw_home, agent.id, date
                    )
                    has_memory = self._check_memory_logged(
                        config.openclaw_home, agent.id, date
                    )

                    if sessions > 0:
                        active_agents += 1
                    if has_memory:
                        memory_logged += 1

                    # Write to daily_agent_activity
                    self._write_activity(
                        config.db_path, date, agent.id,
                        sessions, has_memory,
                    )

                scan.set_attribute("active_agents", active_agents)
                scan.set_attribute("memory_logged", memory_logged)
                scan.set_attribute("total_agents", total_agents)

            # Step 2: Compute metrics
            with tracer.span("Compute Metrics"):
                discipline = (
                    round(memory_logged / total_agents * 100, 1)
                    if total_agents > 0 else 0
                )

            root.set_attribute("active_agent_count", active_agents)
            root.set_attribute("memory_discipline", discipline)

        tracer.flush()
        return [
            Metric("active_agent_count", active_agents, unit="count", breakdown={
                "total_agents": total_agents,
                "active": active_agents,
            }),
            Metric("memory_discipline", discipline, unit="%", breakdown={
                "logged": memory_logged,
                "total": total_agents,
            }),
        ]

    def _count_agent_sessions(self, openclaw_home: Path, agent_id: str,
                              date: str) -> int:
        """Count sessions for an agent on a given date."""
        sessions_dir = openclaw_home / "sessions"
        if not sessions_dir.exists():
            return 0

        count = 0
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

        for path in sessions_dir.iterdir():
            if not path.is_file():
                continue
            # Match agent ID in session filename (pattern: agent:<id>:...)
            if f"agent:{agent_id}:" not in path.name:
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime).date()
                if mtime == target_date:
                    count += 1
            except OSError:
                continue

        return count

    def _check_memory_logged(self, openclaw_home: Path, agent_id: str,
                             date: str) -> bool:
        """Check if an agent has a memory file for the given date."""
        # Check common memory file patterns
        # Pattern 1: Agent workspace memory/YYYY-MM-DD.md
        # We check under the openclaw home and common workspace patterns
        possible_paths = [
            openclaw_home / "agents" / agent_id / "memory" / f"{date}.md",
            openclaw_home / "workspaces" / agent_id / "memory" / f"{date}.md",
        ]

        for path in possible_paths:
            if path.exists():
                return True

        return False

    def _write_activity(self, db_path: Path, date: str, agent_id: str,
                        session_count: int, memory_logged: bool) -> None:
        """Write agent activity to daily_agent_activity table."""
        db = sqlite3.connect(str(db_path))
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(
            """INSERT INTO daily_agent_activity
               (date, agent_id, session_count, memory_logged, created_at)
               VALUES (?, ?, ?, ?, datetime('now'))
               ON CONFLICT(date, agent_id) DO UPDATE SET
                   session_count = excluded.session_count,
                   memory_logged = excluded.memory_logged""",
            (date, agent_id, session_count, 1 if memory_logged else 0),
        )
        db.commit()
        db.close()
