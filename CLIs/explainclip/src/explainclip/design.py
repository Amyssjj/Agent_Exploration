"""
ExplainClip Design System — Theme-aware Manim components.

Usage:
    from explainclip.design import Design

    d = Design()                          # default theme
    d = Design(theme="ocean")             # built-in theme
    d = Design(theme="my-theme.yaml")     # custom theme file

    # All components are methods on the Design instance:
    header = d.make_header("Introduction")
    node = d.make_node("Server", d.colors.blue)
    text = d.make_text("Hello world")
"""
from __future__ import annotations

import random
from pathlib import Path

from manim import (
    BOLD,
    DOWN,
    LEFT,
    NORMAL,
    ORIGIN,
    RIGHT,
    UP,
    WHITE,
    AddTextLetterByLetter,
    AnimationGroup,
    Arrow,
    Circle,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    NumberPlane,
    Polygon,
    Rectangle,
    RoundedRectangle,
    Succession,
    Text,
    Underline,
    VGroup,
    bezier,
    config,
    interpolate_color,
    rate_functions,
    smooth,
    there_and_back,
    ManimColor,
)

from .themes import Theme, get_theme, load_theme_file


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf" for ch in text)


def _has_latin(text: str) -> bool:
    return any(ch.isascii() and ch.isalpha() for ch in text)


