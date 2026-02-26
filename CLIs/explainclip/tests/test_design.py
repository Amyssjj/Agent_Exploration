"""Tests for the Design system (theme-aware Manim components)."""
from __future__ import annotations

from pathlib import Path

import pytest

from explainclip.design import Design, _has_cjk, _has_latin
from explainclip.themes.base import Theme


# ── Language Detection Helpers ──

class TestLanguageDetection:
    def test_has_cjk_chinese(self):
        assert _has_cjk("你好世界")

    def test_has_cjk_english(self):
        assert not _has_cjk("Hello World")

    def test_has_cjk_mixed(self):
        assert _has_cjk("Hello 你好")

    def test_has_cjk_numbers_only(self):
        assert not _has_cjk("12345")

    def test_has_latin_english(self):
        assert _has_latin("Hello")

    def test_has_latin_chinese(self):
        assert not _has_latin("你好")

    def test_has_latin_mixed(self):
        assert _has_latin("你好 World")

    def test_has_latin_numbers_only(self):
        assert not _has_latin("12345")

    def test_has_cjk_empty(self):
        assert not _has_cjk("")

    def test_has_latin_empty(self):
        assert not _has_latin("")


# ── Design Init ──

class TestDesignInit:
    def test_default_theme(self):
        d = Design()
        assert d.theme.name == "default"
        assert d.colors.brand == "#b794f6"

    def test_named_theme(self):
        d = Design(theme="ocean")
        assert d.theme.name == "ocean"
        assert d.colors.brand == "#60a5fa"

    def test_theme_object(self):
        t = Theme(name="custom")
        d = Design(theme=t)
        assert d.theme.name == "custom"

    def test_yaml_theme(self, tmp_path: Path):
        f = tmp_path / "t.yaml"
        f.write_text("name: yaml-test\ncolors:\n  brand: '#abc'")
        d = Design(theme=str(f))
        assert d.colors.brand == "#abc"

    def test_shortcuts(self):
        d = Design()
        assert d.colors is d.theme.colors
        assert d.fonts is d.theme.fonts
        assert d.sizes is d.theme.sizes

    def test_frame_constants(self):
        d = Design()
        assert d.frame_w > 0
        assert d.frame_h > 0


# ── Smart Font ──

class TestSmartFont:
    def test_english_text(self):
        d = Design()
        assert d.smart_font("Hello World") == d.fonts.en

    def test_chinese_text(self):
        d = Design()
        assert d.smart_font("你好世界") == d.fonts.cn

    def test_mixed_text(self):
        d = Design()
        assert d.smart_font("Hello 你好") == d.fonts.mixed

    def test_numbers_only(self):
        d = Design()
        # No CJK and no latin letters → defaults to EN
        assert d.smart_font("12345") == d.fonts.en

    def test_empty_string(self):
        d = Design()
        assert d.smart_font("") == d.fonts.en


# ── Component Smoke Tests ──
# These tests verify components can be created without errors.
# They don't check visual output (that's done by the render test).

class TestMakeComponents:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.d = Design()

    def test_make_text_english(self):
        t = self.d.make_text("Hello")
        assert t is not None

    def test_make_text_chinese(self):
        t = self.d.make_text("你好")
        assert t is not None

    def test_make_text_custom_color(self):
        t = self.d.make_text("Test", color="#ff0000")
        assert t is not None

    def test_make_code_label(self):
        t = self.d.make_code_label("console.log('hi')")
        assert t is not None

    def test_make_header(self):
        h = self.d.make_header("Section Title")
        assert h is not None
        assert len(h) == 2  # text + underline

    def test_make_header_chinese(self):
        h = self.d.make_header("章节标题")
        assert h is not None

    def test_make_node(self):
        n = self.d.make_node("Server", self.d.colors.blue)
        assert n is not None

    def test_make_node_with_glow(self):
        n = self.d.make_node("DB", self.d.colors.green, glow=True)
        assert n is not None
        # glow version has extra element
        assert len(n) == 3

    def test_make_card(self):
        c = self.d.make_card("[T]", "Title", "Description", self.d.colors.blue)
        assert c is not None
        assert len(c) == 5  # bg, accent, icon, title, desc

    def test_make_arrow(self):
        from manim import LEFT, RIGHT
        a = self.d.make_arrow(LEFT, RIGHT)
        assert a is not None

    def test_make_insight_bar(self):
        ib = self.d.make_insight_bar("Key insight here")
        assert ib is not None
        assert len(ib) == 2  # bg + text

    def test_make_memory_box(self):
        mb = self.d.make_memory_box("Title", "subtitle.txt", "Description", self.d.colors.cyan)
        assert mb is not None

    def test_make_glass(self):
        from manim import Rectangle
        r = Rectangle(width=2, height=1)
        g = self.d.make_glass(r)
        assert g is not None
        assert len(g) == 3  # base, glow, rim

    def test_make_shadow(self):
        from manim import Rectangle
        r = Rectangle(width=2, height=1)
        s = self.d.make_shadow(r)
        assert s is not None
        assert len(s) == 5  # 5 layers by default

    def test_make_grid_bg(self):
        bg = self.d.make_grid_bg()
        assert bg is not None

    def test_make_ambient_particles(self):
        p = self.d.make_ambient_particles(count=10)
        assert p is not None
        assert len(p) == 10

    def test_make_terminal_window(self):
        tw = self.d.make_terminal_window([
            "ls -la",
            ("echo hello", "hello"),
        ])
        assert tw is not None

    def test_make_code_window(self):
        cw = self.d.make_code_window([
            "def hello():",
            "    print('hi')",
        ], title="hello.py")
        assert cw is not None


# ── Layout Helpers ──

class TestLayoutHelpers:
    def test_grid_layout(self):
        from manim import Circle
        objs = [Circle(radius=0.5) for _ in range(4)]
        grid = Design.grid_layout(objs, cols=2, spacing=0.5)
        assert grid is not None
        assert len(grid) == 2  # 2 rows

    def test_stack_layout(self):
        from manim import Circle
        objs = [Circle(radius=0.5) for _ in range(3)]
        stack = Design.stack_layout(objs, spacing=0.3)
        assert stack is not None
        assert len(stack) == 3

    def test_clamp_to_frame(self):
        from manim import Rectangle
        d = Design()
        # Create rect far to the right
        r = Rectangle(width=2, height=1).shift([100, 0, 0])
        d.clamp_to_frame(r)
        # Should have been pulled back inside frame
        assert r.get_right()[0] <= d.frame_w / 2
