import { motion } from "framer-motion";
import type { GoalSummary, HealthSummary } from "../types";

function healthDotColor(status: string): string {
  switch (status) {
    case "healthy": return "#34D399";
    case "warning": return "#FBBF24";
    case "critical": return "#F87171";
    default: return "#CBD5E1";
  }
}

interface Props {
  goals: GoalSummary[];
  health: HealthSummary | null;
}

export function HealthSummaryStrip({ goals, health }: Props) {
  const overallScore = computeOverall(goals);

  return (
    <motion.div
      className="health-strip"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-gray-500">Overall Health</span>
        <span className="text-xl font-bold text-gray-900">
          {overallScore !== null ? `${Math.round(overallScore)}%` : "—"}
        </span>
      </div>

      <div className="flex items-center gap-2">
        {goals.map((goal) => (
          <div key={goal.id} className="flex items-center gap-1" title={`${goal.name}: ${goal.healthStatus}`}>
            <div
              className="w-2.5 h-2.5 rounded-full transition-colors"
              style={{ backgroundColor: healthDotColor(goal.healthStatus) }}
            />
            <span className="text-[9px] text-gray-400 font-mono hidden sm:inline">
              {goal.name.slice(0, 5)}
            </span>
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-400 font-mono">
        {health?.lastCollected || "No data"}
      </div>
    </motion.div>
  );
}

function computeOverall(goals: GoalSummary[]): number | null {
  const scores: number[] = [];
  for (const g of goals) {
    const metrics = Object.values(g.metrics);
    const primary = metrics[0];
    if (!primary || primary.value === null) continue;
    if (primary.unit === "%" && primary.direction !== "lower") {
      scores.push(Math.min(100, Math.max(0, primary.value)));
    } else if (primary.direction === "lower") {
      if (primary.value <= primary.healthy) {
        scores.push(90);
      } else if (primary.value <= primary.warning) {
        scores.push(65);
      } else {
        scores.push(40);
      }
    } else if (primary.value >= primary.healthy) {
      scores.push(90);
    } else if (primary.value >= primary.warning) {
      scores.push(65);
    } else {
      scores.push(40);
    }
  }
  if (!scores.length) return null;
  return scores.reduce((a, b) => a + b, 0) / scores.length;
}
