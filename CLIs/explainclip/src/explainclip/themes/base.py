"""
Base theme system for ExplainClip.

Themes define colors, fonts, and sizes. Users can extend BaseTheme
to create their own, or use the built-in defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ColorPalette:
    """Core color tokens."""

    # Background
    bg: str = "#080810"
    surface: str = "#12122a"
    surface_light: str = "#1a1a3e"
    border: str = "#2a2a4a"

    # Brand
    brand: str = "#b794f6"
    brand_dark: str = "#7c5cbf"
    brand_light: str = "#d4b5f9"

    # Text
    text_primary: str = "#ffffff"
    text_secondary: str = "#9a9aba"
    text_muted: str = "#6a6a8a"
    text_dim: str = "#4a4a6a"

    # Semantic
    blue: str = "#3b82f6"
    green: str = "#10b981"
    amber: str = "#f59e0b"
    pink: str = "#ec4899"
    cyan: str = "#06b6d4"
    red: str = "#ef4444"
    teal: str = "#14b8a6"

    # Diagram
    arrow: str = "#3a3a5a"


@dataclass
class FontStack:
    """Font configuration with smart language detection."""

    # Primary fonts (used by smart_font auto-detection)
    cn: str = "PingFang SC"
    en: str = "Optima"
    mono: str = "Menlo"
    mixed: str = "Hiragino Sans GB"

    # Fallbacks (tried in order if primary not found)
    cn_fallback: list[str] = field(default_factory=lambda: ["Noto Sans CJK SC", "SimHei"])
    en_fallback: list[str] = field(default_factory=lambda: ["Helvetica Neue", "Arial"])
    mono_fallback: list[str] = field(default_factory=lambda: ["Consolas", "Courier New"])
    mixed_fallback: list[str] = field(default_factory=lambda: ["Noto Sans CJK SC", "PingFang SC"])


@dataclass
class SizeScale:
    """Typography size scale."""

    title_xl: int = 56
    title_lg: int = 48
    title_md: int = 36
    body_lg: int = 22
    body_md: int = 16
    body_sm: int = 14
    caption: int = 12


@dataclass
class Theme:
    """Complete theme configuration."""

    name: str = "default"
    colors: ColorPalette = field(default_factory=ColorPalette)
    fonts: FontStack = field(default_factory=FontStack)
    sizes: SizeScale = field(default_factory=SizeScale)

    # Layout
    card_radius: float = 0.16
    safe_margin: float = 0.3

    # Timing
    timing_instant: float = 0.15
    timing_fast: float = 0.25
    timing_normal: float = 0.4
    timing_slow: float = 0.6
