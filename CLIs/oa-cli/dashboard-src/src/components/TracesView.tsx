import { motion } from "framer-motion";
import type { TraceSpan } from "../types";

function formatDateTime(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return (
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" }) +
    " " +
    d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  );
}

interface Props {
  traces: TraceSpan[];
}

export function TracesView({ traces }: Props) {
  if (!traces.length) {
    return (
      <div className="glass-card p-12 text-center">
        <p className="text-lg font-semibold text-gray-400">No traces yet</p>
        <p className="text-sm text-gray-300 mt-2">
          Run <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">oa collect</code> to generate traces
        </p>
      </div>
    );
  }

  // Group by trace_id
  const byTrace: Record<string, TraceSpan[]> = {};
  traces.forEach((t) => {
    if (!byTrace[t.trace_id]) byTrace[t.trace_id] = [];
    byTrace[t.trace_id].push(t);
  });

  const groups = Object.entries(byTrace).slice(0, 20);

  return (
    <div className="space-y-3">
      {groups.map(([traceId, spans], i) => {
        const root = spans.find((s) => !s.parent_span_id) || spans[0];
        const totalMs = spans.reduce((sum, s) => sum + (s.duration_ms || 0), 0);
        const attrs = root.attributes
          ? Object.entries(root.attributes).filter(([k]) => !k.startsWith("_")).slice(0, 5)
          : [];

        return (
          <motion.div
            key={traceId}
            className="glass-card p-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    root.status === "ok" ? "bg-emerald-400" : "bg-red-400"
                  }`}
                />
                <span className="text-sm font-semibold text-gray-800">{root.name}</span>
              </div>
              <span className="text-[11px] text-gray-400 bg-gray-50 px-2 py-0.5 rounded">
                {root.service}
              </span>
            </div>

            <div className="flex gap-4 text-[11px] text-gray-400">
              <span>
                {spans.length} span{spans.length > 1 ? "s" : ""}
              </span>
              <span>{totalMs.toFixed(0)}ms</span>
              <span>{formatDateTime(root.start_time)}</span>
              <span className="font-mono">{traceId.slice(0, 8)}…</span>
            </div>

            {attrs.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {attrs.map(([k, v]) => (
                  <span
                    key={k}
                    className="text-[10px] bg-gray-50 border border-gray-100 px-1.5 py-0.5 rounded"
                  >
                    <b className="text-gray-500">{k}:</b> {String(v)}
                  </span>
                ))}
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
