# 🎬 ExplainClip

**Production-quality animated explainer videos from the command line.**

ExplainClip is an opinionated CLI toolkit built on top of [Manim](https://www.manim.community/) that takes the pain out of creating polished explainer animations. It gives you a design system, smart font handling, glass overlays, and a complete production pipeline — so you can focus on content, not tweaking pixels.

## Why ExplainClip?

Manim is powerful, but going from "install manim" to "ship a polished video" is a long road. You have to build your own design system, fight font rendering bugs, figure out spacing, and wire up a concat + audio pipeline.

ExplainClip packages all of that into one `pip install`. You get:

- A battle-tested design system with 30+ components
- Smart Chinese/English font detection that just works
- Three built-in themes (or bring your own)
- A CLI that handles the full lifecycle: scaffold → render → preview → build

Whether you're a developer making technical explainers, a teacher building course animations, or an AI agent producing video content — ExplainClip gets you from idea to polished video in minutes, not hours.

## Features

- 🎨 **Configurable themes** — three built-in themes (default, ocean, warm) or bring your own via YAML
- 🔤 **Smart font detection** — auto-detects Chinese/English/mixed text and applies the correct font + kerning fixes
- 🪟 **Glass overlay system** — premium callout pop-ins with shadows and elastic animations
- 🖥️ **macOS components** — terminal windows, code editors, app windows out of the box
- 📐 **Frame safety** — automatic clamping to keep content within safe zones
- 🎬 **Full pipeline** — init → render → build (concat + audio)
- 🤖 **AI-agent friendly** — typed API, constrained components, validate command for self-checking

## Quick Start

```bash
pip install explainclip

# Create a new project
explainclip init my-video

# Preview a scene (fast, 480p)
cd my-video
explainclip preview scenes/intro.py Intro

# Render at 1080p
explainclip render scenes/intro.py Intro

# Build final video from all scenes
explainclip build Scene1 Scene2 Scene3 -o final.mp4
```

### What you get after `init`

```
my-video/
├── scenes/
│   └── intro.py           ← working example scene
├── assets/                 ← your images, audio, etc.
├── media/                  ← rendered output goes here
├── theme.yaml              ← customize colors, fonts, sizes
└── explainclip.yaml        ← project config
```

## Writing Scenes

Every component lives on a `Design` instance. No magic globals, no guessing — just autocomplete-friendly methods:

```python
from manim import *
from explainclip.design import Design

d = Design()  # uses default theme
# d = Design(theme="ocean")           # built-in theme
# d = Design(theme="my-theme.yaml")   # custom theme file

class MyScene(Scene):
    def construct(self):
        self.camera.background_color = d.colors.bg

        # Section header with brand-colored underline
        header = d.make_header("Why ExplainClip?")
        d.scale_bounce_in(self, header)

        # Feature cards — icon, title, description, color
        card = d.make_card("[>]", "Fast", "Ship videos, not configs", d.colors.green)
        card.next_to(header, DOWN, buff=1)
        d.entrance(self, card)

        # Bottom insight bar
        insight = d.make_insight_bar("Because raw Manim shouldn't require a PhD")
        self.play(FadeIn(insight, shift=UP * 0.2))
        self.wait(2)
```

You never touch raw Manim primitives unless you want to. Font rendering, spacing, colors, kerning — all handled.

## Using with AI Agents (Claude Code, Codex, etc.)

ExplainClip is designed to work beautifully with AI coding agents. Here's why:

### The problem without ExplainClip

When you tell an AI agent "make me an animated explainer video," it has to:
1. Learn Manim's API from scratch (or hallucinate it)
2. Figure out font rendering quirks by trial and error
3. Build a design system from nothing
4. Get spacing, colors, and overlays right through iteration

### The solution

With ExplainClip installed, the agent just needs to know:

> *Use explainclip. Import `Design`, call `d.make_header()`, `d.make_card()`, `d.make_node()`, `d.cascade_in()`. Render with `explainclip render`.*

```bash
# Agent sets up the project
pip install explainclip
explainclip init project

# Agent writes scenes using the typed, documented API
# Every method has docstrings, type hints, clear parameters

# Agent self-checks before delivering
explainclip validate

# Agent renders and builds
explainclip render scenes/scene01.py MyScene
explainclip build Scene1 Scene2 -o final.mp4
```

### Why agents love this

| Feature | Why it helps |
|---------|-------------|
| **Typed `Design` class** | Methods with type hints — agents autocomplete correctly instead of guessing |
| **Constrained components** | `d.make_card()` instead of "figure out RoundedRectangle params" — fewer decisions, fewer hallucinations |
| **`validate` command** | Agent can self-check: catches raw Manim usage, missing `clamp_to_frame()`, font issues |
| **Deterministic themes** | Agent picks `"ocean"` or `"warm"`, gets a guaranteed good-looking result without color theory |
| **Clear error messages** | "You used raw `Text()` — use `d.make_text()` instead" |

### Agent instructions example

Add this to your agent config (e.g., `AGENTS.md`, `.claude/instructions`, or system prompt):

```markdown
## Video Production
- Use `explainclip` for all animated content
- Theme: use our-brand.yaml in project root
- Always run `explainclip validate` before rendering
- Components: d.make_header() for titles, d.make_card() for features,
  d.make_node() + d.make_arrow() for architecture diagrams
```

Now the agent produces **brand-consistent videos every time** without re-learning the design system per session.

## Themes

### Built-in

| Theme | Brand Color | Vibe |
|-------|------------|------|
| `default` | Purple `#b794f6` | Dark, modern, tech |
| `ocean` | Blue `#60a5fa` | Cool, professional |
| `warm` | Amber `#f59e0b` | Earthy, inviting |

```bash
# List available themes with color swatches
explainclip themes

# Start a project with a specific theme
explainclip init my-video --theme ocean
```

### Custom Themes

Create a `theme.yaml` — override only what you need, everything else falls back to defaults:

```yaml
name: my-brand
colors:
  brand: "#ff6600"
  bg: "#0a0a0a"
  surface: "#1a1a1a"
fonts:
  en: "Inter"
  cn: "Noto Sans CJK SC"
sizes:
  body_lg: 24
```

```python
d = Design(theme="theme.yaml")
```

## Components

### Text & Labels

| Component | Method | Use Case |
|-----------|--------|----------|
| Smart text | `d.make_text("Hello")` | Auto-detects language, applies correct font |
| Code label | `d.make_code_label("main.py")` | Inline monospace text |
| Header | `d.make_header("Title")` | Section titles with underline accent |
| Insight bar | `d.make_insight_bar("Key takeaway")` | Bottom callout — white bg, black text |

### Diagrams & Cards

| Component | Method | Use Case |
|-----------|--------|----------|
| Node | `d.make_node("Server", d.colors.blue)` | Architecture diagram boxes |
| Arrow | `d.make_arrow(start, end)` | Flow connections |
| Card | `d.make_card(icon, title, desc, color)` | Feature showcases |
| Memory box | `d.make_memory_box(title, sub, desc, color)` | Data/file displays |

### macOS Components

| Component | Method | Use Case |
|-----------|--------|----------|
| Terminal | `d.make_terminal_window(commands)` | CLI demos |
| Code editor | `d.make_code_window(lines, title="app.py")` | Code walkthroughs |

### Glass Overlay System

For layered analysis — pop explanations on top of existing content:

```python
# Pop in a glass overlay
content = d.make_text("This is the key insight", font_size=22)
glass, shadow = d.callout_pop(self, content, bg_group=existing_content)

# Dismiss
d.callout_out(self, content, shadow, dim=glass, bg_group=existing_content)
```

## Animations

```python
# Entrances
d.scale_bounce_in(self, obj)         # Elastic pop-in
d.zoom_reveal(self, obj)             # Zoom from center
d.cascade_in(self, group)            # Staggered group entrance
d.entrance(self, obj)                # Standard fade-in
d.entrance_stagger(self, group)      # One-by-one fade-in

# Transitions
d.line_wipe_transition(self)         # Horizontal line wipe
d.flash_transition(self)             # White flash

# Overlays
glass, shadow = d.callout_pop(self, content, bg)  # Glass pop-in
d.callout_out(self, content, shadow, glass, bg)    # Dismiss

# Layout
d.clamp_to_frame(obj)               # Keep within safe zone
d.grid_layout(items, cols=3)         # Grid arrangement
d.stack_layout(items)                # Vertical stack
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `explainclip init <name>` | Create a new project with example scene and theme template |
| `explainclip render <file> <Class>` | Render a scene (options: `--quality low/medium/high/4k`, `--output`) |
| `explainclip preview <file> <Class>` | Quick 480p preview with auto-open |
| `explainclip build <scenes...>` | Concatenate rendered scenes into final video |
| `explainclip validate` | Check scenes against design system rules |
| `explainclip themes` | List available built-in themes |

## Requirements

- **Python 3.10+**
- **[Manim Community](https://docs.manim.community/en/stable/installation.html)** — installed automatically as a dependency
- **ffmpeg** — required for video concat and audio mixing
- **LaTeX** — optional, only needed for math equations

### Font recommendations

ExplainClip works with any system fonts. For the best experience with Chinese + English content:

| Font | Platform | Use |
|------|----------|-----|
| PingFang SC | macOS (built-in) | Chinese text |
| Optima | macOS (built-in) | English text |
| Menlo | macOS (built-in) | Code/monospace |
| Noto Sans CJK SC | All platforms (free) | Chinese fallback |
| Inter | All platforms (free) | English alternative |

## Roadmap

- [ ] `explainclip doctor` — check system dependencies (Manim, ffmpeg, fonts)
- [ ] `explainclip scaffold` — generate scene skeletons from topic descriptions
- [ ] Audio pipeline integration — swish/ding/music effects in `build`
- [ ] `--json` output mode for programmatic usage
- [ ] Component visual gallery in docs
- [ ] More built-in themes

## Contributing

Contributions welcome! Please open an issue first to discuss what you'd like to change.

```bash
git clone https://github.com/motusai/explainclip
cd explainclip
pip install -e ".[dev]"
ruff check .
pytest
```

## License

MIT — built by [MotusAI](https://motusai.com)
