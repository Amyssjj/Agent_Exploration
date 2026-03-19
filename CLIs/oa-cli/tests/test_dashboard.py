"""Tests for dashboard static files (Vite build output)."""
from pathlib import Path


DASHBOARD_DIR = Path(__file__).parent.parent / "src" / "oa" / "dashboard"


class TestDashboardFiles:
    def test_index_html_exists(self):
        assert (DASHBOARD_DIR / "index.html").exists()

    def test_assets_dir_exists(self):
        assert (DASHBOARD_DIR / "assets").exists()
        assert (DASHBOARD_DIR / "assets").is_dir()

    def test_js_bundle_exists(self):
        js_files = list((DASHBOARD_DIR / "assets").glob("*.js"))
        assert len(js_files) >= 1, "No JS bundle found in assets/"

    def test_css_bundle_exists(self):
        css_files = list((DASHBOARD_DIR / "assets").glob("*.css"))
        assert len(css_files) >= 1, "No CSS bundle found in assets/"

    def test_index_html_structure(self):
        html = (DASHBOARD_DIR / "index.html").read_text()
        assert "OA Dashboard" in html
        assert "<div id=\"root\">" in html

    def test_index_references_assets(self):
        html = (DASHBOARD_DIR / "index.html").read_text()
        assert "assets/" in html  # references built JS/CSS

    def test_no_private_data(self):
        """Verify no private info leaked into dashboard files."""
        private_terms = ["jingshi", "motus_ssd", "clawd", "clawdbot",
                         "mission-control"]
        for f in DASHBOARD_DIR.rglob("*"):
            if f.is_file() and f.suffix in (".html", ".css"):
                content = f.read_text().lower()
                for term in private_terms:
                    assert term not in content, f"Private term '{term}' found in {f.name}"
        # Check JS bundles too (they're minified but still searchable)
        for f in (DASHBOARD_DIR / "assets").glob("*.js"):
            content = f.read_text().lower()
            for term in private_terms:
                assert term not in content, f"Private term '{term}' found in {f.name}"
