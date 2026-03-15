"""G1: Cron Reliability Pipeline — tracks cron job success rates."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

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

            # Step 1: Read cron job config
            with tracer.span("Read Cron Config", {"source": str(jobs_file)}):
                if not jobs_file.exists():
                    root.set_status("error", "jobs.json not found")
                    tracer.flush()
                    return [Metric("success_rate", 0, "%")]

                with open(jobs_file, encoding="utf-8") as f:
                    jobs_data = json.load(f)

                jobs = jobs_data.get("jobs", [])
                enabled_jobs = [
                    j for j in jobs
                    if j.get("enabled", True) and j.get("schedule", {}).get("kind") == "cron"
                ]

            # Step 2: Read run history from JSONL files
            with tracer.span("Read Run History", {"source": str(runs_dir)}) as hist:
                per_job: dict[str, dict] = {}

                for job in enabled_jobs:
                    job_id = job.get("id", "unknown")
                    job_name = job.get("name", job_id)
                    runs = self._read_runs_jsonl(runs_dir, job_id, date)

                    success = sum(1 for r in runs if r.get("status") == "completed")
                    failed = sum(1 for r in runs if r.get("status") in ("failed", "error"))
                    total = len(runs)

                    per_job[job_name] = {
                        "job_id": job_id,
                        "total": total,
                        "success": success,
                        "failed": failed,
                        "rate": round(success / total * 100, 1) if total > 0 else 0,
                    }

                hist.set_attribute("jobs_scanned", len(enabled_jobs))

            # Step 3: Compute overall success rate
            with tracer.span("Compute Metrics") as compute:
                total_runs = sum(d["total"] for d in per_job.values())
                total_success = sum(d["success"] for d in per_job.values())
                success_rate = round(total_success / total_runs * 100, 1) if total_runs > 0 else 100.0

                compute.set_attribute("success_rate", success_rate)
                compute.set_attribute("total_runs", total_runs)

            # Step 4: Write cron_runs to DB
            with tracer.span("Write cron_runs DB"):
                self._write_cron_runs(config.db_path, date, per_job)

            root.set_attribute("success_rate", success_rate)

        tracer.flush()
        return [Metric(
            "success_rate",
            success_rate,
            unit="%",
            breakdown={"per_job": per_job, "total_runs": total_runs},
        )]

    def _read_runs_jsonl(self, runs_dir: Path, job_id: str, date: str) -> list[dict]:
        """Read JSONL run entries for a job, filtered to a specific date."""
        jsonl_file = runs_dir / f"{job_id}.jsonl"
        if not jsonl_file.exists():
            return []

        runs = []
        try:
            with open(jsonl_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        # Filter by date — check startedAt or completedAt
                        started = entry.get("startedAt", "")
                        if started.startswith(date):
                            runs.append(entry)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass

        return runs

    def _write_cron_runs(self, db_path: Path, date: str, per_job: dict) -> None:
        """Write per-job results to cron_runs table."""
        db = sqlite3.connect(str(db_path))
        db.execute("PRAGMA journal_mode=WAL")

        for job_name, data in per_job.items():
            # Insert a summary row per job per date
            db.execute(
                """INSERT INTO cron_runs (date, cron_name, status, job_id, created_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                (date, job_name,
                 "success" if data["rate"] >= 80 else "failed",
                 data.get("job_id", "")),
            )

        db.commit()
        db.close()
