import { motion } from "framer-motion";
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import type { GoalSummary } from "../types";

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
  if (unit === "%" || unit === "percent") return `${Math.round(value * 10) / 10}%`;
  if (unit === "count") return `${Math.round(value)}`;
  return `${Math.round(value * 10) / 10}${unit ? ` ${unit}` : ""}`;
}

function formatMetricName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

interface Props {
  goal: GoalSummary;
  index: number;
  metrics: unknown[];
}

export function GoalDetailSection({ goal, index, metrics }: Props) {
  const color = healthColor(goal.healthStatus);
  const chartData = goal.sparkline.map((pt) => ({
    date: pt.date,
    dateLabel: formatDate(pt.date),
    value: pt.value,
  }));

  const allMetrics = Object.entries(goal.metrics);
  const primary = allMetrics[0];
  const isPercent = primary && (primary[1].unit === "%" || primary[1].unit === "percent");

  return (
    <motion.div
      className="detail-section h-full"
      style={{ "--goal-color": color } as React.CSSProperties}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 + 0.05 }}
    >
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {goal.name} — Trend
        </h4>
        <span className="text-[10px] text-gray-400 font-mono">
          {chartData.length} days
        </span>
      </div>

      {/* Chart */}
      {chartData.length >= 2 ? (
        <div className="h-[160px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 4 }}>
              <defs>
                <linearGradient id={`grad-${goal.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.15} />
                  <stop offset="100%" stopColor={color} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
              <XAxis
                dataKey="dateLabel"
                tick={{ fontSize: 9, fill: "#9CA3AF" }}
                tickLine={false}
                axisLine={{ stroke: "rgba(0,0,0,0.06)" }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 9, fill: "#9CA3AF" }}
                tickLine={false}
                axisLine={false}
                width={32}
                domain={isPercent ? [0, 100] : ["auto", "auto"]}
              />
              <Tooltip
                contentStyle={{
                  background: "rgba(255,255,255,0.95)",
                  border: "1px solid rgba(0,0,0,0.08)",
                  borderRadius: "8px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                  fontSize: "11px",
                }}
                labelStyle={{ fontWeight: 600, color: "#374151" }}
                itemStyle={{ color: "#6b7280" }}
                formatter={(value: number) => [isPercent ? `${value}%` : value, ""]}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                fill={`url(#grad-${goal.id})`}
                dot={chartData.length <= 14}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-[160px] flex items-center justify-center">
          <span className="text-xs text-gray-300">
            Not enough data for chart — run <code className="bg-gray-50 px-1.5 py-0.5 rounded">oa collect</code> daily
          </span>
        </div>
      )}

      {/* Metrics Summary Grid */}
      {allMetrics.length > 0 && (
        <div className={`grid grid-cols-2 sm:grid-cols-${Math.min(allMetrics.length, 4)} gap-3 mt-4 pt-4 border-t border-gray-100`}>
          {allMetrics.map(([name, m]) => (
            <div key={name}>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">
                {formatMetricName(name)}
              </div>
              <div
                className="text-sm font-bold"
                style={{ color: healthColor(m.status) }}
              >
                {formatValue(m.value, m.unit)}
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
