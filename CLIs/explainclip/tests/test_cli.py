"""Tests for the explainclip CLI commands."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from explainclip.cli import main


@pytest.fixture
def runner():
    return CliRunner()


# ── Version ──

class TestVersion:
    def test_version_flag(self, runner: CliRunner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "explainclip" in result.output
        assert "0.1.0" in result.output


# ── Help ──

class TestHelp:
    def test_help_flag(self, runner: CliRunner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "ExplainClip" in result.output
        assert "render" in result.output
        assert "init" in result.output
        assert "themes" in result.output

    def test_render_help(self, runner: CliRunner):
        result = runner.invoke(main, ["render", "--help"])
        assert result.exit_code == 0
        assert "--quality" in result.output
        assert "--output" in result.output

    def test_init_help(self, runner: CliRunner):
        result = runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "--theme" in result.output


# ── Init ──

class TestInit:
    def test_init_creates_project(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init", "my-project"])
            assert result.exit_code == 0
            assert "Created project" in result.output

            p = Path("my-project")
            assert p.is_dir()
            assert (p / "scenes").is_dir()
            assert (p / "media").is_dir()
            assert (p / "assets").is_dir()
            assert (p / "scenes" / "intro.py").is_file()
            assert (p / "explainclip.yaml").is_file()
            assert (p / "theme.yaml").is_file()

    def test_init_with_theme(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init", "ocean-proj", "--theme", "ocean"])
            assert result.exit_code == 0
            config = (Path("ocean-proj") / "explainclip.yaml").read_text()
            assert "theme: ocean" in config

    def test_init_existing_dir_fails(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("existing").mkdir()
            result = runner.invoke(main, ["init", "existing"])
            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_init_scene_has_valid_python(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(main, ["init", "test-proj"])
            scene = (Path("test-proj") / "scenes" / "intro.py").read_text()
            # Check it contains expected imports and class
            assert "from manim import" in scene
            assert "from explainclip.design import Design" in scene
            assert "class Intro(Scene):" in scene
            assert "d.make_header" in scene

    def test_init_config_has_quality(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(main, ["init", "qtest"])
            config = (Path("qtest") / "explainclip.yaml").read_text()
            assert "quality: high" in config


# ── Themes ──

class TestThemes:
    def test_list_themes(self, runner: CliRunner):
        result = runner.invoke(main, ["themes"])
        assert result.exit_code == 0
        assert "default" in result.output
        assert "ocean" in result.output
        assert "warm" in result.output

    def test_themes_show_font_info(self, runner: CliRunner):
        result = runner.invoke(main, ["themes"])
        assert "Optima" in result.output
        assert "PingFang SC" in result.output


# ── Validate ──

class TestValidate:
    def test_validate_stub(self, runner: CliRunner):
        result = runner.invoke(main, ["validate"])
        assert result.exit_code == 0
        assert "Coming in v0.2" in result.output


# ── Render ──

class TestRender:
    def test_render_calls_manim(self, runner: CliRunner):
        with patch("explainclip.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = runner.invoke(main, ["render", "scene.py", "MyScene"])
            assert result.exit_code == 0
            assert "Rendering" in result.output
            assert "Render complete" in result.output
            # Check the subprocess call
            args = mock_run.call_args[0][0]
            assert "-m" in args
            assert "manim" in args
            assert "-qh" in args  # default quality = high
            assert "scene.py" in args
            assert "MyScene" in args

    def test_render_low_quality(self, runner: CliRunner):
        with patch("explainclip.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = runner.invoke(main, ["render", "s.py", "S", "-q", "low"])
            args = mock_run.call_args[0][0]
            assert "-ql" in args

    def test_render_4k_quality(self, runner: CliRunner):
        with patch("explainclip.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = runner.invoke(main, ["render", "s.py", "S", "-q", "4k"])
            args = mock_run.call_args[0][0]
            assert "-qk" in args

    def test_render_with_output(self, runner: CliRunner):
        with patch("explainclip.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = runner.invoke(main, ["render", "s.py", "S", "-o", "out.mp4"])
            args = mock_run.call_args[0][0]
            assert "-o" in args
            assert "out.mp4" in args

    def test_render_failure_exits(self, runner: CliRunner):
        with patch("explainclip.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = runner.invoke(main, ["render", "s.py", "S"])
            assert result.exit_code == 1
            assert "Render failed" in result.output


# ── Preview ──

class TestPreview:
    def test_preview_calls_manim(self, runner: CliRunner):
        with patch("explainclip.cli.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = runner.invoke(main, ["preview", "scene.py", "MyScene"])
            assert result.exit_code == 0
            assert "Previewing" in result.output
            args = mock_run.call_args[0][0]
            assert "-ql" in args
            assert "--preview" in args


# ── Build ──

class TestBuild:
    def test_build_no_media_dir(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["build", "Scene1", "Scene2"])
            assert result.exit_code == 1
            assert "No rendered media found" in result.output

    def test_build_no_matching_scenes(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("media/videos").mkdir(parents=True)
            result = runner.invoke(main, ["build", "NonExistent"])
            assert result.exit_code == 1
            assert "No scene files found" in result.output

    def test_build_finds_and_concats(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create fake rendered files
            vdir = Path("media/videos/scene/480p15")
            vdir.mkdir(parents=True)
            (vdir / "Intro.mp4").write_bytes(b"fake")
            (vdir / "Scene2.mp4").write_bytes(b"fake")

            with patch("explainclip.cli.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stderr = b""
                result = runner.invoke(main, ["build", "Intro", "Scene2"])
                assert result.exit_code == 0
                assert "Building 2 scenes" in result.output
                # Check ffmpeg was called
                args = mock_run.call_args[0][0]
                assert "ffmpeg" in args
                assert "-f" in args
                assert "concat" in args

    def test_build_custom_output(self, runner: CliRunner, tmp_path: Path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            vdir = Path("media/videos/scene/480p15")
            vdir.mkdir(parents=True)
            (vdir / "Intro.mp4").write_bytes(b"fake")

            with patch("explainclip.cli.subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stderr = b""
                result = runner.invoke(main, ["build", "Intro", "-o", "custom.mp4"])
                args = mock_run.call_args[0][0]
                assert "custom.mp4" in args
