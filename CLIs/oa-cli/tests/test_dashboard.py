"""Tests for dashboard static files."""
from pathlib import Path


class TestDashboardFiles:
    def test_index_html_exists(self):
        dashboard_dir = Path(__file__).parent.parent / "src" / "oa" / "dashboard"
        assert (dashboard_dir / "index.html").exists()

    def test_style_css_exists(self):
        dashboard_dir = Path(__file__).parent.parent / "src" / "oa" / "dashboard"
        assert (dashboard_dir / "style.css").exists()

    def test_app_js_exists(self):
        dashboard_dir = Path(__file__).parent.parent / "src" / "oa" / "dashboard"
        assert (dashboard_dir / "app.js").exists()

    def test_index_html_has_title(self):
        dashboard_dir = Path(__file__).parent.parent / "src" / "oa" / "dashboard"
        html = (dashboard_dir / "index.html").read_text()
        assert "OA" in html
        assert "Dashboard" in html

    def test_no_personal_data_in_dashboard(self):
        """Verify no private info leaked into dashboard files."""
        dashboard_dir = Path(__file__).parent.parent / "src" / "oa" / "dashboard"
        for f in dashboard_dir.iterdir():
            if f.is_file():
                content = f.read_text()
                assert "jingshi" not in content.lower()
                assert "motus_ssd" not in content.lower()
                assert "clawd" not in content.lower()

    def test_app_js_fetches_from_api(self):
        dashboard_dir = Path(__file__).parent.parent / "src" / "oa" / "dashboard"
        js = (dashboard_dir / "app.js").read_text()
        assert "/api/goals" in js
        assert "/api/health" in js
        assert "/api/traces" in js
