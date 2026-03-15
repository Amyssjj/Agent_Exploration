"""
Lightweight tracing module — OTel-compatible, zero external deps.
Follows W3C Trace Context conventions. Writes spans to SQLite.

Usage:
    from oa.core.tracing import Tracer

    tracer = Tracer(service="my_pipeline", db_path="data/monitor.db")
    with tracer.span("Data Collection") as span:
        span.set_attribute("rows", 42)
        with tracer.span("DB Insert") as child:
            child.set_attribute("db.system", "sqlite")
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _generate_trace_id() -> str:
    """Generate a 32-char hex trace ID (128-bit, W3C standard)."""
    return uuid.uuid4().hex


def _generate_span_id() -> str:
    """Generate a 16-char hex span ID (64-bit, W3C standard)."""
    return uuid.uuid4().hex[:16]


def _parse_traceparent(traceparent: str) -> tuple[str, str] | None:
    """Parse W3C traceparent header: 00-{trace_id}-{parent_span_id}-{flags}."""
    if not traceparent:
        return None
    parts = traceparent.strip().split("-")
    if len(parts) >= 3:
        return parts[1], parts[2]
    return None


class Span:
    """A single trace span with timing and attributes."""

    def __init__(self, name: str, trace_id: str, span_id: str,
                 parent_span_id: str | None, service: str):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.service = service
        self.status = "ok"
        self.start_time = datetime.now(timezone.utc)
        self.end_time: datetime | None = None
        self.duration_ms: float | None = None
        self.attributes: dict[str, Any] = {}
        self.events: list[dict] = []
        self._start_ns = time.monotonic_ns()

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        """Record an event within this span."""
        self.events.append({
            "name": name,
            "time": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })

    def set_status(self, status: str, message: str | None = None) -> None:
        """Set span status: 'ok', 'error', or 'unset'."""
        self.status = status
        if message:
            self.set_attribute("error.message", message)

    def end(self) -> None:
        """End the span and calculate duration."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (time.monotonic_ns() - self._start_ns) / 1_000_000

    def to_dict(self) -> dict:
        """Serialize span for storage."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "service": self.service,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
            "attributes": json.dumps(self.attributes) if self.attributes else None,
            "events": json.dumps(self.events) if self.events else None,
        }


class Tracer:
    """Lightweight tracer that writes spans to SQLite.

    Reads TRACEPARENT env var for upstream trace linking.
    Manages a span stack for automatic parent-child relationships.
    """

    def __init__(self, service: str, db_path: Path | str):
        self.service = service
        self.db_path = Path(db_path)
        self._span_stack: list[Span] = []
        self._spans: list[Span] = []

        # Parse upstream trace context
        traceparent = os.environ.get("TRACEPARENT", "")
        parsed = _parse_traceparent(traceparent)
        if parsed:
            self.trace_id, self._root_parent_id = parsed
        else:
            self.trace_id = _generate_trace_id()
            self._root_parent_id = None

    @contextmanager
    def span(self, name: str, attributes: dict | None = None):
        """Context manager for creating a child span.

        Usage:
            with tracer.span("Step Name") as s:
                s.set_attribute("key", "value")
        """
        if self._span_stack:
            parent_id = self._span_stack[-1].span_id
        else:
            parent_id = self._root_parent_id

        s = Span(
            name=name,
            trace_id=self.trace_id,
            span_id=_generate_span_id(),
            parent_span_id=parent_id,
            service=self.service,
        )

        if attributes:
            for k, v in attributes.items():
                s.set_attribute(k, v)

        self._span_stack.append(s)
        try:
            yield s
        except Exception as e:
            s.set_status("error", str(e))
            raise
        finally:
            s.end()
            self._span_stack.pop()
            self._spans.append(s)

    def flush(self) -> int:
        """Write all collected spans to SQLite. Returns count written."""
        if not self._spans:
            return 0

        db = sqlite3.connect(str(self.db_path))
        db.execute("PRAGMA journal_mode=WAL")

        count = 0
        for s in self._spans:
            d = s.to_dict()
            db.execute(
                """INSERT OR REPLACE INTO spans
                (span_id, trace_id, parent_span_id, name, service, status,
                 start_time, end_time, duration_ms, attributes, events)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (d["span_id"], d["trace_id"], d["parent_span_id"],
                 d["name"], d["service"], d["status"],
                 d["start_time"], d["end_time"], d["duration_ms"],
                 d["attributes"], d["events"]),
            )
            count += 1

        db.commit()
        db.close()
        self._spans.clear()
        return count

    def get_traceparent(self) -> str:
        """Generate a TRACEPARENT string for passing to child processes."""
        current_span_id = (
            self._span_stack[-1].span_id if self._span_stack else _generate_span_id()
        )
        return f"00-{self.trace_id}-{current_span_id}-01"
