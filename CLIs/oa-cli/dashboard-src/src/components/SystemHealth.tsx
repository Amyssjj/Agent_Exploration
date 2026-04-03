import { lazy, Suspense } from "react";
import { GoalCard } from "./GoalCard";
import { HealthSummaryStrip } from "./HealthSummaryStrip";
import type { GoalSummary, HealthSummary, CronRun, AgentActivity, GoalMetricHistoryEntry } from "../types";

const GoalDetailSection = lazy(async () => {
  const module = await import("./GoalDetailSection");
  return { default: module.GoalDetailSection };
});

function GoalDetailFallback() {
  return (
    <div className="detail-section space-y-5">
      <div className="flex items-center justify-between">
        <div className="h-6 w-40 rounded-full bg-gray-100" />
        <div className="h-5 w-16 rounded-full bg-gray-100" />
      </div>
      <div className="h-[200px] rounded-2xl bg-gray-50" />
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-24 rounded-2xl bg-gray-50" />
        ))}
      </div>
    </div>
  );
}

interface Props {
  goals: GoalSummary[];
  health: HealthSummary | null;
  goalMetrics: Record<string, GoalMetricHistoryEntry[]>;
  cronRuns: CronRun[];
  teamHealth: AgentActivity[];
}

export function SystemHealth({ goals, health, goalMetrics, cronRuns, teamHealth }: Props) {
  return (
    <div className="space-y-5">
      {/* Overall Health Strip */}
      <HealthSummaryStrip goals={goals} health={health} />

      {/* Two-column: Card (left) + Detail (right) per goal */}
      <div className="space-y-4">
        {goals.map((goal, i) => (
          <div key={goal.id} className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4 items-stretch">
            {/* Left: compact goal card */}
            <div>
              <GoalCard goal={goal} index={i} />
            </div>

            {/* Right: expanded detail with chart */}
            <Suspense fallback={<GoalDetailFallback />}>
              <GoalDetailSection
                goal={goal}
                index={i}
                metrics={goalMetrics[goal.id] || []}
                cronRuns={cronRuns}
                teamHealth={teamHealth}
              />
            </Suspense>
          </div>
        ))}
      </div>

      {/* No goals state */}
      {goals.length === 0 && (
        <div className="glass-card p-12 text-center">
          <p className="text-lg font-semibold text-gray-400">No goals configured</p>
          <p className="text-sm text-gray-300 mt-2">
            Run <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">oa init</code> to set up goals
          </p>
        </div>
      )}
    </div>
  );
}
