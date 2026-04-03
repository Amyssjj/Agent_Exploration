import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AreaChart, Area, ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import type {
  GoalSummary,
  CronRun,
  AgentActivity,
  GoalMetricHistoryEntry,
  CronReliabilityBreakdown,
  CronMissedSlot,
  CronUnsupportedSchedule,
} from "../types";

// ── Helpers ──

function healthColor(status: string): string {
  switch (status) {
    case "healthy": return "#34D399";
    case "warning": return "#FBBF24";
    case "critical": return "#F87171";
    default: return "#94A3B8";
  }
}

function formatDate(d: string): string {
  const dt = new Date(d + "T00:00:00");
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function formatValue(value: number | null, unit: string): string {
  if (value === null) return "—";
  if (unit === "%" || unit === "percent") return `${Math.round(value)}%`;
  if (unit === "count") return `${Math.round(value)}`;
  return `${Math.round(value * 10) / 10}${unit ? ` ${unit}` : ""}`;
}

function formatMetricName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatCount(value: number, singular: string, plural: string = `${singular}s`): string {
  return `${value} ${value === 1 ? singular : plural}`;
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

// ── Metric Definitions (left panel slide-out) ──

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

// ── Glass Tooltip (matches internal style exactly) ──

function GlassTooltip({ active, payload, label, isPercent }: {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string; dataKey?: string; payload?: Record<string, unknown> }>;
  label?: string;
  isPercent?: boolean;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "rgba(255,255,255,0.97)",
      backdropFilter: "blur(12px)",
      border: "1px solid rgba(0,0,0,0.08)",
      borderRadius: "12px",
      padding: "10px 14px",
      fontSize: "11px",
      boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
      minWidth: "160px",
    }}>
      <div style={{ color: "#6B7280", fontSize: "10px", marginBottom: "6px" }}>{label}</div>
      {payload.map((entry, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", gap: "16px", marginBottom: "2px" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: entry.color, display: "inline-block" }} />
            <span style={{ fontWeight: 600, color: "#1F2937" }}>{entry.name}</span>
          </span>
          <span style={{ fontWeight: 700, color: entry.color }}>
            {isPercent ? `${entry.value}%` : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Cron Tooltip (per-job breakdown) ──

function CronTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ payload: Record<string, unknown> }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const data = payload[0].payload;
  const successRate = data.successRate as number;
  const jobs = (data.jobDetails || []) as { name: string; success: number; total: number; rate: number }[];

  return (
    <div style={{
      background: "rgba(255,255,255,0.97)",
      backdropFilter: "blur(12px)",
      border: "1px solid rgba(0,0,0,0.08)",
      borderRadius: "12px",
      padding: "10px 14px",
      fontSize: "11px",
      boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
      minWidth: "200px",
    }}>
      <div style={{ color: "#6B7280", fontSize: "10px", marginBottom: "6px" }}>{label}</div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
        <span style={{ fontWeight: 600, color: "#1F2937" }}>Success Rate</span>
        <span style={{ fontWeight: 700, color: "#60A5FA" }}>{successRate}%</span>
      </div>
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: jobs.length > 0 ? "4px" : "0" }}>
        {typeof data.success === "number" && <span style={{ color: "#059669", fontSize: "10px", fontWeight: 600 }}>success {data.success}</span>}
        {typeof data.failed === "number" && <span style={{ color: "#DC2626", fontSize: "10px", fontWeight: 600 }}>failed {data.failed}</span>}
        {typeof data.unknown === "number" && <span style={{ color: "#8B5CF6", fontSize: "10px", fontWeight: 600 }}>unknown {data.unknown}</span>}
        {typeof data.missed === "number" && data.missed > 0 && <span style={{ color: "#6B7280", fontSize: "10px", fontWeight: 600 }}>missed {data.missed}</span>}
      </div>
      {jobs.length > 0 && (
        <>
          <div style={{ borderTop: "1px solid rgba(0,0,0,0.06)", margin: "4px 0 6px" }} />
          {jobs.map((job) => (
            <div key={job.name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1px 0" }}>
              <span style={{ color: "#6B7280", fontSize: "10px", maxWidth: "140px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {job.name}
              </span>
              <span style={{ fontSize: "10px", display: "flex", gap: "6px", alignItems: "center" }}>
                <span style={{ color: "#374151", fontWeight: 500 }}>{job.success}/{job.total}</span>
                <span style={{
                  color: job.rate >= 100 ? "#059669" : job.rate > 0 ? "#D97706" : "#DC2626",
                  fontWeight: 600, minWidth: "32px", textAlign: "right",
                }}>{job.rate}%</span>
              </span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

// ── Cron Reliability: Stacked Bar + Line (matches internal exactly) ──

function CronReliabilityChart({ cronRuns }: { cronRuns: CronRun[] }) {
  // Aggregate by date
  const byDate = new Map<string, { success: number; failed: number; unknown: number; missed: number; total: number; jobs: Map<string, { success: number; total: number }> }>();

  for (const run of cronRuns) {
    if (!byDate.has(run.date)) {
      byDate.set(run.date, { success: 0, failed: 0, unknown: 0, missed: 0, total: 0, jobs: new Map() });
    }
    const day = byDate.get(run.date)!;
    day.total++;
    if (run.status === "ok" || run.status === "success") day.success++;
    else if (run.status === "error" || run.status === "failed" || run.status === "failure") day.failed++;
    else if (run.status === "missed") day.missed++;
    else day.unknown++;

    if (!day.jobs.has(run.cron_name)) day.jobs.set(run.cron_name, { success: 0, total: 0 });
    const job = day.jobs.get(run.cron_name)!;
    job.total++;
    if (run.status === "ok" || run.status === "success") job.success++;
  }

  const chartData = [...byDate.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, d]) => ({
      dateLabel: formatDate(date),
      success: d.success,
      failed: d.failed,
      unknown: d.unknown,
      missed: d.missed,
      successRate: d.total > 0 ? Math.round((d.success / d.total) * 100) : 0,
      scheduled: d.total,
      jobDetails: [...d.jobs.entries()].map(([name, j]) => ({
        name,
        success: j.success,
        total: j.total,
        rate: j.total > 0 ? Math.round((j.success / j.total) * 100) : 0,
      })),
    }));

  if (chartData.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-1">
        <span className="text-sm text-gray-300">Cron run tracking starting tomorrow</span>
        <span className="text-[10px] text-gray-200">Combined chart will appear once per-slot data is recorded</span>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={chartData} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
        <XAxis dataKey="dateLabel" tick={{ fontSize: 10, fill: "#9CA3AF" }} tickLine={false}
          axisLine={{ stroke: "rgba(0,0,0,0.06)" }} interval="preserveStartEnd" />
        <YAxis yAxisId="rate" orientation="left" tick={{ fontSize: 10, fill: "#60A5FA" }}
          tickLine={false} axisLine={false} width={36} domain={[0, 100]}
          tickFormatter={(v) => `${v}%`} />
        <YAxis yAxisId="count" orientation="right" tick={{ fontSize: 10, fill: "#9CA3AF" }}
          tickLine={false} axisLine={false} width={36} allowDecimals={false} />
        <Tooltip content={<CronTooltip />} wrapperStyle={{ zIndex: 50 }} />
        <Legend iconSize={8} wrapperStyle={{ fontSize: "10px", paddingTop: "4px" }} />
        <Bar yAxisId="count" dataKey="success" stackId="runs" fill="#34D399" fillOpacity={0.6}
          radius={[0, 0, 0, 0]} name="Succeeded" />
        <Bar yAxisId="count" dataKey="failed" stackId="runs" fill="#F87171" fillOpacity={0.7}
          radius={[0, 0, 0, 0]} name="Failed" />
        <Bar yAxisId="count" dataKey="unknown" stackId="runs" fill="#8B5CF6" fillOpacity={0.65}
          radius={[0, 0, 0, 0]} name="Unknown" />
        <Bar yAxisId="count" dataKey="missed" stackId="runs" fill="#D1D5DB" fillOpacity={0.5}
          radius={[2, 2, 0, 0]} name="Missed" />
        <Line yAxisId="rate" type="monotone" dataKey="successRate" stroke="#60A5FA" strokeWidth={2.5}
          dot={{ r: 3, fill: "#60A5FA", stroke: "#fff", strokeWidth: 2 }}
          activeDot={{ r: 5, fill: "#60A5FA", stroke: "#fff", strokeWidth: 2 }}
          name="Success Rate" />
      </ComposedChart>
    </ResponsiveContainer>
  );
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

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
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

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
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

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
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

// ── Team Health Tooltip (per-agent breakdown) ──

const AGENT_COLORS: Record<string, string> = {
  coo: "#F59E0B", cto: "#60A5FA", youtube: "#FB7185", writer: "#A78BFA",
  cpo: "#22D3EE", podcast: "#34D399", researcher: "#F59E0B", reviewer: "#FB7185",
  publisher: "#A78BFA",
};

function TeamHealthTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ dataKey: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const agents = payload.filter(p => p.dataKey !== "sessions" && p.value > 0);
  const sessionsEntry = payload.find(p => p.dataKey === "sessions");

  return (
    <div style={{
      background: "rgba(255,255,255,0.97)",
      backdropFilter: "blur(12px)",
      border: "1px solid rgba(0,0,0,0.08)",
      borderRadius: "12px",
      padding: "10px 14px",
      fontSize: "11px",
      boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
      minWidth: "160px",
    }}>
      <div style={{ color: "#6B7280", fontSize: "10px", marginBottom: "6px" }}>{label}</div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
        <span style={{ fontWeight: 600, color: "#1F2937" }}>Active Agents</span>
        <span style={{ fontWeight: 700, color: "#374151" }}>{agents.length}</span>
      </div>
      {agents.map(a => (
        <div key={a.dataKey} style={{ display: "flex", alignItems: "center", gap: "4px", padding: "1px 0" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: a.color, display: "inline-block" }} />
          <span style={{ color: "#6B7280", fontSize: "10px" }}>{a.dataKey}</span>
        </div>
      ))}
      {sessionsEntry && (
        <>
          <div style={{ borderTop: "1px solid rgba(0,0,0,0.06)", margin: "4px 0" }} />
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontWeight: 600, color: "#F59E0B" }}>Sessions</span>
            <span style={{ fontWeight: 700, color: "#F59E0B" }}>{sessionsEntry.value}</span>
          </div>
        </>
      )}
    </div>
  );
}

// ── Team Health: Stacked DAA Bar + Sessions Line (matches internal) ──

function TeamHealthDualChart({ teamHealth }: { teamHealth: AgentActivity[] }) {
  // Get unique agents and dates
  const agentIds = [...new Set(teamHealth.map(a => a.agent_id))];
  const dates = [...new Set(teamHealth.map(a => a.date))].sort();

  if (dates.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-1">
        <span className="text-sm text-gray-300">Team health data loading...</span>
      </div>
    );
  }

  const chartData = dates.map(date => {
    const dayData: Record<string, unknown> = { dateLabel: formatDate(date) };
    let totalSessions = 0;
    for (const agent of agentIds) {
      const row = teamHealth.find(a => a.date === date && a.agent_id === agent);
      dayData[agent] = row && row.session_count > 0 ? 1 : 0; // 1 = active, 0 = inactive
      totalSessions += row?.session_count || 0;
    }
    dayData.sessions = totalSessions;
    return dayData;
  });

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={chartData} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
        <XAxis dataKey="dateLabel" tick={{ fontSize: 10, fill: "#9CA3AF" }} tickLine={false}
          axisLine={{ stroke: "rgba(0,0,0,0.06)" }} interval="preserveStartEnd" />
        <YAxis yAxisId="daa" tick={{ fontSize: 10, fill: "#9CA3AF" }} tickLine={false}
          axisLine={false} width={28} allowDecimals={false} domain={[0, Math.max(agentIds.length, 6)]}
          label={{ value: "#DAA", angle: -90, position: "insideLeft", style: { fontSize: 9, fill: "#9CA3AF" } }} />
        <YAxis yAxisId="sessions" orientation="right" tick={{ fontSize: 10, fill: "#F59E0B" }}
          tickLine={false} axisLine={false} width={28} allowDecimals={false}
          label={{ value: "Sessions", angle: 90, position: "insideRight", style: { fontSize: 9, fill: "#F59E0B" } }} />
        <Tooltip content={<TeamHealthTooltip />} wrapperStyle={{ zIndex: 50 }} />
        <Legend iconSize={8} wrapperStyle={{ fontSize: "10px", paddingTop: "4px" }} />
        {agentIds.map((agent, i) => (
          <Bar key={agent} yAxisId="daa" dataKey={agent} stackId="daa"
            fill={AGENT_COLORS[agent] || `hsl(${i * 60}, 60%, 60%)`}
            fillOpacity={0.7} name={agent} />
        ))}
        <Line yAxisId="sessions" type="monotone" dataKey="sessions" stroke="#F59E0B"
          strokeWidth={2} dot={false} name="Sessions" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// ── Team Health: Per-Agent Bars ──

function TeamHealthAgentBars({ teamHealth }: { teamHealth: AgentActivity[] }) {
  const agentIds = [...new Set(teamHealth.map(a => a.agent_id))];
  const agentStats = agentIds.map(agent => {
    const rows = teamHealth.filter(a => a.agent_id === agent);
    const daaDays = rows.filter(r => r.session_count > 0).length;
    const sessionDays = rows.filter(r => r.session_count > 0).length;
    const totalSessions = rows.reduce((sum, r) => sum + r.session_count, 0);
    return { agent, daaDays, sessionDays, totalSessions };
  }).sort((a, b) => b.daaDays - a.daaDays);

  const maxDays = Math.max(...agentStats.map(d => d.daaDays), 1);

  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Days Active per Agent
      </h4>
      <div className="space-y-2">
        {agentStats.map(({ agent, daaDays, totalSessions }) => (
          <div key={agent} className="flex items-center gap-2">
            <span className="text-[11px] text-gray-500 w-16 text-right shrink-0 capitalize">{agent}</span>
            <div className="flex-1 h-3 bg-gray-50 rounded-full overflow-hidden">
              <div className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${(daaDays / maxDays) * 100}%`,
                  backgroundColor: AGENT_COLORS[agent] || "#9CA3AF",
                  opacity: 0.85,
                }} />
            </div>
            <span className="text-[9px] text-gray-500 w-6 shrink-0">{daaDays}d</span>
            <span className="text-[9px] text-gray-400 w-14 shrink-0">{totalSessions} sess</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Default Area Chart ──

function DefaultChart({ goal, color, isPercent }: { goal: GoalSummary; color: string; isPercent: boolean }) {
  const chartData = goal.sparkline.map(pt => ({
    dateLabel: formatDate(pt.date),
    value: pt.value,
  }));
  const gradientId = `grad-${goal.id}`;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={chartData} margin={{ top: 8, right: 16, bottom: 4, left: 8 }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.2} />
            <stop offset="95%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
        <XAxis dataKey="dateLabel" tick={{ fontSize: 10, fill: "#9CA3AF" }} tickLine={false}
          axisLine={{ stroke: "rgba(0,0,0,0.06)" }} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10, fill: "#9CA3AF" }} tickLine={false} axisLine={false}
          width={36} domain={isPercent ? [0, 100] : ["auto", "auto"]} />
        <Tooltip content={<GlassTooltip isPercent={isPercent} />} wrapperStyle={{ zIndex: 50 }} />
        <Area type="monotone" dataKey="value" stroke={color} strokeWidth={2}
          fill={`url(#${gradientId})`}
          activeDot={{ r: 4, fill: color, stroke: "#fff", strokeWidth: 2 }}
          animationDuration={800} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ── Main Component ──

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
  const isPercent = primary && (primary[1].unit === "%" || primary[1].unit === "percent");
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
        {/* Section Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-800">{goal.name}</h2>
          {GOAL_METRIC_DEFS[goal.id] && (
            <button
              onClick={() => setShowDetails(true)}
              className="text-[9px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-500 transition-colors cursor-pointer"
            >
              📐 Metrics
            </button>
          )}
        </div>

        {/* Chart — goal-specific */}
        <div className="h-[200px]">
          {isCronGoal && cronRuns.length > 0 ? (
            <CronReliabilityChart cronRuns={cronRuns} />
          ) : isTeamGoal ? (
            <TeamHealthDualChart teamHealth={teamHealth} />
          ) : goal.sparkline.length >= 2 ? (
            <DefaultChart goal={goal} color={color} isPercent={!!isPercent} />
          ) : (
            <div className="h-full flex flex-col items-center justify-center gap-1">
              <span className="text-sm text-gray-300">Data collection starting soon</span>
              <span className="text-[10px] text-gray-200">
                Run <code className="bg-gray-50 px-1.5 py-0.5 rounded">oa collect</code> daily
              </span>
            </div>
          )}
        </div>

        {isCronGoal && cronBreakdown && (
          <CronBreakdownPanel breakdown={cronBreakdown} />
        )}

        {/* Team Health: additional breakdowns */}
        {isTeamGoal && teamHealth.length > 0 && (
          <TeamHealthAgentBars teamHealth={teamHealth} />
        )}

        {/* Metrics Summary Grid (non-team goals) */}
        {allMetrics.length > 0 && !isTeamGoal && (
          <div className="flex flex-wrap gap-3">
            {allMetrics.map(([name, m]) => (
              <div key={name} className="flex flex-col items-center px-4 py-2 bg-white/50 rounded-xl">
                <span className="text-lg font-bold" style={{ color: healthColor(m.status) }}>
                  {formatValue(m.value, m.unit)}
                </span>
                <span className="text-[10px] text-gray-400 uppercase tracking-wider mt-0.5">
                  {formatMetricName(name)}
                </span>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Slide-in Metrics Definition Panel */}
      <AnimatePresence>
        {showDetails && GOAL_METRIC_DEFS[goal.id] && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setShowDetails(false)}
            />
            <motion.div
              className="fixed top-0 right-0 h-full w-[480px] max-w-[90vw] bg-white shadow-2xl z-50 overflow-y-auto"
              initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
            >
              <div className="p-6 space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-gray-800">{goal.name}</h2>
                  <button onClick={() => setShowDetails(false)}
                    className="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">✕</button>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Metrics Definition</h4>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span className="text-[9px] text-gray-400">Datasource:</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
                        {GOAL_METRIC_DEFS[goal.id].datasource}
                      </span>
                    </div>
                  </div>
                  {GOAL_METRIC_DEFS[goal.id].metrics.map((m) => (
                    <div key={m.name} className="rounded-xl border border-gray-100 bg-gray-50/50 p-4 space-y-2">
                      <h5 className="text-sm font-bold text-gray-800">{m.name}</h5>
                      <div className="space-y-1.5">
                        <div className="flex gap-2">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 w-20 shrink-0 pt-0.5">Definition</span>
                          <span className="text-xs text-gray-600">{m.definition}</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 w-20 shrink-0 pt-0.5">Calculation</span>
                          <span className="text-xs text-gray-600 font-mono">{m.calculation}</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 w-20 shrink-0 pt-0.5">Purpose</span>
                          <span className="text-xs text-gray-600">{m.purpose}</span>
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
