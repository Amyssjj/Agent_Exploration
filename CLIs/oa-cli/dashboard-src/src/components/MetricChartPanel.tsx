import {
  AreaChart,
  Area,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { GoalSummary, CronRun, AgentActivity } from "../types";
import { isVisualTestMode } from "../lib/runtimeFlags";

function formatDate(d: string): string {
  const dt = new Date(`${d}T00:00:00`);
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function GlassTooltip({ active, payload, label, isPercent }: {
  active?: boolean;
  payload?: Array<{ value: number; name: string; color: string }>;
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
      {payload.map((entry, index) => (
        <div key={index} style={{ display: "flex", justifyContent: "space-between", gap: "16px", marginBottom: "2px" }}>
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
                  fontWeight: 600,
                  minWidth: "32px",
                  textAlign: "right",
                }}>{job.rate}%</span>
              </span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function CronReliabilityChart({ cronRuns }: { cronRuns: CronRun[] }) {
  const animationEnabled = !isVisualTestMode();
  const byDate = new Map<string, {
    success: number;
    failed: number;
    unknown: number;
    missed: number;
    total: number;
    jobs: Map<string, { success: number; total: number }>;
  }>();

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
    .map(([date, day]) => ({
      dateLabel: formatDate(date),
      success: day.success,
      failed: day.failed,
      unknown: day.unknown,
      missed: day.missed,
      successRate: day.total > 0 ? Math.round((day.success / day.total) * 100) : 0,
      scheduled: day.total,
      jobDetails: [...day.jobs.entries()].map(([name, job]) => ({
        name,
        success: job.success,
        total: job.total,
        rate: job.total > 0 ? Math.round((job.success / job.total) * 100) : 0,
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
          tickFormatter={(value) => `${value}%`} />
        <YAxis yAxisId="count" orientation="right" tick={{ fontSize: 10, fill: "#9CA3AF" }}
          tickLine={false} axisLine={false} width={36} allowDecimals={false} />
        <Tooltip content={<CronTooltip />} wrapperStyle={{ zIndex: 50 }} />
        <Legend iconSize={8} wrapperStyle={{ fontSize: "10px", paddingTop: "4px" }} />
        <Bar yAxisId="count" dataKey="success" stackId="runs" fill="#34D399" fillOpacity={0.6}
          radius={[0, 0, 0, 0]} name="Succeeded" isAnimationActive={animationEnabled} />
        <Bar yAxisId="count" dataKey="failed" stackId="runs" fill="#F87171" fillOpacity={0.7}
          radius={[0, 0, 0, 0]} name="Failed" isAnimationActive={animationEnabled} />
        <Bar yAxisId="count" dataKey="unknown" stackId="runs" fill="#8B5CF6" fillOpacity={0.65}
          radius={[0, 0, 0, 0]} name="Unknown" isAnimationActive={animationEnabled} />
        <Bar yAxisId="count" dataKey="missed" stackId="runs" fill="#D1D5DB" fillOpacity={0.5}
          radius={[2, 2, 0, 0]} name="Missed" isAnimationActive={animationEnabled} />
        <Line yAxisId="rate" type="monotone" dataKey="successRate" stroke="#60A5FA" strokeWidth={2.5}
          dot={{ r: 3, fill: "#60A5FA", stroke: "#fff", strokeWidth: 2 }}
          activeDot={{ r: 5, fill: "#60A5FA", stroke: "#fff", strokeWidth: 2 }}
          name="Success Rate" isAnimationActive={animationEnabled} />
      </ComposedChart>
    </ResponsiveContainer>
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

function TeamHealthTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ dataKey: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const agents = payload.filter((entry) => entry.dataKey !== "sessions" && entry.value > 0);
  const sessionsEntry = payload.find((entry) => entry.dataKey === "sessions");

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
      {agents.map((agent) => (
        <div key={agent.dataKey} style={{ display: "flex", alignItems: "center", gap: "4px", padding: "1px 0" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: agent.color, display: "inline-block" }} />
          <span style={{ color: "#6B7280", fontSize: "10px" }}>{agent.dataKey}</span>
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

function TeamHealthDualChart({ teamHealth }: { teamHealth: AgentActivity[] }) {
  const animationEnabled = !isVisualTestMode();
  const agentIds = [...new Set(teamHealth.map((activity) => activity.agent_id))];
  const dates = [...new Set(teamHealth.map((activity) => activity.date))].sort();

  if (dates.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-1">
        <span className="text-sm text-gray-300">Team health data loading...</span>
      </div>
    );
  }

  const chartData = dates.map((date) => {
    const dayData: Record<string, unknown> = { dateLabel: formatDate(date) };
    let totalSessions = 0;
    for (const agent of agentIds) {
      const row = teamHealth.find((activity) => activity.date === date && activity.agent_id === agent);
      dayData[agent] = row && row.session_count > 0 ? 1 : 0;
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
        {agentIds.map((agent, index) => (
          <Bar key={agent} yAxisId="daa" dataKey={agent} stackId="daa"
            fill={AGENT_COLORS[agent] || `hsl(${index * 60}, 60%, 60%)`}
            fillOpacity={0.7} name={agent} isAnimationActive={animationEnabled} />
        ))}
        <Line yAxisId="sessions" type="monotone" dataKey="sessions" stroke="#F59E0B"
          strokeWidth={2} dot={false} name="Sessions" isAnimationActive={animationEnabled} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function DefaultChart({ goal, color, isPercent }: { goal: GoalSummary; color: string; isPercent: boolean }) {
  const animationEnabled = !isVisualTestMode();
  const chartData = goal.sparkline.map((point) => ({
    dateLabel: formatDate(point.date),
    value: point.value,
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
          animationDuration={animationEnabled ? 800 : 0}
          isAnimationActive={animationEnabled} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface Props {
  goal: GoalSummary;
  cronRuns: CronRun[];
  teamHealth: AgentActivity[];
  color: string;
  isPercent: boolean;
  isCronGoal: boolean;
  isTeamGoal: boolean;
}

function VisualTestReadyMarker({ goalId }: { goalId: string }) {
  if (!isVisualTestMode()) {
    return null;
  }

  return <span hidden data-visual-test-ready={goalId} />;
}

export function MetricChartPanel({
  goal,
  cronRuns,
  teamHealth,
  color,
  isPercent,
  isCronGoal,
  isTeamGoal,
}: Props) {
  if (isCronGoal) {
    return (
      <>
        <CronReliabilityChart cronRuns={cronRuns} />
        <VisualTestReadyMarker goalId={goal.id} />
      </>
    );
  }

  if (isTeamGoal) {
    return (
      <>
        <TeamHealthDualChart teamHealth={teamHealth} />
        <VisualTestReadyMarker goalId={goal.id} />
      </>
    );
  }

  if (goal.sparkline.length >= 2) {
    return (
      <>
        <DefaultChart goal={goal} color={color} isPercent={isPercent} />
        <VisualTestReadyMarker goalId={goal.id} />
      </>
    );
  }

  return (
    <>
      <div className="h-full flex flex-col items-center justify-center gap-1">
        <span className="text-sm text-gray-300">Data collection starting soon</span>
        <span className="text-[10px] text-gray-200">
          Run <code className="bg-gray-50 px-1.5 py-0.5 rounded">oa collect</code> daily
        </span>
      </div>
      <VisualTestReadyMarker goalId={goal.id} />
    </>
  );
}
