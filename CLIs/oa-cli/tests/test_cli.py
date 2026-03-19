"""Tests for CLI commands."""
import tempfile
from pathlib import Path

from click.testing import CliRunner

from oa.cli import main


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
