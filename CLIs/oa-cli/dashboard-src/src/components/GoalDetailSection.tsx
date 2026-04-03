import { lazy, Suspense, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type {
  GoalSummary,
  CronRun,
  AgentActivity,
  GoalMetricHistoryEntry,
  CronReliabilityBreakdown,
  CronMissedSlot,
  CronPerJobBreakdown,
  CronUnsupportedSchedule,
} from "../types";

const MetricChartPanel = lazy(async () => {
  const module = await import("./MetricChartPanel");
  return { default: module.MetricChartPanel };
});

function healthColor(status: string): string {
  switch (status) {
    case "healthy": return "#34D399";
    case "warning": return "#FBBF24";
    case "critical": return "#F87171";
    default: return "#94A3B8";
  }
}

function formatValue(value: number | null, unit: string): string {
  if (value === null) return "—";
  if (unit === "%" || unit === "percent") return `${Math.round(value)}%`;
  if (unit === "count") return `${Math.round(value)}`;
  return `${Math.round(value * 10) / 10}${unit ? ` ${unit}` : ""}`;
}

function formatMetricName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatCount(value: number, singular: string, plural: string = `${singular}s`): string {
  return `${value} ${value === 1 ? singular : plural}`;
}

function formatDuration(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (value < 1000) return `${Math.round(value)}ms`;
  return `${(value / 1000).toFixed(1)}s`;
}

function formatStatusDetailLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function truncateText(value: string, maxLength: number = 140): string {
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength - 1)}…`;
}

function getLatestCronBreakdown(goal: GoalSummary, metrics: GoalMetricHistoryEntry[]): CronReliabilityBreakdown | null {
  const currentBreakdown = goal.metrics["success_rate"]?.breakdown;
  if (currentBreakdown) return currentBreakdown as CronReliabilityBreakdown;

  const historicalRow = [...metrics]
    .reverse()
    .find((entry) => entry.metric === "success_rate" && entry.breakdown);

  return historicalRow?.breakdown ? historicalRow.breakdown as CronReliabilityBreakdown : null;
}

interface MetricDef {
  name: string;
  definition: string;
  calculation: string;
  purpose: string;
}

interface GoalMetricsDef {
  datasource: string;
  metrics: MetricDef[];
}

const GOAL_METRIC_DEFS: Record<string, GoalMetricsDef> = {
  cron_reliability: {
    datasource: "cron_runs",
    metrics: [
      {
        name: "Success Rate",
        definition: "Successful cron runs as a percent of the larger of observed runs or expected schedule slots",
        calculation: "Succeeded ÷ max(observed runs, expected slots) × 100; falls back to observed runs only when schedules cannot be expanded",
        purpose: "Shows whether cron work both ran successfully and covered the schedule OA expected to see.",
      },
      {
        name: "Failed Runs",
        definition: "Cron runs that errored, timed out, or explicitly failed",
        calculation: "Count of normalized status='failure'",
        purpose: "Highlights automation that ran but needs fixing",
      },
      {
        name: "Unknown Runs",
        definition: "Cron runs with a status OA could not classify as success or failure",
        calculation: "Count of normalized status='unknown'",
        purpose: "Flags log formats or runtime outcomes that need investigation",
      },
    ],
  },
  team_health: {
    datasource: "daily_agent_activity",
    metrics: [
      {
        name: "#DAA (Daily Active Agents)",
        definition: "Number of agents with status='active' per day",
        calculation: "COUNT(agent_id WHERE session_count > 0) per date",
        purpose: "Daily team engagement — how many agents are working each day?",
      },
      {
        name: "Sessions per Day",
        definition: "Total sessions across all agents per day",
        calculation: "SUM(session_count) per date from daily_agent_activity",
        purpose: "Activity volume — overall session throughput",
      },
      {
        name: "Memory Logged",
        definition: "Number of agents that wrote memory files per day",
        calculation: "COUNT(agent_id WHERE memory_logged > 0) per date",
        purpose: "Are agents recording their work?",
      },
      {
        name: "Per-Agent Activity (bar chart)",
        definition: "Days active vs days with sessions per agent",
        calculation: "COUNT(dates) GROUP BY agent_id",
        purpose: "Compare agent consistency over time",
      },
    ],
  },
};

function MetricChartFallback() {
  return <div className="h-full rounded-2xl bg-gray-50 animate-pulse" />;
}

function CronSummaryCard({
  label,
  value,
  hint,
  valueClassName,
}: {
  label: string;
  value: string;
  hint: string;
  valueClassName: string;
}) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-white/70 px-4 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-gray-400">
        {label}
      </div>
      <div className={`mt-2 text-2xl font-bold ${valueClassName}`}>
        {value}
      </div>
      <div className="mt-1 text-[11px] leading-5 text-gray-500">
        {hint}
      </div>
    </div>
  );
}

function CronListRow({
  title,
  subtitle,
  badge,
}: {
  title: string;
  subtitle: string;
  badge: string;
}) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl bg-white/70 px-3 py-2">
      <div className="min-w-0">
        <div className="text-xs font-semibold text-gray-700">
          {title}
        </div>
        <div className="text-[11px] leading-5 text-gray-500">
          {subtitle}
        </div>
      </div>
      <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
        {badge}
      </span>
    </div>
  );
}

function CronJobStat({
  label,
  value,
  toneClassName = "text-gray-700",
}: {
  label: string;
  value: string;
  toneClassName?: string;
}) {
  return (
    <div className="rounded-xl bg-white/70 px-3 py-2 xl:bg-transparent xl:px-0 xl:py-0">
      <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
        {label}
      </div>
      <div className={`mt-1 text-sm font-semibold ${toneClassName}`}>
        {value}
      </div>
    </div>
  );
}

function CronStatusPill({
  label,
  count,
  className,
}: {
  label: string;
  count: number;
  className: string;
}) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] ${className}`}>
      <span>{label}</span>
      <span>{count}</span>
    </span>
  );
}

