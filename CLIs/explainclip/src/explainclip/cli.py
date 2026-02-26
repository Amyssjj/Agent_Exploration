"""ExplainClip CLI — the main entry point."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from . import __version__

console = Console()

TEMPLATE_DIR = Path(__file__).parent / "templates"


@click.group()
@click.version_option(__version__, prog_name="explainclip")
def main():
    """ExplainClip — Production-quality animated explainer videos from the CLI."""
    pass


@main.command()
@click.argument("name")
@click.option("--theme", "-t", default="default", help="Theme: default, ocean, warm, or path to .yaml")
def init(name: str, theme: str):
    """Create a new ExplainClip project."""
    project = Path(name)
    if project.exists():
        console.print(f"[red]Error:[/] Directory '{name}' already exists.")
        raise SystemExit(1)

    # Scaffold
    project.mkdir(parents=True)
    (project / "scenes").mkdir()
    (project / "media").mkdir()
    (project / "assets").mkdir()

    # Write project config
    config_content = f"""# ExplainClip project config
name: {name}
theme: {theme}
quality: high  # low (480p), medium (720p), high (1080p), 4k
"""
    (project / "explainclip.yaml").write_text(config_content)

    # Write example scene
    example = '''"""Example ExplainClip scene."""
from manim import *
from explainclip.design import Design

# Initialize with project theme (or override here)
d = Design()


class Intro(Scene):
    def construct(self):
        self.camera.background_color = d.colors.bg

        # Header
        header = d.make_header("Welcome to ExplainClip")
        d.scale_bounce_in(self, header, run_time=0.5)
        self.wait(0.5)

        # Feature cards
        card1 = d.make_card("[T]", "Themes", "Configurable design tokens", d.colors.blue)
        card2 = d.make_card("[S]", "Smart Text", "Auto CN/EN font detection", d.colors.green)
        card3 = d.make_card("[G]", "Glass UI", "Premium overlay system", d.colors.brand)

        cards = VGroup(card1, card2, card3).arrange(RIGHT, buff=0.4)
        cards.next_to(header, DOWN, buff=0.8)
        d.cascade_in(self, cards)
        self.wait(1)

        # Insight
        insight = d.make_insight_bar("Build beautiful explainer videos from the CLI")
        self.play(FadeIn(insight, shift=UP * 0.2), run_time=0.4)
        self.wait(2)
'''
    (project / "scenes" / "intro.py").write_text(example)

    # Write custom theme template
    theme_template = """# Custom ExplainClip theme
# Override only what you need — everything else uses defaults.
# See: https://github.com/motusai/explainclip#themes

name: my-theme

colors:
  brand: "#b794f6"
  bg: "#080810"
  # surface: "#12122a"
  # text_primary: "#ffffff"

fonts:
  en: "Optima"
  cn: "PingFang SC"
  mono: "Menlo"
  # mixed: "Hiragino Sans GB"

# sizes:
#   title_lg: 48
#   body_lg: 22
"""
    (project / "theme.yaml").write_text(theme_template)

    console.print(Panel(
        f"[green]✓[/] Created project [bold]{name}[/]\n\n"
        f"  [dim]scenes/intro.py[/]    — example scene\n"
        f"  [dim]theme.yaml[/]         — customize your theme\n"
        f"  [dim]explainclip.yaml[/]   — project config\n\n"
        f"Next steps:\n"
        f"  cd {name}\n"
        f"  explainclip render intro.py Intro\n"
        f"  explainclip preview intro.py Intro",
        title="🎬 ExplainClip",
        border_style="bright_magenta",
    ))


@main.command()
@click.argument("scene_file")
@click.argument("class_name")
@click.option("--quality", "-q", default="high",
              type=click.Choice(["low", "medium", "high", "4k"]))
@click.option("--output", "-o", default=None, help="Output filename")
def render(scene_file: str, class_name: str, quality: str, output: str | None):
    """Render a scene to video."""
    quality_map = {"low": "l", "medium": "m", "high": "h", "4k": "k"}
    q = quality_map[quality]

    cmd = [sys.executable, "-m", "manim", "render", f"-q{q}", scene_file, class_name]
    if output:
        cmd.extend(["-o", output])

    console.print(f"[bright_magenta]▸[/] Rendering [bold]{class_name}[/] @ {quality}...")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        console.print("[red]✗[/] Render failed.")
        raise SystemExit(result.returncode)
    console.print("[green]✓[/] Render complete.")


@main.command()
@click.argument("scene_file")
@click.argument("class_name")
def preview(scene_file: str, class_name: str):
    """Quick low-quality preview of a scene."""
    cmd = [sys.executable, "-m", "manim", "render", "-ql", "--preview", scene_file, class_name]
    console.print(f"[bright_magenta]▸[/] Previewing [bold]{class_name}[/]...")
    subprocess.run(cmd)


@main.command()
@click.argument("scenes", nargs=-1, required=True)
@click.option("--output", "-o", default="final.mp4", help="Output filename")
def build(scenes: tuple[str, ...], output: str):
    """Concatenate rendered scenes into final video."""
    # Find rendered files
    media_dir = Path("media/videos")
    if not media_dir.exists():
        console.print("[red]Error:[/] No rendered media found. Run `explainclip render` first.")
        raise SystemExit(1)

    # Build concat list
    concat_list = Path("_concat_list.txt")
    found = []
    for scene in scenes:
        # Search for the rendered file
        matches = list(media_dir.rglob(f"*{scene}*"))
        if not matches:
            console.print(f"[yellow]Warning:[/] No rendered file found for '{scene}'")
            continue
        found.append(matches[0])

    if not found:
        console.print("[red]Error:[/] No scene files found to concatenate.")
        raise SystemExit(1)

    with open(concat_list, "w") as f:
        for p in found:
            f.write(f"file '{p}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
           "-c", "copy", output]
    console.print(f"[bright_magenta]▸[/] Building {len(found)} scenes → [bold]{output}[/]")
    result = subprocess.run(cmd, capture_output=True)
    concat_list.unlink(missing_ok=True)

    if result.returncode != 0:
        console.print(f"[red]✗[/] Build failed: {result.stderr.decode()[:200]}")
        raise SystemExit(result.returncode)
    console.print(f"[green]✓[/] Built {output}")


@main.command()
@click.option("--path", "-p", default="scenes/", help="Path to validate")
def validate(path: str):
    """Validate scenes against design system rules."""
    validate_script = Path(__file__).parent / "validate.py"
    if not validate_script.exists():
        console.print("[yellow]Validator not yet bundled. Coming in v0.2.[/]")
        return
    subprocess.run([sys.executable, str(validate_script), path])


@main.command(name="themes")
def list_themes():
    """List available built-in themes."""
    from .themes import get_theme

    for name in ("default", "ocean", "warm"):
        t = get_theme(name)
        console.print(
            f"  [bold bright_magenta]{name:10}[/]  "
            f"brand=[{t.colors.brand}]██[/]  "
            f"bg=[{t.colors.bg}]██[/]  "
            f"fonts: {t.fonts.en} / {t.fonts.cn}"
        )
    console.print("\n  [dim]Custom: explainclip init myproject --theme path/to/theme.yaml[/]")


if __name__ == "__main__":
    main()
