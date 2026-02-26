"""Tests for the theme system (base dataclasses + loader)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from explainclip.themes.base import ColorPalette, FontStack, SizeScale, Theme
from explainclip.themes.loader import get_theme, load_theme_file


# ── ColorPalette ──

class TestColorPalette:
    def test_defaults(self):
        c = ColorPalette()
        assert c.bg == "#080810"
        assert c.brand == "#b794f6"
        assert c.text_primary == "#ffffff"

    def test_override(self):
        c = ColorPalette(brand="#ff0000", bg="#000000")
        assert c.brand == "#ff0000"
        assert c.bg == "#000000"
        # rest stays default
        assert c.surface == "#12122a"


# ── FontStack ──

class TestFontStack:
    def test_defaults(self):
        f = FontStack()
        assert f.cn == "PingFang SC"
        assert f.en == "Optima"
        assert f.mono == "Menlo"
        assert f.mixed == "Hiragino Sans GB"

    def test_fallbacks_are_lists(self):
        f = FontStack()
        assert isinstance(f.cn_fallback, list)
        assert len(f.cn_fallback) >= 1


# ── SizeScale ──

class TestSizeScale:
    def test_defaults(self):
        s = SizeScale()
        assert s.title_lg == 48
        assert s.body_lg == 22
        assert s.caption == 12

    def test_override(self):
        s = SizeScale(title_lg=64, body_sm=10)
        assert s.title_lg == 64
        assert s.body_sm == 10


# ── Theme ──

class TestTheme:
    def test_defaults(self):
        t = Theme()
        assert t.name == "default"
        assert isinstance(t.colors, ColorPalette)
        assert isinstance(t.fonts, FontStack)
        assert isinstance(t.sizes, SizeScale)
        assert t.safe_margin == 0.3
        assert t.card_radius == 0.16

    def test_timing_defaults(self):
        t = Theme()
        assert t.timing_instant == 0.15
        assert t.timing_fast == 0.25
        assert t.timing_normal == 0.4
        assert t.timing_slow == 0.6


# ── get_theme ──

class TestGetTheme:
    def test_default_theme(self):
        t = get_theme("default")
        assert t.name == "default"
        assert t.colors.brand == "#b794f6"

    def test_ocean_theme(self):
        t = get_theme("ocean")
        assert t.name == "ocean"
        assert t.colors.brand == "#60a5fa"
        assert t.colors.bg == "#0a0f1a"

    def test_warm_theme(self):
        t = get_theme("warm")
        assert t.name == "warm"
        assert t.colors.brand == "#f59e0b"
        assert t.colors.bg == "#0f0a05"

    def test_unknown_theme_raises(self):
        with pytest.raises(ValueError, match="Unknown theme 'nonexistent'"):
            get_theme("nonexistent")

    def test_all_themes_have_correct_names(self):
        for name in ("default", "ocean", "warm"):
            t = get_theme(name)
            assert t.name == name


# ── load_theme_file ──

class TestLoadThemeFile:
    def test_load_minimal_yaml(self, tmp_path: Path):
        theme_file = tmp_path / "test.yaml"
        theme_file.write_text(textwrap.dedent("""\
            name: custom
            colors:
              brand: "#ff6600"
        """))
        t = load_theme_file(str(theme_file))
        assert t.name == "custom"
        assert t.colors.brand == "#ff6600"
        # Unspecified fields stay default
        assert t.colors.bg == "#080810"

    def test_load_fonts_override(self, tmp_path: Path):
        theme_file = tmp_path / "fonts.yaml"
        theme_file.write_text(textwrap.dedent("""\
            name: font-test
            fonts:
              en: "Inter"
              mono: "JetBrains Mono"
        """))
        t = load_theme_file(theme_file)
        assert t.fonts.en == "Inter"
        assert t.fonts.mono == "JetBrains Mono"
        # Default CN font preserved
        assert t.fonts.cn == "PingFang SC"

    def test_load_sizes_override(self, tmp_path: Path):
        theme_file = tmp_path / "sizes.yaml"
        theme_file.write_text(textwrap.dedent("""\
            name: size-test
            sizes:
              title_lg: 64
              body_lg: 28
        """))
        t = load_theme_file(theme_file)
        assert t.sizes.title_lg == 64
        assert t.sizes.body_lg == 28
        assert t.sizes.caption == 12  # default

    def test_load_top_level_overrides(self, tmp_path: Path):
        theme_file = tmp_path / "layout.yaml"
        theme_file.write_text(textwrap.dedent("""\
            name: layout-test
            card_radius: 0.25
            safe_margin: 0.5
            timing_fast: 0.3
        """))
        t = load_theme_file(theme_file)
        assert t.card_radius == 0.25
        assert t.safe_margin == 0.5
        assert t.timing_fast == 0.3

    def test_empty_yaml(self, tmp_path: Path):
        theme_file = tmp_path / "empty.yaml"
        theme_file.write_text("")
        t = load_theme_file(theme_file)
        # Should use all defaults
        assert t.name == "empty"
        assert t.colors.brand == "#b794f6"

    def test_ignores_unknown_color_keys(self, tmp_path: Path):
        theme_file = tmp_path / "unknown.yaml"
        theme_file.write_text(textwrap.dedent("""\
            colors:
              brand: "#aaa"
              nonexistent_color: "#bbb"
        """))
        t = load_theme_file(theme_file)
        assert t.colors.brand == "#aaa"
        assert not hasattr(t.colors, "nonexistent_color")

    def test_name_defaults_to_stem(self, tmp_path: Path):
        theme_file = tmp_path / "my-brand.yaml"
        theme_file.write_text("colors:\n  brand: '#123456'")
        t = load_theme_file(theme_file)
        assert t.name == "my-brand"
