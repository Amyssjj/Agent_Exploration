import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AreaChart, Area, ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import type { GoalSummary, CronRun, AgentActivity } from "../types";
import { formatShortDate, localizeGoalName, localizeMetricName, useI18n } from "../i18n";

// ── Helpers ──

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
        definition: "Percentage of cron jobs that ran and completed without error",
        calculation: "Succeeded ÷ (Total − Skipped) × 100",
        purpose: "Core reliability signal — are automated tasks running as scheduled?",
      },
      {
        name: "Succeeded",
        definition: "Cron job ran and completed without error",
        calculation: "Count of runs with status='ok'",
        purpose: "Baseline count of healthy executions",
      },
      {
        name: "Failed",
        definition: "Cron job ran but errored (timeout, crash, or exception)",
        calculation: "Count of runs with status='error'",
        purpose: "Identifies broken automation requiring fix",
      },
      {
        name: "Missed",
        definition: "Scheduled time slot with no run attempt recorded",
        calculation: "Expected slots − Actual runs (within 900s match window)",
        purpose: "Detects silent failures where crons don't even start",
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
  const { lang, t } = useI18n();
  // Aggregate by date
  const byDate = new Map<string, { success: number; failed: number; missed: number; total: number; jobs: Map<string, { success: number; total: number }> }>();

  for (const run of cronRuns) {
    if (!byDate.has(run.date)) {
      byDate.set(run.date, { success: 0, failed: 0, missed: 0, total: 0, jobs: new Map() });
    }
    const day = byDate.get(run.date)!;
    day.total++;
    if (run.status === "ok" || run.status === "success") day.success++;
    else if (run.status === "error" || run.status === "failed") day.failed++;
    else if (run.status === "missed") day.missed++;
    else day.success++; // default to success

    if (!day.jobs.has(run.cron_name)) day.jobs.set(run.cron_name, { success: 0, total: 0 });
    const job = day.jobs.get(run.cron_name)!;
    job.total++;
    if (run.status === "ok" || run.status === "success") job.success++;
  }

  const chartData = [...byDate.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, d]) => ({
      dateLabel: formatShortDate(date, lang),
      success: d.success,
      failed: d.failed,
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
        <span className="text-sm text-gray-300">{t("goal.cronStartingTomorrow")}</span>
        <span className="text-[10px] text-gray-200">{t("goal.cronStartingHint")}</span>
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
          radius={[0, 0, 0, 0]} name={t("chart.succeeded")} />
        <Bar yAxisId="count" dataKey="failed" stackId="runs" fill="#F87171" fillOpacity={0.7}
          radius={[0, 0, 0, 0]} name={t("chart.failed")} />
        <Bar yAxisId="count" dataKey="missed" stackId="runs" fill="#D1D5DB" fillOpacity={0.5}
          radius={[2, 2, 0, 0]} name={t("chart.missed")} />
        <Line yAxisId="rate" type="monotone" dataKey="successRate" stroke="#60A5FA" strokeWidth={2.5}
          dot={{ r: 3, fill: "#60A5FA", stroke: "#fff", strokeWidth: 2 }}
          activeDot={{ r: 5, fill: "#60A5FA", stroke: "#fff", strokeWidth: 2 }}
          name={t("chart.successRate")} />
      </ComposedChart>
    </ResponsiveContainer>
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
  const { t } = useI18n();
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
        <span style={{ fontWeight: 600, color: "#1F2937" }}>{t("chart.activeAgents")}</span>
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
            <span style={{ fontWeight: 600, color: "#F59E0B" }}>{t("chart.sessions")}</span>
            <span style={{ fontWeight: 700, color: "#F59E0B" }}>{sessionsEntry.value}</span>
          </div>
        </>
      )}
    </div>
  );
}

// ── Team Health: Stacked DAA Bar + Sessions Line (matches internal) ──

