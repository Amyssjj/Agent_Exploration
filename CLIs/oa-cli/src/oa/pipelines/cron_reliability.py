"""G1: Cron Reliability Pipeline — tracks observed cron run success rates."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import Metric, Pipeline

if TYPE_CHECKING:
    from oa.core.config import ProjectConfig


class CronReliabilityPipeline(Pipeline):
    """Built-in pipeline: reads OpenClaw cron JSONL logs and computes success rates."""

    goal_id = "cron_reliability"

    def collect(self, date: str, config: "ProjectConfig") -> list[Metric]:
        from oa.core.tracing import Tracer

        cron_dir = config.openclaw_home / "cron"
        jobs_file = cron_dir / "jobs.json"
        runs_dir = cron_dir / "runs"
        tracer = Tracer(service="g1_cron_reliability", db_path=config.db_path)

        with tracer.span("G1: Cron Reliability", {"goal": "G1", "date": date}) as root:
            enabled_jobs = self._read_enabled_jobs(jobs_file)
            runs_by_job = self._collect_runs(runs_dir, date, enabled_jobs)

            observed_jobs = len(runs_by_job)
            total_runs = 0
            total_success = 0
            total_failed = 0
            total_unknown = 0
            per_job: dict[str, dict[str, Any]] = {}
            normalized_rows: list[dict[str, Any]] = []

            with tracer.span("Normalize Run History", {"jobs_file": str(jobs_file), "runs_dir": str(runs_dir)}) as hist:
                for job_id, payload in runs_by_job.items():
                    job_name = payload["job_name"]
                    runs = payload["runs"]
                    success = sum(1 for r in runs if r["normalized_status"] == "success")
                    failed = sum(1 for r in runs if r["normalized_status"] == "failure")
                    unknown = sum(1 for r in runs if r["normalized_status"] == "unknown")
                    total = len(runs)
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
                        "rate": round(success / total * 100, 1) if total > 0 else 0,
                        "avg_duration_ms": avg_duration,
                    }
                    total_runs += total
                    total_success += success
                    total_failed += failed
                    total_unknown += unknown
                    normalized_rows.extend(runs)

                hist.set_attribute("enabled_jobs", len(enabled_jobs))
                hist.set_attribute("observed_jobs", observed_jobs)
                hist.set_attribute("observed_runs", total_runs)

            with tracer.span("Compute Metrics") as compute:
                success_rate = round(total_success / total_runs * 100, 1) if total_runs > 0 else 0.0
                mode = "scheduled_mode" if enabled_jobs else ("observed_only" if total_runs > 0 else "no_data")
                compute.set_attribute("success_rate", success_rate)
                compute.set_attribute("mode", mode)
                compute.set_attribute("failed_runs", total_failed)

            with tracer.span("Write cron_runs DB"):
                self._write_cron_runs(config.db_path, date, normalized_rows)

            root.set_attribute("success_rate", success_rate)
            root.set_attribute("failed_runs", total_failed)
            root.set_attribute("unknown_runs", total_unknown)
            root.set_attribute("mode", mode)

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
                    "note": "expected-slot / missed-trigger calculation not yet enabled" if enabled_jobs else "jobs.json empty or no enabled cron jobs; using observed runs only",
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
        normalized_status = self._normalize_status(raw_status, entry)
        usage = entry.get("usage") or {}
        run_at_ms = entry.get("runAtMs") if isinstance(entry.get("runAtMs"), (int, float)) else None
        duration_ms = entry.get("durationMs") if isinstance(entry.get("durationMs"), (int, float)) else None

        return {
            "date": date,
            "cron_name": job_meta.get("name", job_id),
            "slot_time": self._slot_time(entry),
            "status": normalized_status,
            "normalized_status": normalized_status,
            "job_id": job_id,
            "run_id": entry.get("runId"),
            "error": entry.get("error"),
            "run_at_ms": int(run_at_ms) if run_at_ms is not None else None,
            "duration_ms": int(duration_ms) if duration_ms is not None else None,
            "delivery_status": entry.get("deliveryStatus"),
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

    def _normalize_status(self, raw_status: str, entry: dict) -> str:
        if raw_status in {"ok", "completed", "success", "succeeded"}:
            return "success"
        if raw_status in {"error", "failed", "failure", "timeout", "timed_out"}:
            return "failure"
        error_text = str(entry.get("error", "")).lower()
        if "timed out" in error_text or "timeout" in error_text:
            return "failure"
        return "unknown"

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
