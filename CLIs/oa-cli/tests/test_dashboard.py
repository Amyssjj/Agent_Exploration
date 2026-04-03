"""Tests for dashboard static files and rendered dashboard smoke output."""
from __future__ import annotations

import contextlib
import functools
import http.server
import json
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlparse

import pytest

try:
    from PIL import Image, ImageStat
except ImportError:  # pragma: no cover - optional test dependency in some environments
    Image = None
    ImageStat = None


DASHBOARD_DIR = Path(__file__).parent.parent / "src" / "oa" / "dashboard"
CHROME_BIN = (
    shutil.which("google-chrome")
    or shutil.which("google-chrome-stable")
    or shutil.which("chromium")
    or shutil.which("chromium-browser")
)


def _visual_fixture_payload() -> dict[str, object]:
    cron_breakdown = {
        "mode": "scheduled_mode",
        "enabled_jobs": 3,
        "observed_jobs": 3,
        "total_runs": 12,
        "success": 9,
        "failed": 2,
        "unknown": 1,
        "expected_slots": 11,
        "observed_slots": 10,
        "exact_matches": 8,
        "late_matches": 2,
        "missed": 1,
        "missed_slots": [
            {"cron_name": "Daily Digest", "job_id": "job-daily", "slot_time": "19:00:00"},
        ],
        "unexpected_runs": 2,
        "unsupported_schedules": [
            {
                "job_id": "job-fast",
                "cron_name": "Fast Interval",
                "schedule_kind": "every",
                "expr": None,
                "reason": "every schedule under 60000ms not supported at current minute slot precision",
            }
        ],
        "success_rate_denominator": 12,
        "late_tolerance_minutes": 5,
        "slot_matching_policy": (
            "one-to-one per job: exact minute first; otherwise match a single unmatched expected slot "
            "up to 5 minutes earlier; early runs never match future slots; ambiguous late runs stay unexpected"
        ),
        "no_anchor_every_policy": (
            "schedule.kind=every without anchorMs is treated as anchorMs=0, so slots use the Unix epoch "
            "phase in local wall-clock time at minute precision"
        ),
        "unanchored_every_jobs": [{"cron_name": "Nightly Cleanup", "job_id": "job-clean"}],
        "note": "expected-slot reasoning enabled from jobs.json schedules; sample note",
        "per_job": {
            "Daily Digest": {
                "job_id": "job-daily",
                "total": 5,
                "success": 4,
                "failed": 1,
                "unknown": 0,
                "status_details": {"success": 4, "timeout": 1},
                "rate": 80.0,
                "avg_duration_ms": 1820.0,
                "expected_slots": 5,
                "observed_slots": 4,
                "exact_matches": 3,
                "late_matches": 1,
                "missed": 1,
                "missed_slot_times": ["19:00:00"],
                "unexpected_runs": 1,
                "supported_schedule": True,
                "phase_policy": None,
            },
            "Nightly Cleanup": {
                "job_id": "job-clean",
                "total": 4,
                "success": 4,
                "failed": 0,
                "unknown": 0,
                "status_details": {"success": 4},
                "rate": 100.0,
                "avg_duration_ms": 950.0,
                "expected_slots": 4,
                "observed_slots": 4,
                "exact_matches": 4,
                "late_matches": 0,
                "missed": 0,
                "missed_slot_times": [],
                "unexpected_runs": 0,
                "supported_schedule": True,
                "phase_policy": (
                    "schedule.kind=every without anchorMs is treated as anchorMs=0, so slots use the Unix epoch "
                    "phase in local wall-clock time at minute precision"
                ),
            },
            "Fast Interval": {
                "job_id": "job-fast",
                "total": 3,
                "success": 1,
                "failed": 1,
                "unknown": 1,
                "status_details": {"success": 1, "delivery_error": 1, "mystery": 1},
                "rate": 33.3,
                "avg_duration_ms": 410.0,
                "expected_slots": 0,
                "observed_slots": 0,
                "exact_matches": 0,
                "late_matches": 0,
                "missed": 0,
                "missed_slot_times": [],
                "unexpected_runs": 2,
                "supported_schedule": False,
                "unsupported_reason": "every schedule under 60000ms not supported at current minute slot precision",
                "phase_policy": None,
            },
        },
    }

    goals = [
        {
            "id": "cron_reliability",
            "name": "Cron Reliability",
            "builtin": True,
            "metrics": {
                "success_rate": {
                    "value": 92.5,
                    "unit": "%",
                    "healthy": 95,
                    "warning": 80,
                    "direction": "higher",
                    "trend": 4.5,
                    "date": "2026-03-15",
                    "breakdown": cron_breakdown,
                    "status": "warning",
                },
                "failed_runs": {
                    "value": 2,
                    "unit": "count",
                    "healthy": 0,
                    "warning": 1,
                    "direction": "lower",
                    "trend": 1,
                    "date": "2026-03-15",
                    "breakdown": {
                        "failed": 2,
                        "success": 9,
                        "unknown": 1,
                        "expected_slots": 11,
                        "observed_slots": 10,
                        "missed": 1,
                        "unexpected_runs": 2,
                    },
                    "status": "critical",
                },
                "unknown_runs": {
                    "value": 1,
                    "unit": "count",
                    "healthy": 0,
                    "warning": 1,
                    "direction": "lower",
                    "trend": 0,
                    "date": "2026-03-15",
                    "breakdown": {
                        "failed": 2,
                        "success": 9,
                        "unknown": 1,
                        "expected_slots": 11,
                        "observed_slots": 10,
                        "missed": 1,
                        "unexpected_runs": 2,
                    },
                    "status": "warning",
                },
            },
            "sparkline": [
                {"date": "2026-03-11", "value": 82.0},
                {"date": "2026-03-12", "value": 85.0},
                {"date": "2026-03-13", "value": 91.0},
                {"date": "2026-03-14", "value": 88.0},
                {"date": "2026-03-15", "value": 92.5},
            ],
            "healthStatus": "warning",
        },
        {
            "id": "team_health",
            "name": "Team Health",
            "builtin": True,
            "metrics": {
                "active_agent_count": {
                    "value": 3,
                    "unit": "count",
                    "healthy": 3,
                    "warning": 2,
                    "direction": "higher",
                    "trend": 1,
                    "date": "2026-03-15",
                    "breakdown": None,
                    "status": "healthy",
                },
                "inactive_agent_count": {
                    "value": 0,
                    "unit": "count",
                    "healthy": 0,
                    "warning": 1,
                    "direction": "lower",
                    "trend": -1,
                    "date": "2026-03-15",
                    "breakdown": None,
                    "status": "healthy",
                },
                "memory_discipline": {
                    "value": 75.0,
                    "unit": "%",
                    "healthy": 80,
                    "warning": 50,
                    "direction": "higher",
                    "trend": 5,
                    "date": "2026-03-15",
                    "breakdown": None,
                    "status": "warning",
                },
            },
            "sparkline": [],
            "healthStatus": "healthy",
        },
    ]
    health = {
        "overall": "warning",
        "goals": 2,
        "healthy": 1,
        "warning": 1,
        "critical": 0,
        "lastCollected": "2026-03-15",
    }
    cron_runs = [
        {"date": "2026-03-11", "cron_name": "Daily Digest", "status": "success", "job_id": "job-daily"},
        {"date": "2026-03-11", "cron_name": "Nightly Cleanup", "status": "success", "job_id": "job-clean"},
        {"date": "2026-03-11", "cron_name": "Fast Interval", "status": "failure", "job_id": "job-fast"},
        {"date": "2026-03-12", "cron_name": "Daily Digest", "status": "success", "job_id": "job-daily"},
        {"date": "2026-03-12", "cron_name": "Nightly Cleanup", "status": "success", "job_id": "job-clean"},
        {"date": "2026-03-13", "cron_name": "Daily Digest", "status": "failure", "job_id": "job-daily"},
        {"date": "2026-03-13", "cron_name": "Nightly Cleanup", "status": "success", "job_id": "job-clean"},
        {"date": "2026-03-13", "cron_name": "Fast Interval", "status": "unknown", "job_id": "job-fast"},
        {"date": "2026-03-14", "cron_name": "Daily Digest", "status": "success", "job_id": "job-daily"},
        {"date": "2026-03-14", "cron_name": "Nightly Cleanup", "status": "success", "job_id": "job-clean"},
        {"date": "2026-03-14", "cron_name": "Fast Interval", "status": "success", "job_id": "job-fast"},
        {"date": "2026-03-15", "cron_name": "Daily Digest", "status": "success", "job_id": "job-daily"},
        {"date": "2026-03-15", "cron_name": "Daily Digest", "status": "failure", "job_id": "job-daily"},
        {"date": "2026-03-15", "cron_name": "Nightly Cleanup", "status": "success", "job_id": "job-clean"},
        {"date": "2026-03-15", "cron_name": "Nightly Cleanup", "status": "success", "job_id": "job-clean"},
        {"date": "2026-03-15", "cron_name": "Fast Interval", "status": "failure", "job_id": "job-fast"},
    ]
    team_health = [
        {"date": "2026-03-12", "agent_id": "researcher", "session_count": 4, "memory_logged": 1, "last_active": "2026-03-12T12:00:00"},
        {"date": "2026-03-12", "agent_id": "writer", "session_count": 2, "memory_logged": 1, "last_active": "2026-03-12T10:30:00"},
        {"date": "2026-03-12", "agent_id": "reviewer", "session_count": 1, "memory_logged": 0, "last_active": "2026-03-12T08:15:00"},
        {"date": "2026-03-13", "agent_id": "researcher", "session_count": 5, "memory_logged": 1, "last_active": "2026-03-13T13:10:00"},
        {"date": "2026-03-13", "agent_id": "writer", "session_count": 3, "memory_logged": 1, "last_active": "2026-03-13T09:20:00"},
        {"date": "2026-03-13", "agent_id": "reviewer", "session_count": 0, "memory_logged": 0, "last_active": None},
        {"date": "2026-03-14", "agent_id": "researcher", "session_count": 3, "memory_logged": 1, "last_active": "2026-03-14T11:45:00"},
        {"date": "2026-03-14", "agent_id": "writer", "session_count": 4, "memory_logged": 1, "last_active": "2026-03-14T10:10:00"},
        {"date": "2026-03-14", "agent_id": "reviewer", "session_count": 2, "memory_logged": 1, "last_active": "2026-03-14T15:00:00"},
        {"date": "2026-03-15", "agent_id": "researcher", "session_count": 6, "memory_logged": 1, "last_active": "2026-03-15T14:05:00"},
        {"date": "2026-03-15", "agent_id": "writer", "session_count": 4, "memory_logged": 1, "last_active": "2026-03-15T13:00:00"},
        {"date": "2026-03-15", "agent_id": "reviewer", "session_count": 3, "memory_logged": 1, "last_active": "2026-03-15T16:25:00"},
    ]
    goal_metrics = {
        "cron_reliability": [
            {"date": "2026-03-11", "metric": "success_rate", "value": 82.0, "unit": "%", "breakdown": None},
            {"date": "2026-03-12", "metric": "success_rate", "value": 85.0, "unit": "%", "breakdown": None},
            {"date": "2026-03-13", "metric": "success_rate", "value": 91.0, "unit": "%", "breakdown": None},
            {"date": "2026-03-14", "metric": "success_rate", "value": 88.0, "unit": "%", "breakdown": None},
            {"date": "2026-03-15", "metric": "success_rate", "value": 92.5, "unit": "%", "breakdown": cron_breakdown},
            {"date": "2026-03-15", "metric": "failed_runs", "value": 2, "unit": "count", "breakdown": None},
            {"date": "2026-03-15", "metric": "unknown_runs", "value": 1, "unit": "count", "breakdown": None},
        ],
        "team_health": [
            {"date": "2026-03-15", "metric": "active_agent_count", "value": 3, "unit": "count", "breakdown": None},
            {"date": "2026-03-15", "metric": "inactive_agent_count", "value": 0, "unit": "count", "breakdown": None},
            {"date": "2026-03-15", "metric": "memory_discipline", "value": 75.0, "unit": "%", "breakdown": None},
        ],
    }

    return {
        "goals": goals,
        "health": health,
        "traces": [],
        "cronRuns": cron_runs,
        "teamHealth": team_health,
        "goalMetrics": goal_metrics,
    }


