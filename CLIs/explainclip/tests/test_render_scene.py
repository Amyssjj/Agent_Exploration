"""Minimal scene for test rendering — exercises key Design components."""
from manim import *
from explainclip.design import Design

d = Design(theme="ocean")


class TestRenderScene(Scene):
    """A quick scene that exercises the main design components."""

    def construct(self):
        self.camera.background_color = d.colors.bg

        # 1. Header
        header = d.make_header("ExplainClip Test Render")
        self.play(FadeIn(header), run_time=0.3)
        self.wait(0.3)

        # 2. Node diagram
        n1 = d.make_node("Input", d.colors.blue)
        n2 = d.make_node("Process", d.colors.green, glow=True)
        n3 = d.make_node("Output", d.colors.amber)
        nodes = VGroup(n1, n2, n3).arrange(RIGHT, buff=1.2).shift(UP * 0.5)
        self.play(FadeIn(nodes), run_time=0.3)

        a1 = d.make_arrow(n1.get_right(), n2.get_left())
        a2 = d.make_arrow(n2.get_right(), n3.get_left())
        self.play(Create(a1), Create(a2), run_time=0.3)
        self.wait(0.3)

        # 3. Feature card
        card = d.make_card("[C]", "Components", "30+ Manim primitives", d.colors.brand)
        card.shift(DOWN * 1.8)
        self.play(FadeIn(card, shift=UP * 0.3), run_time=0.3)

        # 4. Insight bar
        insight = d.make_insight_bar("All components render correctly!")
        self.play(FadeIn(insight, shift=UP * 0.2), run_time=0.3)
        self.wait(0.5)