interface CronJobRow extends CronPerJobBreakdown {
  jobName: string;
  unsupported_reason?: string;
}

function cronJobPriority(job: CronJobRow): number {
  if (job.supported_schedule === false) return 0;
  if ((job.missed ?? 0) > 0 || (job.failed ?? 0) > 0 || (job.unknown ?? 0) > 0) return 1;
  if ((job.unexpected_runs ?? 0) > 0) return 2;
  if ((job.late_matches ?? 0) > 0) return 3;
  return 4;
}

function cronJobBadge(job: CronJobRow): { label: string; className: string } {
  if (job.supported_schedule === false) {
    return {
      label: "Unsupported",
      className: "bg-gray-100 text-gray-600",
    };
  }
  if ((job.missed ?? 0) > 0 || (job.failed ?? 0) > 0 || (job.unknown ?? 0) > 0) {
    return {
      label: "Needs Attention",
      className: "bg-rose-50 text-rose-600",
    };
  }
  if ((job.unexpected_runs ?? 0) > 0) {
    return {
      label: "Unexpected Runs",
      className: "bg-violet-50 text-violet-600",
    };
  }
  if ((job.late_matches ?? 0) > 0) {
    return {
      label: "Late Tolerance",
      className: "bg-amber-50 text-amber-600",
    };
  }
  return {
    label: "On Schedule",
    className: "bg-emerald-50 text-emerald-600",
  };
}

function cronJobRateTone(job: CronJobRow): string {
  if (job.supported_schedule === false) return "text-gray-600";
  if ((job.missed ?? 0) > 0 || (job.failed ?? 0) > 0 || (job.unknown ?? 0) > 0) return "text-rose-600";
  if ((job.unexpected_runs ?? 0) > 0 || (job.late_matches ?? 0) > 0) return "text-amber-600";
  return "text-emerald-600";
}