def _visual_fixture_api_payload(fixture: dict[str, object]) -> dict[str, object]:
    return {
        "/api/goals": fixture["goals"],
        "/api/health": fixture["health"],
        "/api/traces": fixture["traces"],
        "/api/cron-chart": fixture["cronRuns"],
        "/api/team-health": fixture["teamHealth"],
        "/api/goals/metrics": fixture["goalMetrics"],
    }


def _prepare_visual_dashboard_fixture(tmpdir: str, fixture: dict[str, object]) -> Path:
    dashboard_copy = Path(tmpdir) / "dashboard"
    shutil.copytree(DASHBOARD_DIR, dashboard_copy)

    html = (dashboard_copy / "index.html").read_text()
    html = html.replace('href="/assets/', 'href="./assets/')
    html = html.replace('src="/assets/', 'src="./assets/')
    modulepreload_tags = "\n".join(
        f'    <link rel="modulepreload" href="./assets/{asset.name}" />'
        for pattern in ("SystemHealth-*.js", "GoalDetailSection-*.js", "MetricChartPanel-*.js")
        for asset in sorted((dashboard_copy / "assets").glob(pattern))
    )
    fixture_json = json.dumps(fixture).replace("</", "<\\/")
    bootstrap = f'    <script>window.__OA_VISUAL_TEST_FIXTURE__ = {fixture_json};</script>'
    injection = "\n".join(part for part in (modulepreload_tags, bootstrap) if part)
    html = html.replace("</head>", f"{injection}\n  </head>")
    (dashboard_copy / "index.html").write_text(html)
    return dashboard_copy


