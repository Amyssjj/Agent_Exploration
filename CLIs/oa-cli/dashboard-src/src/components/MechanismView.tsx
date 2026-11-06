import { motion } from "framer-motion";
import { TraceFlowCard } from "./TraceFlowCard";
import type { GoalSummary, TraceSpan, CronRun } from "../types";
import { useI18n } from "../i18n";

interface Props {
  goals: GoalSummary[];
  traces: TraceSpan[];
  cronRuns: CronRun[];
}

export function MechanismView({ goals, traces, cronRuns }: Props) {
  const { t } = useI18n();
  // Group traces by trace_id
  const traceGroups: Record<string, TraceSpan[]> = {};
  traces.forEach((t) => {
    if (!traceGroups[t.trace_id]) traceGroups[t.trace_id] = [];
    traceGroups[t.trace_id].push(t);
  });

  // Deduplicate: keep only the LATEST trace per root span name (goal pipeline)
  const latestByGoal = new Map<string, [string, TraceSpan[]]>();
  for (const [traceId, spans] of Object.entries(traceGroups)) {
    const root = spans.find(s => !s.parent_span_id) || spans[0];
    const goalName = root.name;
    const existing = latestByGoal.get(goalName);
    if (!existing || root.start_time > (existing[1].find(s => !s.parent_span_id) || existing[1][0]).start_time) {
      latestByGoal.set(goalName, [traceId, spans]);
    }
  }
  const pipelineTraces = [...latestByGoal.values()];

  // Group cron runs by name
  const cronByName: Record<string, CronRun[]> = {};
  cronRuns.forEach((r) => {
    if (!cronByName[r.cron_name]) cronByName[r.cron_name] = [];
    cronByName[r.cron_name].push(r);
  });

  return (
    <div className="space-y-6">
      {/* Three-Layer Accountability */}
      <motion.div
        className="glass-card p-5"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-[0.15em] mb-4">
          {t("mechanism.howItWorks")}
        </h2>

        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl bg-violet-50/80 ring-1 ring-violet-100 p-4 text-center">
            <div className="text-2xl mb-1">📊</div>
            <div className="text-sm font-bold text-gray-800">{t("mechanism.collect")}</div>
            <div className="text-[10px] font-mono text-violet-600 uppercase tracking-wider mt-0.5">
              {t("mechanism.collectType")}
            </div>
            <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
              {t("mechanism.collectDesc")}
            </p>
          </div>
          <div className="rounded-xl bg-blue-50/80 ring-1 ring-blue-100 p-4 text-center relative">
            <div className="text-2xl mb-1">⚙️</div>
            <div className="text-sm font-bold text-gray-800">{t("mechanism.analyze")}</div>
            <div className="text-[10px] font-mono text-blue-600 uppercase tracking-wider mt-0.5">
              {t("mechanism.analyzeType")}
            </div>
            <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
              {t("mechanism.analyzeDesc")}
            </p>
            <div className="absolute left-0 top-1/2 -translate-x-full flex items-center px-1">
              <span className="text-gray-300">←</span>
            </div>
            <div className="absolute right-0 top-1/2 translate-x-full flex items-center px-1">
              <span className="text-gray-300">→</span>
            </div>
          </div>
          <div className="rounded-xl bg-emerald-50/80 ring-1 ring-emerald-100 p-4 text-center">
            <div className="text-2xl mb-1">🖥️</div>
            <div className="text-sm font-bold text-gray-800">{t("mechanism.visualize")}</div>
            <div className="text-[10px] font-mono text-emerald-600 uppercase tracking-wider mt-0.5">
              {t("mechanism.visualizeType")}
            </div>
            <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
              {t("mechanism.visualizeDesc")}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Pipeline Traces — SVG Flow Charts */}
      {pipelineTraces.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-[0.15em]">
              🔭 {t("chart.pipelineTraces")}
            </h3>
            <span className="text-[9px] text-gray-300 font-mono">
              {pipelineTraces.length} {t("chart.pipelines")} · {t("chart.latestRuns")}
            </span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {pipelineTraces.map(([traceId, spans], i) => (
              <TraceFlowCard key={traceId} spans={spans} traceId={traceId} index={i} />
            ))}
          </div>
        </motion.div>
      )}

      {/* Footer */}
      <motion.div
        className="text-center py-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
      >
        <span className="text-[10px] text-gray-300 font-mono tracking-wider uppercase">
          {t("mechanism.footer")}
        </span>
      </motion.div>
    </div>
  );
}

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
