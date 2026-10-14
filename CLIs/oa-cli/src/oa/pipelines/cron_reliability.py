"""G1: Cron Reliability Pipeline — tracks observed cron run success rates."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import Metric, Pipeline

if TYPE_CHECKING:
    from oa.core.config import ProjectConfig


class CronReliabilityPipeline(Pipeline):
    """Built-in pipeline: reads OpenClaw cron JSONL logs and computes success rates."""

    goal_id = "cron_reliability"
    _LATE_MATCH_TOLERANCE_MINUTES = 5
    _LATE_MATCH_TOLERANCE = timedelta(minutes=_LATE_MATCH_TOLERANCE_MINUTES)
    _STATUS_ORDER = ("success", "timeout", "delivery_error", "failure", "unknown")
    _CRON_MACROS = {
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@hourly": "0 * * * *",
    }
    _MONTH_NAMES = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    _WEEKDAY_NAMES = {
        "sun": 0,
        "mon": 1,
        "tue": 2,
        "wed": 3,
        "thu": 4,
        "fri": 5,
        "sat": 6,
    }

    def collect(self, date: str, config: "ProjectConfig") -> list[Metric]:
        from oa.core.tracing import Tracer

        cron_dir = config.openclaw_home / "cron"
        jobs_file = cron_dir / "jobs.json"
        runs_dir = cron_dir / "runs"
        tracer = Tracer(service="g1_cron_reliability", db_path=config.db_path)

        with tracer.span("G1: Cron Reliability", {"goal": "G1", "date": date}) as root:
            enabled_jobs = self._read_enabled_jobs(jobs_file)
            runs_by_job = self._collect_runs(runs_dir, date, enabled_jobs)
            schedule_summary = self._build_schedule_summary(date, enabled_jobs, runs_by_job)

            observed_jobs = len(runs_by_job)
            total_runs = 0
            total_success = 0
            total_failed = 0
            total_unknown = 0
            per_job: dict[str, dict[str, Any]] = {}
            normalized_rows: list[dict[str, Any]] = []

            with tracer.span("Normalize Run History", {"jobs_file": str(jobs_file), "runs_dir": str(runs_dir)}) as hist:
                job_ids = sorted(set(enabled_jobs.keys()) | set(runs_by_job.keys()))
                for job_id in job_ids:
                    job_meta = enabled_jobs.get(job_id, {})
                    payload = runs_by_job.get(job_id, {"runs": []})
                    job_name = payload.get("job_name") or job_meta.get("name", job_id)
                    runs = payload.get("runs", [])
                    success = sum(1 for r in runs if r["normalized_status"] == "success")
                    failed = sum(1 for r in runs if r["normalized_status"] == "failure")
                    unknown = sum(1 for r in runs if r["normalized_status"] == "unknown")
                    detail_counts = self._status_counts(runs, "status")
                    schedule_job = schedule_summary["per_job"].get(job_id, {})
                    total = len(runs)
                    success_rate_denominator = max(total, int(schedule_job.get("expected_slots") or 0))
                    avg_duration = round(
                        sum(r.get("duration_ms", 0) for r in runs if r.get("duration_ms") is not None) /
                        max(1, sum(1 for r in runs if r.get("duration_ms") is not None)),
                        1,
                    ) if any(r.get("duration_ms") is not None for r in runs) else None

                    per_job[job_name] = {
                        "job_id": job_id,
                        "total": total,
                        "success": success,
                        "failed": failed,
                        "unknown": unknown,
                        "status_details": detail_counts,
                        "rate": round(success / success_rate_denominator * 100, 1) if success_rate_denominator > 0 else 0,
                        "avg_duration_ms": avg_duration,
                        "expected_slots": int(schedule_job.get("expected_slots") or 0),
                        "observed_slots": int(schedule_job.get("observed_slots") or 0),
                        "exact_matches": int(schedule_job.get("exact_matches") or 0),
                        "late_matches": int(schedule_job.get("late_matches") or 0),
                        "missed": int(schedule_job.get("missed") or 0),
                        "missed_slot_times": list(schedule_job.get("missed_slot_times") or []),
                        "unexpected_runs": int(schedule_job.get("unexpected_runs") or 0),
                        "supported_schedule": bool(schedule_job.get("supported_schedule")),
                        "unsupported_reason": schedule_job.get("unsupported_reason"),
                        "phase_policy": schedule_job.get("phase_policy"),
                    }
                    total_runs += total
                    total_success += success
                    total_failed += failed
                    total_unknown += unknown
                    normalized_rows.extend(runs)

                hist.set_attribute("enabled_jobs", len(enabled_jobs))
                hist.set_attribute("observed_jobs", observed_jobs)
                hist.set_attribute("observed_runs", total_runs)
                hist.set_attribute("expected_slots", schedule_summary["expected_slots"])
                hist.set_attribute("missed_slots", schedule_summary["missed"])

            with tracer.span("Compute Metrics") as compute:
                success_rate_denominator = max(total_runs, schedule_summary["expected_slots"])
                success_rate = round(total_success / success_rate_denominator * 100, 1) if success_rate_denominator > 0 else 0.0
                mode = "scheduled_mode" if enabled_jobs else ("observed_only" if total_runs > 0 else "no_data")
                detail_counts = self._status_counts(normalized_rows, "status")
                failure_types = {name: count for name, count in detail_counts.items() if self._status_group(name) == "failure"}
                compute.set_attribute("success_rate", success_rate)
                compute.set_attribute("mode", mode)
                compute.set_attribute("failed_runs", total_failed)
                compute.set_attribute("expected_slots", schedule_summary["expected_slots"])
                compute.set_attribute("missed_slots", schedule_summary["missed"])

            with tracer.span("Write cron_runs DB"):
                self._write_cron_runs(config.db_path, date, normalized_rows)

            root.set_attribute("success_rate", success_rate)
            root.set_attribute("failed_runs", total_failed)
            root.set_attribute("unknown_runs", total_unknown)
            root.set_attribute("mode", mode)
            root.set_attribute("expected_slots", schedule_summary["expected_slots"])
            root.set_attribute("missed_slots", schedule_summary["missed"])

        tracer.flush()
        return [
            Metric(
                "success_rate",
                success_rate,
                unit="%",
                breakdown={
                    "mode": mode,
                    "per_job": per_job,
                    "enabled_jobs": len(enabled_jobs),
                    "observed_jobs": observed_jobs,
                    "total_runs": total_runs,
                    "success": total_success,
                    "failed": total_failed,
                    "unknown": total_unknown,
                    "expected_slots": schedule_summary["expected_slots"],
                    "observed_slots": schedule_summary["observed_slots"],
                    "exact_matches": schedule_summary["exact_matches"],
                    "late_matches": schedule_summary["late_matches"],
                    "missed": schedule_summary["missed"],
                    "missed_slots": schedule_summary["missed_slots"],
                    "unexpected_runs": schedule_summary["unexpected_runs"],
                    "unsupported_schedules": schedule_summary["unsupported_schedules"],
                    "success_rate_denominator": success_rate_denominator,
                    "late_tolerance_minutes": self._LATE_MATCH_TOLERANCE_MINUTES,
                    "slot_matching_policy": self._slot_matching_policy(),
                    "no_anchor_every_policy": self._no_anchor_every_policy(),
                    "unanchored_every_jobs": schedule_summary["unanchored_every_jobs"],
                    "status_details": detail_counts,
                    "failure_types": failure_types,
                    "note": schedule_summary["note"],
                },
            ),
            Metric(
                "failed_runs",
                float(total_failed),
                unit="count",
                breakdown={
                    "mode": mode,
                    "total_runs": total_runs,
                    "failed": total_failed,
                    "success": total_success,
                    "unknown": total_unknown,
                    "expected_slots": schedule_summary["expected_slots"],
                    "observed_slots": schedule_summary["observed_slots"],
                    "missed": schedule_summary["missed"],
                    "unexpected_runs": schedule_summary["unexpected_runs"],
                },
            ),
            Metric(
                "unknown_runs",
                float(total_unknown),
                unit="count",
                breakdown={
                    "mode": mode,
                    "total_runs": total_runs,
                    "failed": total_failed,
                    "success": total_success,
                    "unknown": total_unknown,
                    "expected_slots": schedule_summary["expected_slots"],
                    "observed_slots": schedule_summary["observed_slots"],
                    "missed": schedule_summary["missed"],
                    "unexpected_runs": schedule_summary["unexpected_runs"],
                },
            ),
        ]

    def _read_enabled_jobs(self, jobs_file: Path) -> dict[str, dict]:
        if not jobs_file.exists():
            return {}
        try:
            with open(jobs_file, encoding="utf-8") as f:
                jobs_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

        enabled_jobs: dict[str, dict] = {}
        for job in jobs_data.get("jobs", []):
            if not job.get("enabled", True):
                continue
            job_id = job.get("id")
            if not job_id:
                continue
            schedule = job.get("schedule", {})
            enabled_jobs[job_id] = {
                "name": job.get("name", job_id),
                "schedule_kind": schedule.get("kind", "unknown"),
                "schedule": schedule,
            }
        return enabled_jobs

    def _build_schedule_summary(self, date: str, enabled_jobs: dict[str, dict], runs_by_job: dict[str, dict[str, Any]]) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "expected_slots": 0,
            "observed_slots": 0,
            "exact_matches": 0,
            "late_matches": 0,
            "missed": 0,
            "missed_slots": [],
            "unexpected_runs": 0,
            "unsupported_schedules": [],
            "unanchored_every_jobs": [],
            "per_job": {},
            "supported_jobs": 0,
            "note": "jobs.json empty or no enabled cron jobs; using observed runs only",
        }
        if not enabled_jobs:
            return summary

        for job_id, job_meta in enabled_jobs.items():
            job_name = job_meta.get("name", job_id)
            expected_slots, unsupported_reason = self._expected_slots_for_job(date, job_meta)
            runs = runs_by_job.get(job_id, {}).get("runs", [])
            job_summary = {
                "expected_slots": 0,
                "observed_slots": 0,
                "exact_matches": 0,
                "late_matches": 0,
                "missed": 0,
                "missed_slot_times": [],
                "unexpected_runs": 0,
                "supported_schedule": False,
                "phase_policy": None,
            }

            if expected_slots is None:
                job_summary["unsupported_reason"] = unsupported_reason
                summary["unsupported_schedules"].append({
                    "job_id": job_id,
                    "cron_name": job_name,
                    "schedule_kind": job_meta.get("schedule_kind"),
                    "expr": (job_meta.get("schedule") or {}).get("expr"),
                    "reason": unsupported_reason,
                })
                summary["per_job"][job_id] = job_summary
                continue

            summary["supported_jobs"] += 1
            job_summary["supported_schedule"] = True
            job_summary["expected_slots"] = len(expected_slots)
            if self._uses_unanchored_every(job_meta):
                job_summary["phase_policy"] = self._no_anchor_every_policy()
                summary["unanchored_every_jobs"].append({"cron_name": job_name, "job_id": job_id})
            expected_keys = [self._slot_key(slot) for slot in expected_slots]
            expected_by_key = {self._slot_key(slot): slot for slot in expected_slots}
            match_summary = self._match_runs_to_expected_slots(runs, expected_slots, expected_by_key)
            observed_keys = match_summary["matched_keys"]
            unexpected_runs = match_summary["unexpected_runs"]

            missed_keys = [key for key in expected_keys if key not in observed_keys]
            missed_slot_times = [self._slot_label(expected_by_key[key]) for key in missed_keys]
            job_summary["observed_slots"] = len(observed_keys)
            job_summary["exact_matches"] = match_summary["exact_matches"]
            job_summary["late_matches"] = match_summary["late_matches"]
            job_summary["missed"] = len(missed_keys)
            job_summary["missed_slot_times"] = missed_slot_times
            job_summary["unexpected_runs"] = unexpected_runs
            summary["per_job"][job_id] = job_summary

            summary["expected_slots"] += len(expected_slots)
            summary["observed_slots"] += len(observed_keys)
            summary["exact_matches"] += match_summary["exact_matches"]
            summary["late_matches"] += match_summary["late_matches"]
            summary["missed"] += len(missed_keys)
            summary["unexpected_runs"] += unexpected_runs
            summary["missed_slots"].extend(
                {"cron_name": job_name, "job_id": job_id, "slot_time": slot_time}
                for slot_time in missed_slot_times
            )

        policy_notes = [self._slot_matching_policy_note()]
        if summary["unanchored_every_jobs"]:
            policy_notes.append(self._no_anchor_every_policy_note())
        policy_text = "; ".join(policy_notes)

        if summary["supported_jobs"] == 0:
            summary["note"] = "expected-slot reasoning currently supports cron schedules and every schedules >=60s; using observed runs only"
        elif summary["unsupported_schedules"]:
            summary["note"] = (
                "expected-slot reasoning enabled for supported cron/every schedules; "
                f"{policy_text}; unsupported schedules are listed separately"
            )
        elif summary["expected_slots"] == 0:
            summary["note"] = f"expected-slot reasoning enabled; {policy_text}; no slots were scheduled for this date"
        else:
            summary["note"] = (
                "expected-slot reasoning enabled from jobs.json schedules; "
                f"{policy_text}"
            )
        return summary

    def _expected_slots_for_job(self, date: str, job_meta: dict[str, Any]) -> tuple[list[datetime] | None, str | None]:
        schedule_kind = str(job_meta.get("schedule_kind") or "unknown").lower()
        schedule = job_meta.get("schedule") or {}
        if schedule_kind == "cron":
            expr = self._coerce_text(schedule.get("expr"))
            if not expr:
                return None, "cron schedule missing expr"
            slots = self._expand_cron_slots(date, expr)
            if slots is None:
                return None, f"unsupported cron expr: {expr}"
            return slots, None
        if schedule_kind == "every":
            every_ms = self._safe_int(schedule.get("everyMs"))
            if every_ms is None or every_ms <= 0:
                return None, "every schedule missing valid everyMs"
            return self._expand_every_slots(date, every_ms, schedule.get("anchorMs"))
        return None, f"schedule.kind={schedule_kind} not supported"

    def _expand_every_slots(self, date: str, every_ms: int, anchor_ms: Any) -> tuple[list[datetime] | None, str | None]:
        if every_ms < 60_000:
            return None, "every schedule under 60000ms not supported at current minute slot precision"

        if anchor_ms is None:
            # Keep a stable phase for unanchored every schedules by treating them as anchorMs=0.
            raw_anchor_ms = 0
        else:
            raw_anchor_ms = self._safe_int(anchor_ms)
            if raw_anchor_ms is None:
                return None, "every schedule has invalid anchorMs"

        try:
            anchor_dt = datetime.fromtimestamp(raw_anchor_ms / 1000).replace(microsecond=0)
            step = timedelta(milliseconds=every_ms)
        except (OverflowError, OSError, ValueError):
            return None, "every schedule has invalid timing values"

        day_start = datetime.strptime(date, "%Y-%m-%d")
        day_end = day_start + timedelta(days=1)
        current = anchor_dt

        if current < day_start:
            current += step * ((day_start - current) // step)
            while current < day_start:
                current += step

        slots: list[datetime] = []
        while current < day_end:
            if current >= day_start:
                slots.append(current)
            current += step
        return slots, None

    def _expand_cron_slots(self, date: str, expr: str) -> list[datetime] | None:
        normalized_expr = self._CRON_MACROS.get(expr.strip().lower(), expr.strip())
        fields = normalized_expr.split()
        if len(fields) != 5:
            return None

        minutes = self._parse_cron_field(fields[0], 0, 59)
        hours = self._parse_cron_field(fields[1], 0, 23)
        day_of_month = self._parse_cron_field(fields[2], 1, 31, allow_question=True)
        months = self._parse_cron_field(fields[3], 1, 12, names=self._MONTH_NAMES)
        day_of_week = self._parse_cron_field(fields[4], 0, 7, names=self._WEEKDAY_NAMES, allow_question=True, sunday_is_zero=True)
        if not all((minutes, hours, day_of_month, months, day_of_week)):
            return None

        minute_values, _ = minutes
        hour_values, _ = hours
        day_values, day_is_any = day_of_month
        month_values, _ = months
        weekday_values, weekday_is_any = day_of_week

        target_dt = datetime.strptime(date, "%Y-%m-%d")
        if not self._cron_matches_date(target_dt, day_values, day_is_any, month_values, weekday_values, weekday_is_any):
            return []

        slots: list[datetime] = []
        for hour in sorted(hour_values):
            for minute in sorted(minute_values):
                slots.append(target_dt.replace(hour=hour, minute=minute, second=0, microsecond=0))
        return slots

    def _parse_cron_field(
        self,
        field: str,
        minimum: int,
        maximum: int,
        names: dict[str, int] | None = None,
        allow_question: bool = False,
        sunday_is_zero: bool = False,
    ) -> tuple[set[int], bool] | None:
        text = (field or "").strip().lower()
        if not text:
            return None
        if text == "?" and not allow_question:
            return None

        is_any = text in {"*", "?"}
        values: set[int] = set()
        for raw_part in text.split(","):
            part = raw_part.strip().lower()
            if not part:
                return None
            if part == "?":
                if not allow_question:
                    return None
                part = "*"

            if "/" in part:
                base, step_text = part.split("/", 1)
                try:
                    step = int(step_text)
                except ValueError:
                    return None
                if step <= 0:
                    return None
            else:
                base = part
                step = 1

            if base in {"", "*"}:
                start = minimum
                end = maximum
            elif "-" in base:
                left, right = base.split("-", 1)
                start = self._cron_value(left, names)
                end = self._cron_value(right, names)
                if start is None or end is None or start > end:
                    return None
            else:
                single = self._cron_value(base, names)
                if single is None:
                    return None
                start = single
                end = single

            for value in range(start, end + 1, step):
                normalized = 0 if sunday_is_zero and value == 7 else value
                if normalized < minimum or normalized > maximum:
                    return None
                values.add(normalized)

        return values, is_any

    def _cron_value(self, token: str, names: dict[str, int] | None = None) -> int | None:
        value = token.strip().lower()
        if not value:
            return None
        if names and value[:3] in names and not value.isdigit():
            return names[value[:3]]
        try:
            return int(value)
        except ValueError:
            return None

    def _cron_matches_date(
        self,
        target_dt: datetime,
        day_values: set[int],
        day_is_any: bool,
        month_values: set[int],
        weekday_values: set[int],
        weekday_is_any: bool,
    ) -> bool:
        if target_dt.month not in month_values:
            return False

        day_match = target_dt.day in day_values
        weekday_match = ((target_dt.weekday() + 1) % 7) in weekday_values
        if day_is_any and weekday_is_any:
            return True
        if day_is_any:
            return weekday_match
        if weekday_is_any:
            return day_match
        return day_match or weekday_match

    def _slot_key(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M")

    def _slot_label(self, value: datetime) -> str:
        return value.strftime("%H:%M:%S")

    def _slot_matching_policy(self) -> str:
        return (
            "one-to-one per job: exact minute first; otherwise match a single unmatched expected slot up to "
            f"{self._LATE_MATCH_TOLERANCE_MINUTES} minutes earlier; early runs never match future slots; "
            "ambiguous late runs stay unexpected"
        )

    def _slot_matching_policy_note(self) -> str:
        return f"exact minute matches first, then up to {self._LATE_MATCH_TOLERANCE_MINUTES} minutes late tolerance for unique matches"

    def _no_anchor_every_policy(self) -> str:
        return (
            "schedule.kind=every without anchorMs is treated as anchorMs=0, "
            "so slots use the Unix epoch phase in local wall-clock time at minute precision"
        )

    def _no_anchor_every_policy_note(self) -> str:
        return "missing every anchorMs uses Unix epoch phase (anchorMs=0)"

    def _uses_unanchored_every(self, job_meta: dict[str, Any]) -> bool:
        schedule_kind = str(job_meta.get("schedule_kind") or "unknown").lower()
        schedule = job_meta.get("schedule") or {}
        return schedule_kind == "every" and schedule.get("anchorMs") is None

    def _match_runs_to_expected_slots(
        self,
        runs: list[dict[str, Any]],
        expected_slots: list[datetime],
        expected_by_key: dict[str, datetime],
    ) -> dict[str, Any]:
        matched_keys: set[str] = set()
        match_summary = {
            "matched_keys": matched_keys,
            "unexpected_runs": 0,
            "exact_matches": 0,
            "late_matches": 0,
        }

        for run in sorted(runs, key=self._run_match_sort_key):
            matched_key, match_type = self._match_run_to_expected_slot(run, expected_slots, expected_by_key, matched_keys)
            if matched_key is None:
                match_summary["unexpected_runs"] += 1
                continue
            matched_keys.add(matched_key)
            if match_type == "exact":
                match_summary["exact_matches"] += 1
            elif match_type == "late":
                match_summary["late_matches"] += 1

        return match_summary

    def _run_match_sort_key(self, run: dict[str, Any]) -> tuple[Any, ...]:
        observed_dt = run.get("observed_slot_dt")
        return (
            observed_dt is None,
            observed_dt or datetime.max,
            run.get("run_at_ms") if run.get("run_at_ms") is not None else float("inf"),
            run.get("slot_time") or "",
            run.get("run_id") or "",
        )

    def _match_run_to_expected_slot(
        self,
        run: dict[str, Any],
        expected_slots: list[datetime],
        expected_by_key: dict[str, datetime],
        matched_keys: set[str],
    ) -> tuple[str | None, str | None]:
        observed_key = run.get("observed_slot_key")
        if observed_key and observed_key in expected_by_key:
            if observed_key in matched_keys:
                return None, None
            return observed_key, "exact"

        observed_dt = run.get("observed_slot_dt")
        if not isinstance(observed_dt, datetime):
            return None, None

        late_window_start = observed_dt - self._LATE_MATCH_TOLERANCE
        late_candidates = [
            self._slot_key(slot)
            for slot in expected_slots
            if late_window_start <= slot < observed_dt and self._slot_key(slot) not in matched_keys
        ]
        if len(late_candidates) != 1:
            return None, None
        return late_candidates[0], "late"

    def _collect_runs(self, runs_dir: Path, date: str, enabled_jobs: dict[str, dict]) -> dict[str, dict[str, Any]]:
        runs_by_job: dict[str, dict[str, Any]] = {}
        if not runs_dir.exists():
            return runs_by_job

        candidate_ids = set(enabled_jobs.keys())
        run_files = []
        if candidate_ids:
            for job_id in candidate_ids:
                run_files.append(runs_dir / f"{job_id}.jsonl")
        else:
            run_files.extend(sorted(runs_dir.glob("*.jsonl")))

        for jsonl_file in run_files:
            if not jsonl_file.exists():
                continue
            file_job_id = jsonl_file.stem
            try:
                with open(jsonl_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        normalized = self._normalize_entry(entry, file_job_id, date, enabled_jobs)
                        if not normalized:
                            continue
                        payload = runs_by_job.setdefault(
                            normalized["job_id"],
                            {"job_name": normalized["cron_name"], "runs": []},
                        )
                        payload["job_name"] = normalized["cron_name"]
                        payload["runs"].append(normalized)
            except OSError:
                continue

        return runs_by_job

    def _normalize_entry(self, entry: dict, file_job_id: str, date: str, enabled_jobs: dict[str, dict]) -> dict[str, Any] | None:
        if entry.get("action") not in (None, "finished"):
            return None

        event_date = self._entry_date(entry)
        if event_date != date:
            return None

        job_id = entry.get("jobId") or file_job_id
        job_meta = enabled_jobs.get(job_id, {})
        raw_status = str(entry.get("status", "")).lower()
        delivery_status = self._coerce_text(entry.get("deliveryStatus"))
        error_value = entry.get("error")
        error_text = self._extract_error_text(error_value)
        detailed_status, normalized_status = self._classify_status(raw_status, delivery_status, error_text)
        usage = entry.get("usage") or {}
        run_at_ms = entry.get("runAtMs") if isinstance(entry.get("runAtMs"), (int, float)) else None
        duration_ms = entry.get("durationMs") if isinstance(entry.get("durationMs"), (int, float)) else None
        observed_slot_dt = self._entry_slot_datetime(entry)

        return {
            "date": date,
            "cron_name": job_meta.get("name", job_id),
            "slot_time": self._slot_time(entry),
            "observed_slot_key": self._slot_key(observed_slot_dt) if observed_slot_dt is not None else None,
            "observed_slot_dt": observed_slot_dt,
            "status": detailed_status,
            "normalized_status": normalized_status,
            "job_id": job_id,
            "run_id": entry.get("runId"),
            "error": self._serialize_value(error_value),
            "run_at_ms": int(run_at_ms) if run_at_ms is not None else None,
            "duration_ms": int(duration_ms) if duration_ms is not None else None,
            "delivery_status": delivery_status,
            "model": entry.get("model"),
            "provider": entry.get("provider"),
            "input_tokens": self._safe_int(usage.get("input_tokens")),
            "output_tokens": self._safe_int(usage.get("output_tokens")),
            "total_tokens": self._safe_int(usage.get("total_tokens")),
        }

    def _entry_date(self, entry: dict) -> str | None:
        for key in ("runAtMs", "ts"):
            value = entry.get(key)
            if isinstance(value, (int, float)):
                try:
                    return datetime.fromtimestamp(value / 1000).strftime("%Y-%m-%d")
                except (OverflowError, OSError, ValueError):
                    pass
        for key in ("startedAt", "completedAt"):
            value = entry.get(key)
            if isinstance(value, str) and len(value) >= 10:
                return value[:10]
        return None

    def _slot_time(self, entry: dict) -> str | None:
        for key in ("runAtMs", "ts"):
            value = entry.get(key)
            if isinstance(value, (int, float)):
                try:
                    return datetime.fromtimestamp(value / 1000).strftime("%H:%M:%S")
                except (OverflowError, OSError, ValueError):
                    pass
        for key in ("startedAt", "completedAt"):
            value = entry.get(key)
            if isinstance(value, str) and len(value) >= 19:
                return value[11:19]
        return None

    def _observed_slot_key(self, entry: dict) -> str | None:
        observed_dt = self._entry_slot_datetime(entry)
        if observed_dt is None:
            return None
        return self._slot_key(observed_dt)

    def _entry_slot_datetime(self, entry: dict) -> datetime | None:
        for key in ("runAtMs", "ts"):
            value = entry.get(key)
            if isinstance(value, (int, float)):
                try:
                    return datetime.fromtimestamp(value / 1000).replace(second=0, microsecond=0)
                except (OverflowError, OSError, ValueError):
                    pass
        for key in ("startedAt", "completedAt"):
            value = entry.get(key)
            parsed = self._parse_iso_datetime(value)
            if parsed is not None:
                return parsed.replace(second=0, microsecond=0)
        return None

    def _parse_iso_datetime(self, value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            if len(text) < 16:
                return None
            try:
                parsed = datetime.strptime(text[:16], "%Y-%m-%dT%H:%M")
            except ValueError:
                return None
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed

    def _classify_status(self, raw_status: str, delivery_status: str | None, error_text: str) -> tuple[str, str]:
        raw_status_token = self._normalize_token(raw_status)
        delivery_token = self._normalize_token(delivery_status)
        raw_status_text = raw_status.strip().lower()
        delivery_text = (delivery_status or "").strip().lower()

        if self._is_timeout(raw_status_token, raw_status_text, error_text):
            return "timeout", "failure"
        if self._is_delivery_error(delivery_token, delivery_text, error_text):
            return "delivery_error", "failure"
        if error_text:
            return "failure", "failure"
        if raw_status_token in {"ok", "completed", "success", "succeeded"}:
            return "success", "success"
        if raw_status_token in {"error", "failed", "failure"}:
            return "failure", "failure"
        return "unknown", "unknown"

    def _is_timeout(self, raw_status_token: str, raw_status_text: str, error_text: str) -> bool:
        return (
            raw_status_token in {"timeout", "timed_out"}
            or "timed out" in raw_status_text
            or "timeout" in raw_status_text
            or "timed out" in error_text
            or "timeout" in error_text
        )

    def _is_delivery_error(self, delivery_token: str, delivery_text: str, error_text: str) -> bool:
        if delivery_token in {
            "delivery_error",
            "delivery_failed",
            "delivery_failure",
            "failed",
            "error",
        }:
            return True
        return any(
            phrase in delivery_text or phrase in error_text
            for phrase in (
                "delivery failed",
                "delivery error",
                "failed to deliver",
                "delivering to ",
                "requires target",
                "undeliver",
            )
        )

    def _extract_error_text(self, value: Any, depth: int = 0) -> str:
        if value is None or depth > 4:
            return ""
        if isinstance(value, str):
            return value.strip().lower()
        if isinstance(value, dict):
            priority_keys = ("message", "error", "details", "detail", "cause", "stderr", "stdout", "type", "code")
            parts = [
                self._extract_error_text(value[key], depth + 1)
                for key in priority_keys
                if key in value
            ]
            text = " ".join(part for part in parts if part).strip()
            if text:
                return text
            return " ".join(
                part for part in (self._extract_error_text(item, depth + 1) for item in value.values()) if part
            ).strip()
        if isinstance(value, (list, tuple, set)):
            return " ".join(
                part for part in (self._extract_error_text(item, depth + 1) for item in value) if part
            ).strip()
        return str(value).strip().lower()

    def _serialize_value(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text or None
        try:
            return json.dumps(value, ensure_ascii=True, sort_keys=True)
        except TypeError:
            text = str(value).strip()
            return text or None

    def _coerce_text(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _normalize_token(self, value: str | None) -> str:
        token = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
        while "__" in token:
            token = token.replace("__", "_")
        return token

    def _status_group(self, status: str | None) -> str:
        if status == "success":
            return "success"
        if status == "unknown":
            return "unknown"
        return "failure"

    def _status_counts(self, rows: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts = Counter(str(row.get(field, "unknown")) for row in rows if row.get(field))
        ordered: dict[str, int] = {}
        for status in self._STATUS_ORDER:
            count = counts.pop(status, 0)
            if count:
                ordered[status] = count
        for status in sorted(counts):
            if counts[status]:
                ordered[status] = counts[status]
        return ordered

    def _safe_int(self, value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _write_cron_runs(self, db_path: Path, date: str, rows: list[dict[str, Any]]) -> None:
        db = sqlite3.connect(str(db_path))
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("DELETE FROM cron_runs WHERE date = ?", (date,))
        for row in rows:
            db.execute(
                """INSERT INTO cron_runs (
                       date, cron_name, slot_time, status, job_id, run_id, error,
                       run_at_ms, duration_ms, delivery_status, model, provider,
                       input_tokens, output_tokens, total_tokens, created_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                (
                    row["date"], row["cron_name"], row["slot_time"], row["status"], row["job_id"],
                    row["run_id"], row["error"], row["run_at_ms"], row["duration_ms"], row["delivery_status"],
                    row["model"], row["provider"], row["input_tokens"], row["output_tokens"], row["total_tokens"],
                ),
            )
        db.commit()
        db.close()