@contextlib.contextmanager
def _serve_visual_dashboard_fixture(tmpdir: str):
    fixture = _visual_fixture_payload()
    fixture_api = _visual_fixture_api_payload(fixture)
    dashboard_root = _prepare_visual_dashboard_fixture(tmpdir, fixture)

    class DashboardFixtureHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dashboard_root), **kwargs)

        def do_GET(self):  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path in fixture_api:
                payload = json.dumps(fixture_api[parsed.path]).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            self.path = parsed.path or "/"
            super().do_GET()

        def log_message(self, format, *args):  # noqa: A003
            return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), DashboardFixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/index.html?visual-test=1"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _count_dark_pixels(image) -> int:
    return sum(1 for r, g, b in image.getdata() if max(r, g, b) < 150)


def _count_accent_pixels(image) -> int:
    return sum(1 for r, g, b in image.getdata() if max(r, g, b) - min(r, g, b) > 45 and max(r, g, b) > 115)


def _chrome_supports_headless_screenshot() -> tuple[bool, str]:
    if CHROME_BIN is None:
        return False, "Headless Chrome binary not found."

    with tempfile.TemporaryDirectory() as tmpdir:
        probe_path = Path(tmpdir) / "chrome-probe.png"
        chrome_profile = Path(tmpdir) / "chrome-profile"
        result = subprocess.run(
            [
                CHROME_BIN,
                "--headless=new",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-crash-reporter",
                "--disable-breakpad",
                "--hide-scrollbars",
                "--no-first-run",
                "--no-default-browser-check",
                "--no-sandbox",
                f"--user-data-dir={chrome_profile}",
                "--window-size=800,600",
                f"--screenshot={probe_path}",
                "about:blank",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and probe_path.exists():
            return True, ""
        return False, (result.stderr or result.stdout or "Headless Chrome probe failed.").strip()


class TestDashboardFiles:
    def test_index_html_exists(self):
        assert (DASHBOARD_DIR / "index.html").exists()

    def test_assets_dir_exists(self):
        assert (DASHBOARD_DIR / "assets").exists()
        assert (DASHBOARD_DIR / "assets").is_dir()

    def test_js_bundle_exists(self):
        js_files = list((DASHBOARD_DIR / "assets").glob("*.js"))
        assert len(js_files) >= 1, "No JS bundle found in assets/"

    def test_dashboard_is_code_split(self):
        js_files = list((DASHBOARD_DIR / "assets").glob("*.js"))
        assert len(js_files) >= 2, "Expected multiple JS chunks so chart-heavy UI stays split."

    def test_largest_js_chunk_stays_below_warning_budget(self):
        js_sizes = [path.stat().st_size for path in (DASHBOARD_DIR / "assets").glob("*.js")]
        assert js_sizes
        assert max(js_sizes) < 500_000, "Largest JS chunk regressed above the Vite large-chunk warning threshold."

    def test_css_bundle_exists(self):
        css_files = list((DASHBOARD_DIR / "assets").glob("*.css"))
        assert len(css_files) >= 1, "No CSS bundle found in assets/"

    def test_index_html_structure(self):
        html = (DASHBOARD_DIR / "index.html").read_text()
        assert "OA Dashboard" in html
        assert "<div id=\"root\">" in html

    def test_index_references_assets(self):
        html = (DASHBOARD_DIR / "index.html").read_text()
        assert "assets/" in html

    def test_no_private_data(self):
        private_terms = ["jingshi", "motus_ssd", "clawd", "clawdbot", "mission-control"]
        for file_path in DASHBOARD_DIR.rglob("*"):
            if file_path.is_file() and file_path.suffix in (".html", ".css"):
                content = file_path.read_text().lower()
                for term in private_terms:
                    assert term not in content, f"Private term '{term}' found in {file_path.name}"
        for file_path in (DASHBOARD_DIR / "assets").glob("*.js"):
            content = file_path.read_text().lower()
            for term in private_terms:
                assert term not in content, f"Private term '{term}' found in {file_path.name}"

    def test_cron_breakdown_labels_exist_in_bundle(self):
        bundle = "\n".join(file_path.read_text() for file_path in (DASHBOARD_DIR / "assets").glob("*.js"))
        assert "Expected Slots" in bundle
        assert "Observed Slots" in bundle
        assert "Unsupported Schedules" in bundle
        assert "Slot Matching Policy" in bundle
        assert "Per Job Breakdown" in bundle
        assert "Expected vs Seen" in bundle
        assert "Status Detail" in bundle
        assert "Missed Slot Times" in bundle

    @pytest.mark.skipif(CHROME_BIN is None or Image is None or ImageStat is None, reason="Headless Chrome and Pillow are required for dashboard screenshot smoke coverage.")
    def test_dashboard_visual_smoke_screenshot(self):
        supported, reason = _chrome_supports_headless_screenshot()
        if not supported:
            pytest.skip(f"Headless Chrome cannot capture screenshots in this environment: {reason.splitlines()[0]}")

        with tempfile.TemporaryDirectory() as tmpdir, _serve_visual_dashboard_fixture(tmpdir) as url:
            screenshot_path = Path(tmpdir) / "dashboard-smoke.png"
            dom_html = ""
            overall_dark = 0
            overall_accent = 0
            chart_accent = 0
            chart_stddev = 0.0
            details_accent = 0
            details_stddev = 0.0

            for attempt in range(3):
                chrome_profile = Path(tmpdir) / f"chrome-profile-{attempt}"
                result = subprocess.run(
                    [
                        CHROME_BIN,
                        "--headless=new",
                        "--disable-gpu",
                        "--disable-background-networking",
                        "--disable-dev-shm-usage",
                        "--hide-scrollbars",
                        "--force-device-scale-factor=1",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--no-sandbox",
                        f"--user-data-dir={chrome_profile}",
                        "--window-size=1600,2200",
                        f"--screenshot={screenshot_path}",
                        "--virtual-time-budget=5000",
                        "--run-all-compositor-stages-before-draw",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert result.returncode == 0, result.stderr or result.stdout
                assert screenshot_path.exists()

                dump_dom = subprocess.run(
                    [
                        CHROME_BIN,
                        "--headless=new",
                        "--disable-gpu",
                        "--disable-background-networking",
                        "--disable-dev-shm-usage",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--no-sandbox",
                        f"--user-data-dir={chrome_profile}-dom",
                        "--virtual-time-budget=5000",
                        "--dump-dom",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert dump_dom.returncode == 0, dump_dom.stderr or dump_dom.stdout
                dom_html = dump_dom.stdout
                assert "Loading</p>" not in dom_html
                assert "Per Job Breakdown" in dom_html
                assert "Expected vs Seen" in dom_html
                assert "Slot Matching Policy" in dom_html

                with Image.open(screenshot_path) as image:
                    assert image.size == (1600, 2200)

                    sample = image.convert("RGB").resize((400, 550))
                    overall_dark = _count_dark_pixels(sample)
                    overall_accent = _count_accent_pixels(sample)
                    chart_crop = sample.crop((82, 62, 360, 176))
                    details_crop = sample.crop((68, 150, 360, 420))
                    chart_accent = _count_accent_pixels(chart_crop)
                    chart_stddev = ImageStat.Stat(chart_crop.convert("L")).stddev[0]
                    details_accent = _count_accent_pixels(details_crop)
                    details_stddev = ImageStat.Stat(details_crop.convert("L")).stddev[0]

                if (
                    overall_accent > 3000
                    and chart_stddev > 10
                    and chart_accent > 1200
                    and details_stddev > 10
                    and details_accent > 500
                    and overall_dark > 100
                ):
                    break
            else:
                pytest.fail(
                    "Rendered dashboard screenshot did not reach the expected visual thresholds after 3 attempts: "
                    f"overall_accent={overall_accent}, chart_stddev={chart_stddev}, chart_accent={chart_accent}, "
                    f"details_stddev={details_stddev}, details_accent={details_accent}, overall_dark={overall_dark}"
                )
