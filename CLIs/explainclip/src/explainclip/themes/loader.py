"""Theme loading from YAML files."""
from __future__ import annotations

from pathlib import Path

import yaml

from .base import ColorPalette, FontStack, SizeScale, Theme

# Built-in themes registry
_BUILTIN_THEMES: dict[str, Theme] = {}


def _register_builtins() -> None:
    """Register the three default themes."""
    if _BUILTIN_THEMES:
        return

    # 1. Default — our original MotusAI look (purple brand, dark bg)
    _BUILTIN_THEMES["default"] = Theme(name="default")

    # 2. Ocean — cool blue professional theme
    _BUILTIN_THEMES["ocean"] = Theme(
        name="ocean",
        colors=ColorPalette(
            bg="#0a0f1a",
            surface="#111827",
            surface_light="#1f2937",
            border="#374151",
            brand="#60a5fa",
            brand_dark="#2563eb",
            brand_light="#93c5fd",
            text_primary="#f9fafb",
            text_secondary="#9ca3af",
            text_muted="#6b7280",
            text_dim="#4b5563",
            arrow="#4b5563",
        ),
    )

    # 3. Warm — amber/gold earthy theme
    _BUILTIN_THEMES["warm"] = Theme(
        name="warm",
        colors=ColorPalette(
            bg="#0f0a05",
            surface="#1c1510",
            surface_light="#2a2018",
            border="#4a3a28",
            brand="#f59e0b",
            brand_dark="#b45309",
            brand_light="#fbbf24",
            text_primary="#fef3c7",
            text_secondary="#d4a574",
            text_muted="#8a7050",
            text_dim="#5a4a30",
            arrow="#5a4a30",
        ),
    )


def get_theme(name: str = "default") -> Theme:
    """Get a built-in theme by name."""
    _register_builtins()
    if name not in _BUILTIN_THEMES:
        available = ", ".join(sorted(_BUILTIN_THEMES.keys()))
        raise ValueError(f"Unknown theme '{name}'. Available: {available}")
    return _BUILTIN_THEMES[name]


def load_theme_file(path: str | Path) -> Theme:
    """Load a custom theme from a YAML file.

    Example YAML::

        name: my-brand
        colors:
          brand: "#ff6600"
          bg: "#0a0a0a"
        fonts:
          en: "Inter"
        sizes:
          body_lg: 24

    Only specified fields are overridden; everything else uses defaults.
    """
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    theme = Theme(name=data.get("name", path.stem))

    if "colors" in data:
        for k, v in data["colors"].items():
            if hasattr(theme.colors, k):
                setattr(theme.colors, k, v)

    if "fonts" in data:
        for k, v in data["fonts"].items():
            if hasattr(theme.fonts, k):
                setattr(theme.fonts, k, v)

    if "sizes" in data:
        for k, v in data["sizes"].items():
            if hasattr(theme.sizes, k):
                setattr(theme.sizes, k, int(v))

    # Top-level overrides
    for key in ("card_radius", "safe_margin", "timing_instant", "timing_fast",
                "timing_normal", "timing_slow"):
        if key in data:
            setattr(theme, key, float(data[key]))

    return theme