function TeamHealthDualChart({ teamHealth }: { teamHealth: AgentActivity[] }) {
  const { t, lang } = useI18n();
  // Get unique agents and dates
  const agentIds = [...new Set(teamHealth.map(a => a.agent_id))];
  const dates = [...new Set(teamHealth.map(a => a.date))].sort();

  if (dates.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-1">
        <span className="text-sm text-gray-300">{t("goal.teamLoading")}</span>
      </div>
    );
  }

  const chartData = dates.map(date => {
    const dayData: Record<string, unknown> = { dateLabel: formatShortDate(date, lang) };
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
          label={{ value: t("chart.sessions"), angle: 90, position: "insideRight", style: { fontSize: 9, fill: "#F59E0B" } }} />
        <Tooltip content={<TeamHealthTooltip />} wrapperStyle={{ zIndex: 50 }} />
        <Legend iconSize={8} wrapperStyle={{ fontSize: "10px", paddingTop: "4px" }} />
        {agentIds.map((agent, i) => (
          <Bar key={agent} yAxisId="daa" dataKey={agent} stackId="daa"
            fill={AGENT_COLORS[agent] || `hsl(${i * 60}, 60%, 60%)`}
            fillOpacity={0.7} name={agent} />
        ))}
        <Line yAxisId="sessions" type="monotone" dataKey="sessions" stroke="#F59E0B"
          strokeWidth={2} dot={false} name={t("chart.sessions")} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// ── Team Health: Per-Agent Bars ──

function TeamHealthAgentBars({ teamHealth }: { teamHealth: AgentActivity[] }) {
  const { t } = useI18n();
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
        {t("goal.daysActivePerAgent")}
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
            <span className="text-[9px] text-gray-500 w-6 shrink-0">{daaDays}{t("goal.daySuffix")}</span>
            <span className="text-[9px] text-gray-400 w-14 shrink-0">{totalSessions} {t("goal.sess")}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Default Area Chart ──

function DefaultChart({ goal, color, isPercent }: { goal: GoalSummary; color: string; isPercent: boolean }) {
  const { lang } = useI18n();
  const chartData = goal.sparkline.map(pt => ({
    dateLabel: formatShortDate(pt.date, lang),
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
  metrics: unknown[];
  cronRuns: CronRun[];
  teamHealth: AgentActivity[];
}

export function GoalDetailSection({ goal, index, metrics, cronRuns, teamHealth }: Props) {
  const { lang, t } = useI18n();
  const [showDetails, setShowDetails] = useState(false);
  const color = healthColor(goal.healthStatus);
  const allMetrics = Object.entries(goal.metrics);
  const primary = allMetrics[0];
  const isPercent = primary && (primary[1].unit === "%" || primary[1].unit === "percent");
  const isCronGoal = goal.id.includes("cron");
  const isTeamGoal = goal.id.includes("team") || goal.id.includes("health");

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
          <h2 className="text-lg font-bold text-gray-800">{localizeGoalName(goal.name, lang)}</h2>
          {GOAL_METRIC_DEFS[goal.id] && (
            <button
              onClick={() => setShowDetails(true)}
              className="text-[9px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-500 transition-colors cursor-pointer"
            >
              📐 {t("goal.metrics")}
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
              <span className="text-sm text-gray-300">{t("goal.dataStartingSoon")}</span>
              <span className="text-[10px] text-gray-200">
                {t("goal.collectDaily")} <code className="bg-gray-50 px-1.5 py-0.5 rounded">oa collect</code>
              </span>
            </div>
          )}
        </div>

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
                  {localizeMetricName(name, lang)}
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
                  <h2 className="text-lg font-bold text-gray-800">{localizeGoalName(goal.name, lang)}</h2>
                  <button onClick={() => setShowDetails(false)}
                    className="text-gray-400 hover:text-gray-600 text-lg cursor-pointer">✕</button>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("goal.metricDefinition")}</h4>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span className="text-[9px] text-gray-400">{t("goal.datasource")}:</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
                        {GOAL_METRIC_DEFS[goal.id].datasource}
                      </span>
                    </div>
                  </div>
                  {GOAL_METRIC_DEFS[goal.id].metrics.map((m) => (
                    <div key={m.name} className="rounded-xl border border-gray-100 bg-gray-50/50 p-4 space-y-2">
                      <h5 className="text-sm font-bold text-gray-800">{localizeMetricName(m.name, lang)}</h5>
                      <div className="space-y-1.5">
                        <div className="flex gap-2">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 w-20 shrink-0 pt-0.5">{t("goal.definition")}</span>
                          <span className="text-xs text-gray-600">{m.definition}</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 w-20 shrink-0 pt-0.5">{t("goal.calculation")}</span>
                          <span className="text-xs text-gray-600 font-mono">{m.calculation}</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 w-20 shrink-0 pt-0.5">{t("goal.purpose")}</span>
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
