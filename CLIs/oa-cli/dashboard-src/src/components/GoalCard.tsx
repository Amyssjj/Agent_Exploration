import { motion } from "framer-motion";
import type { GoalSummary } from "../types";
import { localizeGoalName, localizeMetricName, useI18n } from "../i18n";

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
  if (unit === "%" || unit === "percent") return `${Math.round(value * 10) / 10}%`;
  if (unit === "count") return `${Math.round(value)}`;
  return `${Math.round(value * 10) / 10}${unit ? ` ${unit}` : ""}`;
}

interface Props {
  goal: GoalSummary;
  index: number;
}

export function GoalCard({ goal, index }: Props) {
  const { lang } = useI18n();
  const color = healthColor(goal.healthStatus);
  const metrics = Object.entries(goal.metrics);
  const primary = metrics[0];

  return (
    <motion.div
      className="goal-card p-5 h-full"
      style={{ "--goal-health-color": color } as React.CSSProperties}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">{localizeGoalName(goal.name, lang)}</h3>
        <div
          className="w-2.5 h-2.5 rounded-full"
          style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}40` }}
        />
      </div>

      {/* Primary Metric */}
      {primary && (
        <div className="mb-3">
          <div className="text-3xl font-bold" style={{ color }}>
            {formatValue(primary[1].value, primary[1].unit)}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-gray-400 uppercase tracking-wider">
              {localizeMetricName(primary[0], lang)}
            </span>
            <TrendBadge trend={primary[1].trend} />
          </div>
        </div>
      )}

      {/* Sub-metrics */}
      {metrics.length > 1 && (
        <div className="border-t border-gray-100 pt-2 mt-2 space-y-1.5">
          {metrics.slice(1).map(([name, m]) => (
            <div key={name} className="flex items-center justify-between">
              <span className="text-[11px] text-gray-400">{localizeMetricName(name, lang)}</span>
              <span
                className="text-[11px] font-semibold"
                style={{ color: healthColor(m.status) }}
              >
                {formatValue(m.value, m.unit)}
              </span>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

function TrendBadge({ trend }: { trend: number | null }) {
  if (trend === null || trend === undefined) return null;
  if (trend > 0) {
    return <span className="text-[11px] font-medium text-emerald-600">▲ +{trend}</span>;
  }
  if (trend < 0) {
    return <span className="text-[11px] font-medium text-red-500">▼ {trend}</span>;
  }
  return <span className="text-[11px] font-medium text-gray-400">─</span>;
}
