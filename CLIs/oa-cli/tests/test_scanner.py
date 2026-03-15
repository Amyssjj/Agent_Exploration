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