function CronBreakdownPanel({ breakdown }: { breakdown: CronReliabilityBreakdown }) {
  const expectedSlots = breakdown.expected_slots ?? 0;
  const observedSlots = breakdown.observed_slots ?? 0;
  const exactMatches = breakdown.exact_matches ?? 0;
  const lateMatches = breakdown.late_matches ?? 0;
  const missed = breakdown.missed ?? 0;
  const unexpectedRuns = breakdown.unexpected_runs ?? 0;
  const unsupportedSchedules = breakdown.unsupported_schedules ?? [];
  const missedSlots = breakdown.missed_slots ?? [];
  const unanchoredEveryJobs = breakdown.unanchored_every_jobs ?? [];
  const totalRuns = breakdown.total_runs ?? 0;
  const lateToleranceMinutes = breakdown.late_tolerance_minutes;
  const shownMissedSlots = missedSlots.slice(0, 4);
  const shownUnsupportedSchedules = unsupportedSchedules.slice(0, 3);
  const shownUnanchoredJobs = unanchoredEveryJobs.slice(0, 3);
  const unsupportedByJobId = new Map(unsupportedSchedules.map((item) => [item.job_id, item.reason]));
  const perJobRows = Object.entries(breakdown.per_job ?? {})
    .map(([jobName, job]) => ({
      jobName,
      ...job,
      unsupported_reason: job.unsupported_reason ?? (job.job_id ? unsupportedByJobId.get(job.job_id) : undefined),
    }))
    .sort((a, b) => (
      cronJobPriority(a) - cronJobPriority(b) ||
      (a.rate ?? 0) - (b.rate ?? 0) ||
      (b.total ?? 0) - (a.total ?? 0) ||
      a.jobName.localeCompare(b.jobName)
    ));
  const [expandedJob, setExpandedJob] = useState<string | null>(
    () => perJobRows.find((job) => cronJobPriority(job) < 4)?.jobName ?? perJobRows[0]?.jobName ?? null,
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <CronSummaryCard
          label="Expected Slots"
          value={String(expectedSlots)}
          hint="Scheduled slots from supported jobs in the latest window."
          valueClassName="text-slate-700"
        />
        <CronSummaryCard
          label="Observed Slots"
          value={String(observedSlots)}
          hint={totalRuns > 0 ? `${totalRuns} total run${totalRuns === 1 ? "" : "s"} seen` : "No runs seen in the latest window"}
          valueClassName="text-blue-600"
        />
        <CronSummaryCard
          label="Exact Matches"
          value={String(exactMatches)}
          hint="Runs that landed on the expected scheduled minute."
          valueClassName="text-emerald-600"
        />
        <CronSummaryCard
          label="Late Matches"
          value={String(lateMatches)}
          hint={lateToleranceMinutes ? `Matched within the ${lateToleranceMinutes} minute late window.` : "Matched after the scheduled minute."}
          valueClassName="text-amber-500"
        />
        <CronSummaryCard
          label="Missed Slots"
          value={String(missed)}
          hint="Expected slots that never received a matching run."
          valueClassName="text-rose-500"
        />
        <CronSummaryCard
          label="Unexpected Runs"
          value={String(unexpectedRuns)}
          hint="Runs that did not match any expected slot."
          valueClassName="text-violet-500"
        />
        <CronSummaryCard
          label="Unsupported Schedules"
          value={String(unsupportedSchedules.length)}
          hint="Enabled jobs OA could not expand into minute-precision slots."
          valueClassName="text-gray-700"
        />
      </div>

      <div className="rounded-2xl border border-gray-100 bg-gray-50/60 p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-[0.15em] text-gray-500">
              Per Job Breakdown
            </h4>
            <p className="mt-1 text-xs leading-5 text-gray-500">
              Expand a row to inspect slot coverage, raw status details, and missed slot times.
            </p>
          </div>
          <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
            {formatCount(perJobRows.length, "job")}
          </span>
        </div>

        {perJobRows.length > 0 ? (
          <>
            <div className="hidden xl:grid xl:grid-cols-[minmax(0,1.8fr)_0.9fr_1fr_1fr_0.8fr_0.8fr_auto] gap-3 px-4 text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
              <span>Job</span>
              <span>Rate</span>
              <span>Expected vs Seen</span>
              <span>Runs</span>
              <span>Missed</span>
              <span>Unexpected</span>
              <span className="text-right">Details</span>
            </div>
            <div className="space-y-3">
              {perJobRows.map((job) => {
                const badge = cronJobBadge(job);
                const isExpanded = expandedJob === job.jobName;
                const statusEntries = Object.entries(job.status_details ?? {})
                  .sort(([, left], [, right]) => right - left);

                return (
                  <div key={job.jobName} className="overflow-hidden rounded-2xl border border-gray-100 bg-white/70">
                    <button
                      type="button"
                      onClick={() => setExpandedJob(isExpanded ? null : job.jobName)}
                      className="w-full px-4 py-4 text-left transition-colors hover:bg-white/90"
                    >
                      <div className="flex flex-col gap-4 xl:grid xl:grid-cols-[minmax(0,1.8fr)_0.9fr_1fr_1fr_0.8fr_0.8fr_auto] xl:items-center">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="truncate text-sm font-semibold text-gray-800">
                              {job.jobName}
                            </span>
                            <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${badge.className}`}>
                              {badge.label}
                            </span>
                          </div>
                          <p className="mt-1 text-[11px] leading-5 text-gray-500">
                            {job.supported_schedule === false
                              ? truncateText(job.unsupported_reason ?? "Schedule reasoning was not available for this job.")
                              : `${job.exact_matches ?? 0} exact · ${job.late_matches ?? 0} late matches${job.phase_policy ? " · epoch phase policy applied" : ""}`}
                          </p>
                        </div>
                        <CronJobStat
                          label="Rate"
                          value={`${Math.round(job.rate ?? 0)}%`}
                          toneClassName={cronJobRateTone(job)}
                        />
                        <CronJobStat
                          label="Expected vs Seen"
                          value={`${job.expected_slots ?? 0} / ${job.observed_slots ?? 0}`}
                        />
                        <CronJobStat
                          label="Runs"
                          value={`${job.success ?? 0} ok · ${job.failed ?? 0} fail · ${job.unknown ?? 0} unknown`}
                        />
                        <CronJobStat
                          label="Missed"
                          value={String(job.missed ?? 0)}
                          toneClassName={(job.missed ?? 0) > 0 ? "text-rose-600" : "text-gray-700"}
                        />
                        <CronJobStat
                          label="Unexpected"
                          value={String(job.unexpected_runs ?? 0)}
                          toneClassName={(job.unexpected_runs ?? 0) > 0 ? "text-violet-600" : "text-gray-700"}
                        />
                        <div className="text-right text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
                          {isExpanded ? "Hide" : "Details"}
                        </div>
                      </div>
                    </button>

                    <AnimatePresence initial={false}>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="border-t border-gray-100"
                        >
                          <div className="grid grid-cols-1 gap-3 px-4 py-4 xl:grid-cols-3">
                            <div className="rounded-xl bg-gray-50/80 px-3 py-3">
                              <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
                                Slot Coverage
                              </div>
                              <div className="mt-2 text-sm font-semibold text-gray-800">
                                {job.expected_slots ?? 0} expected · {job.observed_slots ?? 0} matched
                              </div>
                              <p className="mt-2 text-xs leading-5 text-gray-600">
                                Exact matches: {job.exact_matches ?? 0}. Late matches: {job.late_matches ?? 0}. Missed slots: {job.missed ?? 0}.
                              </p>
                              {job.phase_policy && (
                                <p className="mt-2 text-[11px] leading-5 text-gray-500">
                                  {job.phase_policy}
                                </p>
                              )}
                            </div>

                            <div className="rounded-xl bg-gray-50/80 px-3 py-3">
                              <div className="flex items-center justify-between gap-3">
                                <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
                                  Run Detail
                                </div>
                                <span className="text-[11px] font-semibold text-gray-500">
                                  Avg Duration {formatDuration(job.avg_duration_ms)}
                                </span>
                              </div>
                              <div className="mt-3 flex flex-wrap gap-2">
                                <CronStatusPill label="Success" count={job.success ?? 0} className="bg-emerald-50 text-emerald-600" />
                                <CronStatusPill label="Failed" count={job.failed ?? 0} className="bg-rose-50 text-rose-600" />
                                <CronStatusPill label="Unknown" count={job.unknown ?? 0} className="bg-violet-50 text-violet-600" />
                              </div>
                              {statusEntries.length > 0 && (
                                <div className="mt-3 space-y-2">
                                  <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
                                    Status Detail
                                  </div>
                                  <div className="flex flex-wrap gap-2">
                                    {statusEntries.map(([status, count]) => (
                                      <span key={status} className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-500">
                                        {formatStatusDetailLabel(status)} {count}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>

                            <div className="rounded-xl bg-gray-50/80 px-3 py-3">
                              <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
                                Missed Slot Times
                              </div>
                              {(job.missed_slot_times?.length ?? 0) > 0 ? (
                                <div className="mt-3 flex flex-wrap gap-2">
                                  {job.missed_slot_times!.map((slotTime) => (
                                    <span key={slotTime} className="rounded-full bg-white px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-500">
                                      {slotTime}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <p className="mt-2 text-xs leading-5 text-gray-500">
                                  No unmatched slot times were recorded for this job.
                                </p>
                              )}
                              {job.supported_schedule === false && (
                                <p className="mt-3 text-xs leading-5 text-gray-600">
                                  {job.unsupported_reason ?? "Schedule reasoning was unavailable for this job."}
                                </p>
                              )}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <p className="text-xs leading-5 text-gray-500">
            Per-job schedule detail was not reported for this Cron Reliability sample.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
        <div className="rounded-2xl border border-gray-100 bg-gray-50/60 p-4 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h4 className="text-xs font-semibold uppercase tracking-[0.15em] text-gray-500">
              Missed Slots
            </h4>
            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
              {formatCount(missedSlots.length, "slot")}
            </span>
          </div>
          {shownMissedSlots.length > 0 ? (
            <div className="space-y-2">
              {shownMissedSlots.map((slot: CronMissedSlot) => (
                <CronListRow
                  key={`${slot.job_id}-${slot.slot_time}`}
                  title={slot.cron_name}
                  subtitle="No matching run recorded for this slot."
                  badge={slot.slot_time}
                />
              ))}
              {missedSlots.length > shownMissedSlots.length && (
                <p className="text-[11px] text-gray-400">
                  +{missedSlots.length - shownMissedSlots.length} more missed slot{missedSlots.length - shownMissedSlots.length === 1 ? "" : "s"}
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs leading-5 text-gray-500">
              No missed slots were reported in the latest Cron Reliability sample.
            </p>
          )}
        </div>

        <div className="rounded-2xl border border-gray-100 bg-gray-50/60 p-4 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h4 className="text-xs font-semibold uppercase tracking-[0.15em] text-gray-500">
              Unsupported Schedules
            </h4>
            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
              {formatCount(unsupportedSchedules.length, "schedule")}
            </span>
          </div>
          {shownUnsupportedSchedules.length > 0 ? (
            <div className="space-y-2">
              {shownUnsupportedSchedules.map((schedule: CronUnsupportedSchedule) => (
                <CronListRow
                  key={`${schedule.job_id}-${schedule.reason}`}
                  title={schedule.cron_name}
                  subtitle={truncateText(schedule.reason)}
                  badge={schedule.schedule_kind ?? "unknown"}
                />
              ))}
              {unsupportedSchedules.length > shownUnsupportedSchedules.length && (
                <p className="text-[11px] text-gray-400">
                  +{unsupportedSchedules.length - shownUnsupportedSchedules.length} more unsupported schedule{unsupportedSchedules.length - shownUnsupportedSchedules.length === 1 ? "" : "s"}
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs leading-5 text-gray-500">
              All enabled schedules were supported at the current minute slot precision.
            </p>
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-blue-100 bg-blue-50/70 p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h4 className="text-xs font-semibold uppercase tracking-[0.15em] text-blue-700">
            Slot Matching Policy
          </h4>
          {lateToleranceMinutes !== undefined && (
            <span className="rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-700">
              Late tolerance {lateToleranceMinutes}m
            </span>
          )}
        </div>
        <p className="text-sm leading-6 text-blue-950/80">
          {breakdown.slot_matching_policy ?? "Policy details were not reported for this sample."}
        </p>

        <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
          <div className="rounded-xl bg-white/70 px-3 py-3">
            <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
              Every Without Anchor
            </div>
            {unanchoredEveryJobs.length > 0 ? (
              <div className="mt-2 space-y-2">
                <p className="text-xs leading-5 text-gray-600">
                  {breakdown.no_anchor_every_policy ?? "Unanchored every schedules use the default Unix epoch phase."}
                </p>
                <p className="text-[11px] text-gray-500">
                  Active for {shownUnanchoredJobs.map((job) => job.cron_name).join(", ")}
                  {unanchoredEveryJobs.length > shownUnanchoredJobs.length ? ` +${unanchoredEveryJobs.length - shownUnanchoredJobs.length} more` : ""}
                </p>
              </div>
            ) : (
              <p className="mt-2 text-xs leading-5 text-gray-500">
                No unanchored <code>every</code> schedules affected this window.
              </p>
            )}
          </div>

          <div className="rounded-xl bg-white/70 px-3 py-3">
            <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-400">
              Reasoning Note
            </div>
            <p className="mt-2 text-xs leading-5 text-gray-600">
              {breakdown.note ?? "No additional reasoning note was reported for this sample."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

const AGENT_COLORS: Record<string, string> = {
  coo: "#F59E0B",
  cto: "#60A5FA",
  youtube: "#FB7185",
  writer: "#A78BFA",
  cpo: "#22D3EE",
  podcast: "#34D399",
  researcher: "#F59E0B",
  reviewer: "#FB7185",
  publisher: "#A78BFA",
};

function TeamHealthAgentBars({ teamHealth }: { teamHealth: AgentActivity[] }) {
  const agentIds = [...new Set(teamHealth.map((activity) => activity.agent_id))];
  const agentStats = agentIds.map((agent) => {
    const rows = teamHealth.filter((activity) => activity.agent_id === agent);
    const daaDays = rows.filter((row) => row.session_count > 0).length;
    const totalSessions = rows.reduce((sum, row) => sum + row.session_count, 0);
    return { agent, daaDays, totalSessions };
  }).sort((left, right) => right.daaDays - left.daaDays);

  const maxDays = Math.max(...agentStats.map((row) => row.daaDays), 1);

  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
        Days Active per Agent
      </h4>
      <div className="space-y-2">
        {agentStats.map(({ agent, daaDays, totalSessions }) => (
          <div key={agent} className="flex items-center gap-2">
            <span className="w-16 shrink-0 text-right text-[11px] capitalize text-gray-500">{agent}</span>
            <div className="h-3 flex-1 overflow-hidden rounded-full bg-gray-50">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${(daaDays / maxDays) * 100}%`,
                  backgroundColor: AGENT_COLORS[agent] || "#9CA3AF",
                  opacity: 0.85,
                }}
              />
            </div>
            <span className="w-6 shrink-0 text-[9px] text-gray-500">{daaDays}d</span>
            <span className="w-14 shrink-0 text-[9px] text-gray-400">{totalSessions} sess</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface Props {
  goal: GoalSummary;
  index: number;
  metrics: GoalMetricHistoryEntry[];
  cronRuns: CronRun[];
  teamHealth: AgentActivity[];
}

export function GoalDetailSection({ goal, index, metrics, cronRuns, teamHealth }: Props) {
  const [showDetails, setShowDetails] = useState(false);
  const color = healthColor(goal.healthStatus);
  const allMetrics = Object.entries(goal.metrics);
  const primary = allMetrics[0];
  const isPercent = !!primary && (primary[1].unit === "%" || primary[1].unit === "percent");
  const isCronGoal = goal.id.includes("cron");
  const isTeamGoal = goal.id.includes("team") || goal.id.includes("health");
  const cronBreakdown = isCronGoal ? getLatestCronBreakdown(goal, metrics) : null;

  return (
    <>
      <motion.div
        className="detail-section space-y-5"
        style={{ "--goal-color": color } as React.CSSProperties}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 + index * 0.05 }}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-800">{goal.name}</h2>
          {GOAL_METRIC_DEFS[goal.id] && (
            <button
              onClick={() => setShowDetails(true)}
              className="cursor-pointer rounded-full bg-gray-100 px-1.5 py-0.5 text-[9px] text-gray-400 transition-colors hover:bg-gray-200 hover:text-gray-500"
            >
              📐 Metrics
            </button>
          )}
        </div>

        <div className="h-[200px]">
          <Suspense fallback={<MetricChartFallback />}>
            <MetricChartPanel
              goal={goal}
              cronRuns={cronRuns}
              teamHealth={teamHealth}
              color={color}
              isPercent={isPercent}
              isCronGoal={isCronGoal}
              isTeamGoal={isTeamGoal}
            />
          </Suspense>
        </div>

        {isCronGoal && cronBreakdown && (
          <CronBreakdownPanel breakdown={cronBreakdown} />
        )}

        {isTeamGoal && teamHealth.length > 0 && (
          <TeamHealthAgentBars teamHealth={teamHealth} />
        )}

        {allMetrics.length > 0 && !isTeamGoal && (
          <div className="flex flex-wrap gap-3">
            {allMetrics.map(([name, metric]) => (
              <div key={name} className="flex flex-col items-center rounded-xl bg-white/50 px-4 py-2">
                <span className="text-lg font-bold" style={{ color: healthColor(metric.status) }}>
                  {formatValue(metric.value, metric.unit)}
                </span>
                <span className="mt-0.5 text-[10px] uppercase tracking-wider text-gray-400">
                  {formatMetricName(name)}
                </span>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      <AnimatePresence>
        {showDetails && GOAL_METRIC_DEFS[goal.id] && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowDetails(false)}
            />
            <motion.div
              className="fixed right-0 top-0 z-50 h-full w-[480px] max-w-[90vw] overflow-y-auto bg-white shadow-2xl"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
            >
              <div className="space-y-6 p-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-gray-800">{goal.name}</h2>
                  <button
                    onClick={() => setShowDetails(false)}
                    className="cursor-pointer text-lg text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Metrics Definition</h4>
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <span className="text-[9px] text-gray-400">Datasource:</span>
                      <span className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] text-gray-500">
                        {GOAL_METRIC_DEFS[goal.id].datasource}
                      </span>
                    </div>
                  </div>
                  {GOAL_METRIC_DEFS[goal.id].metrics.map((metric) => (
                    <div key={metric.name} className="space-y-2 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
                      <h5 className="text-sm font-bold text-gray-800">{metric.name}</h5>
                      <div className="space-y-1.5">
                        <div className="flex gap-2">
                          <span className="w-20 shrink-0 pt-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">Definition</span>
                          <span className="text-xs text-gray-600">{metric.definition}</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="w-20 shrink-0 pt-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">Calculation</span>
                          <span className="font-mono text-xs text-gray-600">{metric.calculation}</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="w-20 shrink-0 pt-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">Purpose</span>
                          <span className="text-xs text-gray-600">{metric.purpose}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
