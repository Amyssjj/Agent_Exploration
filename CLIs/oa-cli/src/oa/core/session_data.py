"""Helpers for reading activity timestamps from OpenClaw session files."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_TIMESTAMP_KEYS = {
    "timestamp",
    "ts",
    "createdAt",
    "updatedAt",
    "startedAt",
    "completedAt",
    "lastConnectedAt",
    "savedAt",
    "runAtMs",
}


@dataclass
class SessionFileInfo:
    """Activity summary extracted from one session file."""

    activity_dates: set[str] = field(default_factory=set)
    latest_by_date: dict[str, str] = field(default_factory=dict)
    last_active: str | None = None


def inspect_session_file(path: Path) -> SessionFileInfo:
    """Read a session file and summarize activity dates and timestamps."""
    info = SessionFileInfo()
    latest_dt: datetime | None = None

    for dt in _iter_session_datetimes(path):
        iso_ts = dt.isoformat()
        date_str = dt.strftime("%Y-%m-%d")
        info.activity_dates.add(date_str)
        if info.latest_by_date.get(date_str, "") < iso_ts:
            info.latest_by_date[date_str] = iso_ts
        if latest_dt is None or dt > latest_dt:
            latest_dt = dt

    if latest_dt is not None:
        info.last_active = latest_dt.isoformat()
        return info

    try:
        fallback_dt = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return info

    fallback_iso = fallback_dt.isoformat()
    fallback_date = fallback_dt.strftime("%Y-%m-%d")
    info.activity_dates.add(fallback_date)
    info.latest_by_date[fallback_date] = fallback_iso
    info.last_active = fallback_iso
    return info


def _iter_session_datetimes(path: Path):
    if not path.exists() or not path.is_file():
        return

    try:
        with open(path, encoding="utf-8") as f:
            if path.suffix == ".jsonl":
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    yield from _iter_payload_datetimes(payload)
                return

            try:
                payload = json.load(f)
            except json.JSONDecodeError:
                return
    except OSError:
        return

    yield from _iter_payload_datetimes(payload)


def _iter_payload_datetimes(payload: Any):
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in _TIMESTAMP_KEYS:
                dt = _parse_datetime(value)
                if dt is not None:
                    yield dt
            if isinstance(value, (dict, list)):
                yield from _iter_payload_datetimes(value)
        return

    if isinstance(payload, list):
        for item in payload:
            yield from _iter_payload_datetimes(item)


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, (int, float)):
        seconds = value / 1000 if abs(value) >= 100_000_000_000 else value
        try:
            return datetime.fromtimestamp(seconds)
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
        if dt.tzinfo is not None:
            return dt.astimezone().replace(tzinfo=None)
        return dt

    return None
