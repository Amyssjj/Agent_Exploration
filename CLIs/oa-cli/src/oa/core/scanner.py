"""OpenClaw auto-detection — scans the local installation for agents, cron jobs, and sessions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .session_data import inspect_session_file


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
            schedule_str = schedule.get("expr") or schedule.get("kind", "unknown")
            result.append(
                CronJobInfo(
                    id=job.get("id", "unknown"),
                    name=job.get("name", job.get("id", "unknown")),
                    schedule=schedule_str,
                    enabled=job.get("enabled", True),
                )
            )
        return result

    def _scan_agents(self) -> list[AgentInfo]:
        """Detect agents from agent dirs, sessions, and cron run logs."""
        agents: dict[str, AgentInfo] = {}

        agents_dir = self.home / "agents"
        if agents_dir.exists():
            for path in agents_dir.iterdir():
                if path.is_dir():
                    self._register_agent(agents, path.name)

        for path in self._iter_legacy_session_files():
            agent_id = self._extract_agent_id(path.stem)
            if agent_id:
                self._register_agent(
                    agents,
                    agent_id,
                    inspect_session_file(path).last_active,
                )

        for agent_id, path in self._iter_agent_session_files():
            self._register_agent(
                agents,
                agent_id,
                inspect_session_file(path).last_active,
            )

        runs_dir = self.home / "cron" / "runs"
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
                            agent_id = self._extract_agent_id(entry.get("sessionKey", ""))
                            if not agent_id:
                                continue
                            ts = self._entry_timestamp_iso(entry) or datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                            self._register_agent(agents, agent_id, ts)
                except OSError:
                    continue

        return sorted(agents.values(), key=lambda a: a.id)

    def _count_sessions(self) -> int:
        """Count total session files across legacy and current layouts."""
        count = sum(1 for _ in self._iter_legacy_session_files())
        count += sum(1 for _agent_id, _path in self._iter_agent_session_files())
        return count

    def _iter_legacy_session_files(self):
        sessions_dir = self.home / "sessions"
        if not sessions_dir.exists():
            return
        for path in sessions_dir.iterdir():
            if path.is_file():
                yield path

    def _iter_agent_session_files(self):
        agents_dir = self.home / "agents"
        if not agents_dir.exists():
            return
        for agent_dir in agents_dir.iterdir():
            sessions_dir = agent_dir / "sessions"
            if not agent_dir.is_dir() or not sessions_dir.exists():
                continue
            for path in sessions_dir.glob("*.jsonl"):
                if path.is_file():
                    yield agent_dir.name, path

    def _register_agent(self, agents: dict[str, AgentInfo], agent_id: str, last_active: str | None = None) -> None:
        if not agent_id:
            return
        if agent_id not in agents:
            agents[agent_id] = AgentInfo(id=agent_id, name=agent_id.upper(), last_active=last_active)
            return

        existing = agents[agent_id]
        if last_active and (existing.last_active is None or last_active > existing.last_active):
            existing.last_active = last_active

    def _extract_agent_id(self, text: str) -> str | None:
        if not text or "agent:" not in text:
            return None
        parts = text.split(":")
        try:
            idx = parts.index("agent")
        except ValueError:
            idx = -1
        if idx >= 0 and idx + 1 < len(parts):
            return parts[idx + 1]
        if text.startswith("agent:") and len(parts) >= 2:
            return parts[1]
        return None

    def _entry_timestamp_iso(self, entry: dict) -> str | None:
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
