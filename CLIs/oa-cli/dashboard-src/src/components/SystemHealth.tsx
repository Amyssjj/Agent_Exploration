import { motion } from "framer-motion";
import { GoalCard } from "./GoalCard";
import { GoalDetailSection } from "./GoalDetailSection";
import { HealthSummaryStrip } from "./HealthSummaryStrip";
import type { GoalSummary, HealthSummary, CronRun, AgentActivity } from "../types";
import { useI18n } from "../i18n";

interface Props {
  goals: GoalSummary[];
  health: HealthSummary | null;
  goalMetrics: Record<string, unknown[]>;
  cronRuns: CronRun[];
  teamHealth: AgentActivity[];
}

export function SystemHealth({ goals, health, goalMetrics, cronRuns, teamHealth }: Props) {
  const { t } = useI18n();
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
            <GoalDetailSection
              goal={goal}
              index={i}
              metrics={goalMetrics[goal.id] || []}
              cronRuns={cronRuns}
              teamHealth={teamHealth}
            />
          </div>
        ))}
      </div>

      {/* No goals state */}
      {goals.length === 0 && (
        <div className="glass-card p-12 text-center">
          <p className="text-lg font-semibold text-gray-400">{t("health.noGoals")}</p>
          <p className="text-sm text-gray-300 mt-2">
            {t("health.noGoalsHint")} <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">oa init</code>
          </p>
        </div>
      )}
    </div>
  );
}