class Design:
    """Theme-aware design system. All Manim components are methods here."""

    def __init__(self, theme: str | Theme = "default"):
        if isinstance(theme, str):
            if theme.endswith((".yaml", ".yml")):
                self.theme = load_theme_file(theme)
            else:
                self.theme = get_theme(theme)
        else:
            self.theme = theme

        # Shortcuts
        self.colors = self.theme.colors
        self.fonts = self.theme.fonts
        self.sizes = self.theme.sizes

        # Frame constants
        self.frame_w = config.frame_width
        self.frame_h = config.frame_height
        self.safe_margin = self.theme.safe_margin

        # Easing curves
        self.ease_brand = bezier([0.25, 0.1, 0.25, 1.0])
        self.ease_bounce = bezier([0.68, -0.55, 0.265, 1.55])
        self.ease_swift = bezier([0.4, 0.0, 0.2, 1])

    # ━━━ FONT DETECTION ━━━

    def smart_font(self, text: str) -> str:
        """Auto-pick font: pure CN → cn font, pure EN → en font, mixed → mixed font."""
        has_cn = _has_cjk(text)
        has_en = _has_latin(text)
        if has_cn and has_en:
            return self.fonts.mixed
        elif has_cn:
            return self.fonts.cn
        return self.fonts.en

    # ━━━ LAYOUT ━━━

    def clamp_to_frame(self, mobject, margin: float | None = None):
        """Shift mobject to stay within frame safe zone. Call after positioning."""
        m = margin if margin is not None else self.safe_margin
        l = -self.frame_w / 2 + m
        r = self.frame_w / 2 - m
        t = self.frame_h / 2 - m
        b = -self.frame_h / 2 + m

        sx, sy = 0.0, 0.0
        if mobject.get_right()[0] > r:
            sx = r - mobject.get_right()[0]
        if mobject.get_left()[0] < l:
            sx = l - mobject.get_left()[0]
        if mobject.get_top()[1] > t:
            sy = t - mobject.get_top()[1]
        if mobject.get_bottom()[1] < b:
            sy = b - mobject.get_bottom()[1]

        if sx != 0 or sy != 0:
            mobject.shift(RIGHT * sx + UP * sy)
        return mobject

    # ━━━ TEXT ━━━

    def make_text(self, label: str, font_size: int = 20, color: str | None = None,
                  weight=NORMAL) -> Text:
        """Smart text — auto-detects language and applies correct font + kerning fix."""
        color = color or self.colors.text_primary
        font = self.smart_font(label)
        if font == self.fonts.en:
            t = Text(label, font_size=font_size * 2, font=font, color=color, weight=weight)
            t.scale(0.5)
            return t
        return Text(label, font_size=font_size, font=font, color=color, weight=weight)

    def make_code_label(self, text: str, font_size: int = 14,
                        color: str | None = None) -> Text:
        """Monospace text for code/paths."""
        color = color or self.colors.text_secondary
        return Text(text, font_size=font_size, font=self.fonts.mono, color=color)

    # ━━━ COMPONENTS ━━━

    def make_header(self, text_str: str, font_size: int | None = None) -> VGroup:
        """Section header with underline accent."""
        font_size = font_size or self.sizes.title_lg
        font = self.smart_font(text_str)
        if font == self.fonts.en:
            header = Text(text_str, font_size=font_size * 2, font=font,
                          weight=BOLD, color=self.colors.brand)
            header.scale(0.5)
        else:
            header = Text(text_str, font_size=font_size, font=font,
                          weight=BOLD, color=self.colors.brand)
        underline = Underline(header, color=self.colors.brand, stroke_width=2, buff=0.12)
        group = VGroup(header, underline)
        group.to_edge(UP, buff=0.4)
        return group

    def make_node(self, label: str, color: str, w: float = 2.5, h: float = 0.85,
                  font_size: int = 20, glow: bool = False) -> VGroup:
        """Node box for architecture diagrams."""
        bg = RoundedRectangle(
            corner_radius=0.12, width=w, height=h,
            fill_color=color, fill_opacity=0.12,
            stroke_color=color, stroke_width=1.5,
        )
        text = self.make_text(label, font_size=font_size)
        group = VGroup(bg, text)
        if glow:
            glow_bg = bg.copy().set_stroke(opacity=0.2, width=6).scale(1.03)
            group = VGroup(glow_bg, bg, text)
        return group

    def make_card(self, icon: str, title_text: str, desc_text: str, color: str,
                  w: float = 3.6, h: float = 1.8) -> VGroup:
        """Feature card with accent bar and icon."""
        bg = RoundedRectangle(
            corner_radius=0.15, width=w, height=h,
            fill_color=self.colors.surface, fill_opacity=0.95,
            stroke_color=color, stroke_width=1.2,
        )
        accent = Rectangle(
            width=w, height=0.04,
            fill_color=color, fill_opacity=0.8, stroke_width=0,
        ).move_to(bg.get_top())
        icon_t = self.make_code_label(icon, font_size=32, color=color)
        icon_t.move_to(bg.get_center() + UP * 0.35)
        title_t = self.make_text(title_text, font_size=self.sizes.body_lg, weight=BOLD)
        title_t.move_to(bg.get_center() + DOWN * 0.1)
        desc_t = self.make_text(desc_text, font_size=self.sizes.body_sm - 1,
                                color=self.colors.text_muted)
        desc_t.move_to(bg.get_center() + DOWN * 0.5)
        return VGroup(bg, accent, icon_t, title_t, desc_t)

    def make_arrow(self, start, end) -> Arrow:
        """Standard arrow for diagrams."""
        return Arrow(
            start, end,
            color=self.colors.arrow, stroke_width=1.8, buff=0.1,
            tip_length=0.2,
        )

    def make_insight_bar(self, text_str: str, color: str | None = None,
                         w: float | None = None) -> VGroup:
        """Bottom insight callout bar — white bg, black text."""
        color = color or self.colors.amber
        font = self.smart_font(text_str)
        if font == self.fonts.en:
            t = Text(text_str, font_size=self.sizes.body_lg * 2,
                     font=self.fonts.en, color="#000000", weight=BOLD)
            t.scale(0.5)
        else:
            t = Text(text_str, font_size=self.sizes.body_lg,
                     font=font, color="#000000", weight=BOLD)
        pad_x, pad_y = 0.4, 0.25
        bar_w = w if w else t.width + pad_x * 2
        bg = RoundedRectangle(
            corner_radius=0.1, width=bar_w, height=t.height + pad_y * 2,
            fill_color=WHITE, fill_opacity=1.0, stroke_width=0,
        )
        t.move_to(bg)
        group = VGroup(bg, t)
        group.to_edge(DOWN, buff=0.4)
        return group

    def make_memory_box(self, title_str: str, subtitle_mono: str, desc_str: str,
                        color: str, w: float = 4.2, h: float = 1.6) -> VGroup:
        """Data/file display box."""
        bg = RoundedRectangle(
            corner_radius=0.12, width=w, height=h,
            fill_color=color, fill_opacity=0.08,
            stroke_color=color, stroke_width=1.5,
        )
        t = self.make_text(title_str, font_size=24, color=color, weight=BOLD)
        t.move_to(bg.get_center() + UP * 0.35)
        s = self.make_code_label(subtitle_mono, font_size=14)
        s.move_to(bg.get_center() + DOWN * 0.05)
        d = self.make_text(desc_str, font_size=self.sizes.caption, color=self.colors.text_muted)
        d.move_to(bg.get_center() + DOWN * 0.35)
        return VGroup(bg, t, s, d)

    # ━━━ GLASS OVERLAY SYSTEM ━━━

    def make_glass(self, mobject, pad_x: float = 0.6, pad_y: float = 0.5) -> VGroup:
        """Dark glass container with rim light effect."""
        w = mobject.width + pad_x * 2
        h = mobject.height + pad_y * 2
        base = RoundedRectangle(
            corner_radius=0.15, width=w, height=h,
            fill_color="#121212", fill_opacity=0.95, stroke_width=0,
        )
        glow = RoundedRectangle(
            corner_radius=0.15, width=w, height=h,
            fill_color="#000000", fill_opacity=0,
            stroke_color=WHITE, stroke_width=2, stroke_opacity=0.1,
        )
        rim = RoundedRectangle(
            corner_radius=0.15, width=w, height=h,
            fill_opacity=0, stroke_color="#555555", stroke_width=1.5,
        )
        group = VGroup(base, glow, rim)
        group.move_to(mobject.get_center())
        group.set_z_index(5)
        return group

    def make_shadow(self, mobject, layers: int = 5, opacity: float = 0.4,
                    spread: float = 1.1, offset: float = 0.15) -> VGroup:
        """Multi-layer gaussian blur shadow."""
        shadow_group = VGroup()
        for i in range(layers):
            s_factor = 1.0 + (spread - 1.0) * (i / layers)
            op = opacity * (1.0 - (i / layers)) * 0.5
            layer = mobject.copy()
            layer.set_fill("#000000", opacity=op)
            layer.set_stroke(width=0)
            layer.scale(s_factor)
            layer.shift(DOWN * offset)
            shadow_group.add(layer)
        shadow_group.set_z_index(mobject.z_index - 1 if hasattr(mobject, "z_index") else 4)
        return shadow_group

    def callout_pop(self, scene, content_group, bg_group=None):
        """Premium pop-in: glass + shadow + elastic overshoot. Returns (glass, shadow)."""
        glass = self.make_glass(content_group)
        shadow = self.make_shadow(glass)
        content_group.set_z_index(10)

        content_group.save_state()
        shadow.save_state()
        glass.save_state()

        content_group.scale(0.8).set_opacity(0)
        shadow.scale(0.8).set_opacity(0)
        glass.scale(0.8).set_opacity(0)

        anims = []
        if bg_group is not None:
            anims.append(bg_group.animate.set_opacity(0.15))
        anims.extend([
            glass.animate(rate_func=rate_functions.ease_out_back).restore(),
            shadow.animate(rate_func=rate_functions.ease_out_back).restore(),
            content_group.animate(rate_func=rate_functions.ease_out_back).restore(),
        ])
        scene.play(AnimationGroup(*anims), run_time=0.6)
        return glass, shadow

    def callout_out(self, scene, callout, shadow, dim=None, bg_group=None):
        """Animate callout disappearing."""
        anims = [FadeOut(callout)]
        if shadow is not None:
            anims.append(FadeOut(shadow))
        if dim is not None:
            anims.append(FadeOut(dim))
        if bg_group is not None:
            anims.append(bg_group.animate.set_opacity(1.0))
        scene.play(*anims, run_time=0.3)

    # ━━━ BACKGROUNDS ━━━

    def make_grid_bg(self) -> NumberPlane:
        """Subtle grid background."""
        return NumberPlane(
            x_range=[-8, 8], y_range=[-5, 5],
            background_line_style={
                "stroke_color": self.colors.surface_light,
                "stroke_width": 0.5,
                "stroke_opacity": 0.3,
            },
            axis_config={"stroke_opacity": 0},
            faded_line_ratio=0,
        )

    def make_ambient_particles(self, count: int = 30, seed: int = 42) -> VGroup:
        """Ambient floating particles."""
        random.seed(seed)
        dots = VGroup()
        for _ in range(count):
            d = Dot(
                point=[random.uniform(-7, 7), random.uniform(-4, 4), 0],
                radius=random.uniform(0.01, 0.04),
                color=interpolate_color(
                    ManimColor(self.colors.brand_dark),
                    ManimColor(self.colors.brand_light),
                    random.random(),
                ),
            ).set_opacity(random.uniform(0.1, 0.3))
            dots.add(d)
        return dots

    # ━━━ ANIMATIONS ━━━

    def entrance(self, scene, obj, shift=None, scale: float = 0.9, run_time: float = 0.5):
        shift = shift if shift is not None else UP * 0.3
        scene.play(FadeIn(obj, shift=shift, scale=scale), run_time=run_time)

    def entrance_stagger(self, scene, group, shift=None, scale: float = 0.9,
                         per_item: float = 0.35):
        shift = shift if shift is not None else UP * 0.3
        for item in group:
            scene.play(FadeIn(item, shift=shift, scale=scale), run_time=per_item)

    def scale_bounce_in(self, scene, obj, run_time: float = 0.6):
        obj.save_state()
        obj.scale(0).set_opacity(0)
        scene.play(obj.animate.restore(), run_time=run_time,
                   rate_func=rate_functions.ease_out_back)

    def zoom_reveal(self, scene, obj, run_time: float = 0.8):
        obj.save_state()
        obj.scale(0.01).set_opacity(0)
        scene.play(obj.animate.restore(), run_time=run_time, rate_func=smooth)

    def cascade_in(self, scene, group, direction=None, stagger: float = 0.12):
        direction = direction if direction is not None else DOWN
        anims = [FadeIn(item, shift=direction * 0.4, scale=0.9) for item in group]
        scene.play(
            LaggedStart(*anims, lag_ratio=stagger),
            run_time=len(group) * stagger + 0.5,
        )

    def line_wipe_transition(self, scene, run_time: float = 0.8):
        line = Rectangle(
            width=0, height=8,
            fill_color=self.colors.brand, fill_opacity=0.15, stroke_width=0,
        ).move_to(LEFT * 8)
        scene.play(
            line.animate.stretch_to_fit_width(16).move_to(ORIGIN),
            run_time=run_time * 0.4,
        )
        scene.play(
            line.animate.stretch_to_fit_width(0).move_to(RIGHT * 8),
            run_time=run_time * 0.6,
        )
        scene.remove(line)

    def flash_transition(self, scene, run_time: float = 0.7):
        flash = Rectangle(
            width=14, height=8,
            fill_color=WHITE, fill_opacity=0.12, stroke_width=0,
        )
        scene.play(FadeIn(flash, run_time=0.15))
        scene.play(FadeOut(flash, run_time=run_time - 0.15))

    # ━━━ MAC WINDOW COMPONENTS ━━━

    def make_terminal_window(self, commands, title: str = "Terminal",
                             width: float = 10, height: float = 4,
                             prompt: str = "$") -> VGroup:
        """macOS Terminal window with command lines."""
        title_bar_height = 0.45
        padding_x, padding_y = 0.4, 0.3

        window_bg = RoundedRectangle(
            corner_radius=0.12, width=width, height=height,
            fill_color="#1e1e1e", fill_opacity=1,
            stroke_color="#3d3d3d", stroke_width=1,
        )
        title_bar = Rectangle(
            width=width, height=title_bar_height,
            fill_color="#3d3d3d", fill_opacity=1, stroke_width=0,
        ).move_to(window_bg.get_top() + DOWN * title_bar_height / 2)

        buttons = self._traffic_lights(title_bar)
        title_text = Text(title, font_size=13, font=self.fonts.en, color="#cccccc")
        title_text.move_to(title_bar)

        content_start = (window_bg.get_corner(UP + LEFT)
                         + DOWN * (title_bar_height + padding_y) + RIGHT * padding_x)
        lines = VGroup()
        for i, cmd in enumerate(commands):
            if isinstance(cmd, tuple):
                command, output = cmd
            else:
                command, output = cmd, None
            prompt_text = Text(f"{prompt} ", font_size=18, font=self.fonts.mono,
                               color=self.colors.green)
            cmd_text = Text(command, font_size=18, font=self.fonts.mono, color="#e0e0e0")
            cmd_line = VGroup(prompt_text, cmd_text).arrange(RIGHT, buff=0.08)
            cmd_line.move_to(content_start + DOWN * i * 0.45, aligned_edge=LEFT)
            lines.add(cmd_line)
            if output:
                out_text = Text(output, font_size=16, font=self.fonts.mono, color="#888888")
                out_text.next_to(cmd_line, DOWN, buff=0.15, aligned_edge=LEFT)
                lines.add(out_text)

        return VGroup(window_bg, title_bar, buttons, title_text, lines)

    def make_code_window(self, code_lines: list[str], title: str = "code.py",
                         width: float = 10, height: float = 5,
                         show_line_numbers: bool = True) -> VGroup:
        """macOS-style code editor window."""
        title_bar_height = 0.45
        padding_x, padding_y = 0.4, 0.3

        window_bg = RoundedRectangle(
            corner_radius=0.12, width=width, height=height,
            fill_color="#1e1e1e", fill_opacity=1,
            stroke_color="#3d3d3d", stroke_width=1,
        )
        title_bar = Rectangle(
            width=width, height=title_bar_height,
            fill_color="#323233", fill_opacity=1, stroke_width=0,
        ).move_to(window_bg.get_top() + DOWN * title_bar_height / 2)

        buttons = self._traffic_lights(title_bar)
        title_text = Text(title, font_size=13, font=self.fonts.en, color="#cccccc")
        title_text.move_to(title_bar)

        content_start = (window_bg.get_corner(UP + LEFT)
                         + DOWN * (title_bar_height + padding_y) + RIGHT * padding_x)
        lines = VGroup()
        for i, line in enumerate(code_lines):
            line_group = VGroup()
            if show_line_numbers:
                line_num = Text(f"{i + 1:3}", font_size=12, font=self.fonts.mono, color="#6e7681")
                line_group.add(line_num)
            code_text = Text(line if line else " ", font_size=14,
                             font=self.fonts.mono, color="#e0e0e0")
            line_group.add(code_text)
            line_group.arrange(RIGHT, buff=0.25)
            line_group.move_to(content_start + DOWN * i * 0.35, aligned_edge=LEFT)
            lines.add(line_group)

        return VGroup(window_bg, title_bar, buttons, title_text, lines)

    def _traffic_lights(self, title_bar) -> VGroup:
        """macOS window traffic light buttons."""
        r = 0.07
        spacing = 0.22
        start = title_bar.get_left() + RIGHT * 0.35
        close = Circle(radius=r, fill_color="#ff5f57", fill_opacity=1, stroke_width=0)
        close.move_to(start)
        mini = Circle(radius=r, fill_color="#febc2e", fill_opacity=1, stroke_width=0)
        mini.move_to(start + RIGHT * spacing)
        maxi = Circle(radius=r, fill_color="#28c840", fill_opacity=1, stroke_width=0)
        maxi.move_to(start + RIGHT * spacing * 2)
        return VGroup(close, mini, maxi)

    # ━━━ LAYOUT HELPERS ━━━

    @staticmethod
    def grid_layout(objects, cols: int = 2, spacing: float = 24) -> VGroup:
        rows = []
        for i in range(0, len(objects), cols):
            row = VGroup(*objects[i:i + cols])
            row.arrange(RIGHT, buff=spacing)
            rows.append(row)
        grid = VGroup(*rows)
        grid.arrange(DOWN, buff=spacing)
        return grid

    @staticmethod
    def stack_layout(objects, spacing: float = 16, align=ORIGIN) -> VGroup:
        stack = VGroup(*objects)
        stack.arrange(DOWN, buff=spacing, aligned_edge=align)
        return stack
