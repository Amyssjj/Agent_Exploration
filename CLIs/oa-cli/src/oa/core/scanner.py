"""OpenClaw auto-detection — scans the local installation for agents, cron jobs, and sessions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class AgentInfo:
    """Detected agent from OpenClaw installation."""
    id: str
    name: str
    last_active: str | None = None  # ISO timestamp


@dataclass
class CronJobInfo:
    """Detected cron job."""
    id: str
    name: str
    schedule: str
    enabled: bool = True


@dataclass
class ScanResult:
    """Result of scanning an OpenClaw installation."""
    openclaw_home: Path
    agents: list[AgentInfo] = field(default_factory=list)
    cron_jobs: list[CronJobInfo] = field(default_factory=list)
    session_count: int = 0
    found: bool = False


class OpenClawScanner:
    """Scans ~/.openclaw for agents, cron jobs, and sessions."""

    def __init__(self, openclaw_home: Path | None = None):
        self.home = openclaw_home or Path.home() / ".openclaw"

    def scan(self) -> ScanResult:
        """Run full scan and return results."""
        result = ScanResult(openclaw_home=self.home)

        if not self.home.exists():
            return result

        result.found = True
        result.cron_jobs = self._scan_cron_jobs()
        result.agents = self._scan_agents()
        result.session_count = self._count_sessions()

        return result

    def _scan_cron_jobs(self) -> list[CronJobInfo]:
        """Read cron job definitions from jobs.json."""
        jobs_file = self.home / "cron" / "jobs.json"
        if not jobs_file.exists():
            return []

        try:
            with open(jobs_file, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

        jobs = data.get("jobs", [])
        result = []
        for job in jobs:
            schedule = job.get("schedule", {})
            schedule_str = schedule.get("expr", schedule.get("kind", "unknown"))
            result.append(CronJobInfo(
                id=job.get("id", "unknown"),
                name=job.get("name", job.get("id", "unknown")),
                schedule=schedule_str,
                enabled=job.get("enabled", True),
            ))
        return result

    def _scan_agents(self) -> list[AgentInfo]:
        """Detect agents from session directories and config."""
        agents: dict[str, AgentInfo] = {}

        # Try reading from session directories
        # OpenClaw stores sessions as agent:<id>:* patterns
        sessions_dir = self.home / "sessions"
        if sessions_dir.exists():
            for path in sessions_dir.iterdir():
                if path.is_file() and path.suffix == ".json":
                    try:
                        name = path.stem
                        # Extract agent ID from session key pattern: agent:<id>:...
                        if "agent:" in name:
                            parts = name.split(":")
                            if len(parts) >= 2:
                                agent_id = parts[1]
                                if agent_id not in agents:
                                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                                    agents[agent_id] = AgentInfo(
                                        id=agent_id,
                                        name=agent_id.upper(),
                                        last_active=mtime.isoformat(),
                                    )
                                else:
                                    # Update last_active if more recent
                                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                                    existing = agents[agent_id]
                                    if existing.last_active and mtime.isoformat() > existing.last_active:
                                        existing.last_active = mtime.isoformat()
                    except (OSError, ValueError):
                        continue

        # Also try agent config directory
        agents_dir = self.home / "agents"
        if agents_dir.exists():
            for path in agents_dir.iterdir():
                if path.is_dir():
                    agent_id = path.name
                    if agent_id not in agents:
                        agents[agent_id] = AgentInfo(
                            id=agent_id,
                            name=agent_id.upper(),
                        )

        return sorted(agents.values(), key=lambda a: a.id)

    def _count_sessions(self) -> int:
        """Count total session files."""
        sessions_dir = self.home / "sessions"
        if not sessions_dir.exists():
            return 0
        return sum(1 for f in sessions_dir.iterdir() if f.is_file())
