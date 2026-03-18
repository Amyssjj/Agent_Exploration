"""Tests for dashboard static files."""
from pathlib import Path


DASHBOARD_DIR = Path(__file__).parent.parent / "src" / "oa" / "dashboard"


class TestDashboardFiles:
    def test_index_html_exists(self):
        assert (DASHBOARD_DIR / "index.html").exists()

    def test_style_css_exists(self):
        assert (DASHBOARD_DIR / "style.css").exists()

    def test_app_js_exists(self):
        assert (DASHBOARD_DIR / "app.js").exists()

    def test_index_html_structure(self):
        html = (DASHBOARD_DIR / "index.html").read_text()
        assert "OA Dashboard" in html
        assert "tailwindcss" in html  # Tailwind CDN
        assert "chart.js" in html or "Chart" in html  # Chart.js CDN
        assert "health-strip" in html
        assert "system-health" in html

    def test_glass_morphism_styles(self):
        css = (DASHBOARD_DIR / "style.css").read_text()
        assert "glass-card" in css
        assert "backdrop-filter" in css
        assert "blur(24px)" in css
        assert "dot-matrix" in css.lower() or "radial-gradient" in css

    def test_app_js_api_endpoints(self):
        js = (DASHBOARD_DIR / "app.js").read_text()
        assert "/api/goals" in js
        assert "/api/health" in js
        assert "/api/traces" in js
        assert "Chart" in js  # Chart.js usage

    def test_no_private_data(self):
        """Verify no private info leaked into dashboard files."""
        private_terms = ["jingshi", "motus_ssd", "clawd", "clawdbot",
                         "motusai", "mission-control", "1465", "1466"]
        for f in DASHBOARD_DIR.iterdir():
            if f.is_file():
                content = f.read_text().lower()
                for term in private_terms:
                    assert term not in content, f"Private term '{term}' found in {f.name}"
