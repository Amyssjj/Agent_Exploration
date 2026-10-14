"""Tests for OpenClaw scanner."""
import json
import tempfile
from pathlib import Path

from oa.core.scanner import OpenClawScanner


class TestScanner:
    def test_scan_missing_directory(self):
        scanner = OpenClawScanner(openclaw_home=Path("/tmp/nonexistent-oa-test"))
        result = scanner.scan()
        assert result.found is False
        assert len(result.agents) == 0
        assert len(result.cron_jobs) == 0

    def test_scan_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = OpenClawScanner(openclaw_home=Path(tmpdir))
            result = scanner.scan()
            assert result.found is True
            assert len(result.agents) == 0
            assert len(result.cron_jobs) == 0

    def test_scan_cron_jobs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            oc_home = Path(tmpdir)
            cron_dir = oc_home / "cron"
            cron_dir.mkdir()

            jobs = {
                "jobs": [
                    {
                        "id": "daily-collect",
                        "name": "Daily Collection",
                        "schedule": {"kind": "cron", "expr": "0 7 * * *"},
                        "enabled": True,
                    },
                    {
                        "id": "disabled-job",
                        "name": "Disabled",
                        "schedule": {"kind": "cron", "expr": "0 12 * * *"},
                        "enabled": False,
                    },
                ]
            }
            (cron_dir / "jobs.json").write_text(json.dumps(jobs))

            scanner = OpenClawScanner(openclaw_home=oc_home)
            result = scanner.scan()

            assert len(result.cron_jobs) == 2
            assert result.cron_jobs[0].name == "Daily Collection"
            assert result.cron_jobs[0].enabled is True
            assert result.cron_jobs[1].enabled is False

    def test_scan_agents_from_agents_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            oc_home = Path(tmpdir)
            agents_dir = oc_home / "agents"
            (agents_dir / "researcher").mkdir(parents=True)
            (agents_dir / "writer").mkdir(parents=True)

            scanner = OpenClawScanner(openclaw_home=oc_home)
            result = scanner.scan()

            agent_ids = [a.id for a in result.agents]
            assert "researcher" in agent_ids
            assert "writer" in agent_ids

    def test_scan_sessions_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            oc_home = Path(tmpdir)
            sessions_dir = oc_home / "sessions"
            sessions_dir.mkdir()

            # Create some fake session files
            for i in range(5):
                (sessions_dir / f"session-{i}.json").write_text("{}")

            scanner = OpenClawScanner(openclaw_home=oc_home)
            result = scanner.scan()
            assert result.session_count == 5

    def test_scan_sessions_count_from_agent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            oc_home = Path(tmpdir)
            main_sessions = oc_home / "agents" / "main" / "sessions"
            researcher_sessions = oc_home / "agents" / "researcher" / "sessions"
            main_sessions.mkdir(parents=True)
            researcher_sessions.mkdir(parents=True)

            (main_sessions / "session-1.jsonl").write_text("{}")
            (main_sessions / "session-2.jsonl").write_text("{}")
            (researcher_sessions / "session-3.jsonl").write_text("{}")
            (main_sessions / "sessions.json").write_text("{}")

            scanner = OpenClawScanner(openclaw_home=oc_home)
            result = scanner.scan()
            assert result.session_count == 3

    def test_scan_agents_from_cron_runs_session_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            oc_home = Path(tmpdir)
            runs_dir = oc_home / "cron" / "runs"
            runs_dir.mkdir(parents=True)
            (runs_dir / "job-1.jsonl").write_text(
                json.dumps({"ts": 1742022000000, "sessionKey": "agent:main:cron:job-1:run:abc"}) + "\n"
            )

            scanner = OpenClawScanner(openclaw_home=oc_home)
            result = scanner.scan()
            agent_ids = [a.id for a in result.agents]
            assert "main" in agent_ids

    def test_scan_agents_last_active_from_agent_session_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            oc_home = Path(tmpdir)
            sessions_dir = oc_home / "agents" / "main" / "sessions"
            sessions_dir.mkdir(parents=True)
            session_file = sessions_dir / "recent.jsonl"
            session_file.write_text("{}")

            scanner = OpenClawScanner(openclaw_home=oc_home)
            result = scanner.scan()
            main = next(a for a in result.agents if a.id == "main")
            assert main.last_active is not None

    def test_scan_agents_last_active_prefers_session_contents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            oc_home = Path(tmpdir)
            sessions_dir = oc_home / "agents" / "main" / "sessions"
            sessions_dir.mkdir(parents=True)
            session_file = sessions_dir / "recent.jsonl"
            session_file.write_text(
                json.dumps({"type": "session", "timestamp": "2026-03-15T09:00:00"}) + "\n"
                + json.dumps({"type": "message", "timestamp": "2026-03-15T10:30:00"}) + "\n",
                encoding="utf-8",
            )

            scanner = OpenClawScanner(openclaw_home=oc_home)
            result = scanner.scan()
            main = next(a for a in result.agents if a.id == "main")
            assert main.last_active == "2026-03-15T10:30:00"
