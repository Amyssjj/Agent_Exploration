"""Tests for the OTel-compatible tracing module."""
import sqlite3
import tempfile
from pathlib import Path

from oa.core.schema import create_schema
from oa.core.tracing import Tracer


class TestTracer:
    def _make_db(self, tmpdir: str) -> Path:
        db_path = Path(tmpdir) / "test.db"
        create_schema(db_path)
        return db_path

    def test_basic_span(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = self._make_db(tmpdir)
            tracer = Tracer(service="test", db_path=db_path)

            with tracer.span("root") as s:
                s.set_attribute("key", "value")

            count = tracer.flush()
            assert count == 1

            db = sqlite3.connect(str(db_path))
            row = db.execute("SELECT name, service, status FROM spans").fetchone()
            assert row[0] == "root"
            assert row[1] == "test"
            assert row[2] == "ok"
            db.close()

    def test_nested_spans(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = self._make_db(tmpdir)
            tracer = Tracer(service="test", db_path=db_path)

            with tracer.span("parent") as parent:
                with tracer.span("child") as child:
                    child.set_attribute("level", 2)

            count = tracer.flush()
            assert count == 2

            db = sqlite3.connect(str(db_path))
            rows = db.execute(
                "SELECT name, parent_span_id FROM spans ORDER BY start_time"
            ).fetchall()

            # Child's parent should be the parent span
            parent_row = [r for r in rows if r[0] == "parent"][0]
            child_row = [r for r in rows if r[0] == "child"][0]
            assert child_row[1] is not None  # has parent
            db.close()

    def test_error_span(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = self._make_db(tmpdir)
            tracer = Tracer(service="test", db_path=db_path)

            try:
                with tracer.span("failing"):
                    raise ValueError("test error")
            except ValueError:
                pass

            tracer.flush()

            db = sqlite3.connect(str(db_path))
            row = db.execute("SELECT status FROM spans").fetchone()
            assert row[0] == "error"
            db.close()

    def test_trace_id_consistency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = self._make_db(tmpdir)
            tracer = Tracer(service="test", db_path=db_path)

            with tracer.span("a"):
                with tracer.span("b"):
                    pass

            tracer.flush()

            db = sqlite3.connect(str(db_path))
            trace_ids = db.execute("SELECT DISTINCT trace_id FROM spans").fetchall()
            assert len(trace_ids) == 1  # all spans share same trace
            db.close()

    def test_get_traceparent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = self._make_db(tmpdir)
            tracer = Tracer(service="test", db_path=db_path)
            tp = tracer.get_traceparent()
            assert tp.startswith("00-")
            parts = tp.split("-")
            assert len(parts) == 4
            assert len(parts[1]) == 32  # trace_id
            assert len(parts[2]) == 16  # span_id

    def test_flush_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = self._make_db(tmpdir)
            tracer = Tracer(service="test", db_path=db_path)
            count = tracer.flush()
            assert count == 0

    def test_span_duration(self):
        import time
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = self._make_db(tmpdir)
            tracer = Tracer(service="test", db_path=db_path)

            with tracer.span("timed"):
                time.sleep(0.01)

            tracer.flush()

            db = sqlite3.connect(str(db_path))
            row = db.execute("SELECT duration_ms FROM spans").fetchone()
            assert row[0] > 0  # should have measurable duration
            db.close()
