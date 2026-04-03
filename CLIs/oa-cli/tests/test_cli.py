"""Tests for CLI commands."""
import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from oa.cli import main
from oa.core.config import GoalConfig, MetricConfig, ProjectConfig
from oa.core.schema import create_schema


class TestCLI:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        from oa import __version__
        assert __version__ in result.output

    def test_doctor(self):
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "Python" in result.output
        assert "SQLite" in result.output

    def test_init_creates_project(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                result = runner.invoke(main, ["init", "my-test-project", "--yes"])
                assert result.exit_code == 0

                project = Path("my-test-project")
                assert project.exists()
                assert (project / "config.yaml").exists()
                assert (project / "data" / "monitor.db").exists()
                assert (project / "pipelines").exists()

    def test_init_duplicate_errors(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                runner.invoke(main, ["init", "dupe-test", "--yes"])
                result = runner.invoke(main, ["init", "dupe-test", "--yes"])
                assert result.exit_code == 1
                assert "already exists" in result.output

    def test_collect_no_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                result = runner.invoke(main, ["collect"])
                assert result.exit_code == 1
                assert "config.yaml not found" in result.output

    def test_status_no_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                result = runner.invoke(main, ["status"])
                assert result.exit_code == 1

    def test_cron_show(self):
        runner = CliRunner()
        result = runner.invoke(main, ["cron", "show"])
        assert result.exit_code == 0
        assert "oa-collect" in result.output
        assert "7,12,19" in result.output

    def test_serve_no_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                result = runner.invoke(main, ["serve"])
                assert result.exit_code == 1
                assert "config.yaml not found" in result.output

    def test_collect_custom_pipeline(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                Path("data").mkdir()
                Path("pipelines").mkdir()
                create_schema("data/monitor.db")
                Path("pipelines/custom_goal.py").write_text(
                    "from oa import Pipeline, Metric\n\nclass CustomGoal(Pipeline):\n    goal_id='custom_goal'\n    def collect(self, date, config):\n        return [Metric('score', 42, unit='count')]\n",
                    encoding="utf-8",
                )
                Path("config.yaml").write_text(
                    "openclaw_home: ~/.openclaw\nworkspace_root: ~/.openclaw/workspace\nmemory_paths:\n  - memory/{date}.md\ndb_path: data/monitor.db\nagents:\n  - id: main\n    name: Main\ngoals:\n  - id: custom_goal\n    name: Custom Goal\n    builtin: false\n    pipeline: pipelines/custom_goal.py\n    metrics:\n      - name: score\n        unit: count\n        healthy: 10\n        warning: 5\n",
                    encoding="utf-8",
                )
                result = runner.invoke(main, ["collect"])
                assert result.exit_code == 0
                assert "score: 42 count" in result.output

    def test_full_workflow(self):
        """Integration test: init → collect → status."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                # Init
                result = runner.invoke(main, ["init", "workflow-test", "--yes"])
                assert result.exit_code == 0

                # Collect
                result = runner.invoke(main, ["collect", "--config", "workflow-test/config.yaml"])
                assert result.exit_code == 0
                assert "success_rate" in result.output

                # Status
                result = runner.invoke(main, ["status", "--config", "workflow-test/config.yaml"])
                assert result.exit_code == 0

    def test_collect_reports_detailed_cron_failures(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                openclaw_home = Path("openclaw")
                runs_dir = openclaw_home / "cron" / "runs"
                runs_dir.mkdir(parents=True)
                Path("data").mkdir()
                create_schema("data/monitor.db")

                config = ProjectConfig(openclaw_home=openclaw_home, workspace_root=openclaw_home / "workspace", db_path=Path("data/monitor.db"))
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
                    )
                ]
                config.save("config.yaml")

                (runs_dir / "job-1.jsonl").write_text(
                    json.dumps({
                        "ts": 1742022000000,
                        "jobId": "job-1",
                        "action": "finished",
                        "status": "ok",
                        "runAtMs": 1742022000000,
                        "deliveryStatus": "not-delivered",
                    }) + "\n"
                    + json.dumps({
                        "ts": 1742025600000,
                        "jobId": "job-1",
                        "action": "finished",
                        "status": "error",
                        "error": {"message": "cron: job execution timed out"},
                        "runAtMs": 1742025600000,
                    }) + "\n",
                    encoding="utf-8",
                )

                result = runner.invoke(main, ["collect", "--date", "2025-03-15"])
                assert result.exit_code == 0
                assert "observed 2 runs -> 1 success, 1 timeout" in result.output
