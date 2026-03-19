import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { TraceSpan } from "../types";

// ══════════════════════════════════════════════════════
// UNIFIED DESIGN SYSTEM
// ══════════════════════════════════════════════════════

type NodeIdentity = "db" | "script" | "cron" | "agent" | "source" | "default";

const IDENTITY_COLORS: Record<NodeIdentity, { fill: string; text: string }> = {
  db:      { fill: "#F5E6D3", text: "#8B6914" },
  script:  { fill: "#B6CEB4", text: "#3A5239" },
  cron:    { fill: "#9ACBD0", text: "#2C5154" },
  agent:   { fill: "#9ACBD0", text: "#2C5154" },
  source:  { fill: "#D6A99D", text: "#5C3A32" },
  default: { fill: "#D9CFC7", text: "#4A4540" },
};

type ShapeKind = "cylinder" | "rect" | "pill" | "rounded";
const IDENTITY_SHAPE: Record<NodeIdentity, ShapeKind> = {
  db: "cylinder", script: "rect", cron: "pill",
  agent: "pill", source: "rounded", default: "rect",
};

const IDENTITY_LABELS: Record<NodeIdentity, string> = {
  db: "Database", script: "Script", cron: "Cron",
  agent: "Agent", source: "Source", default: "Step",
};

const STATUS_COLORS: Record<string, string> = {
  ok: "#059669", error: "#DC2626", unset: "#9CA3AF",
};

function getIdentity(name: string, attrs: Record<string, unknown>): NodeIdentity {
  const lower = name.toLowerCase();
  const step = attrs["step"] as string | undefined;
  const dbOp = attrs["db.operation"] as string | undefined;
  const dbTable = attrs["db.table"] as string | undefined;

  if (step?.includes("store") || step?.includes("write")) return "db";
  if (step?.includes("read") || step?.includes("scan")) return "source";
  if (step?.includes("compute")) return "script";
  if ((dbOp === "write" && dbTable) || lower.includes(" db") || lower.endsWith("_db")) return "db";
  if (lower.includes("scan") || lower.startsWith("read ")) return "source";
  if (lower.includes("compute") || lower.includes("collect")) return "script";
  if (lower.includes("scheduler") || lower.includes("cron")) return "cron";
  if (lower.includes("agent")) return "agent";
  return "default";
}

// ══════════════════════════════════════════════════════
// LAYOUT
// ══════════════════════════════════════════════════════

const NODE_W = 170;
const NODE_H = 38;
const GAP_X = 44;
const GAP_Y = 22;
const COLS = 3;

interface NodePos {
  x: number; y: number; cx: number; cy: number;
  span: TraceSpan; attrs: Record<string, unknown>;
  identity: NodeIdentity; row: number; col: number;
}

function parseAttrs(raw: string | Record<string, unknown> | null): Record<string, unknown> {
  if (!raw) return {};
  if (typeof raw === "object") return raw as Record<string, unknown>;
  try { return JSON.parse(raw); } catch { return {}; }
}

function shortName(name: string): string {
  if (name.length > 22) return name.slice(0, 20) + "…";
  return name;
}

function formatDuration(ms: number | null): string {
  if (ms === null || ms === undefined) return "";
  if (ms < 1) return "<1ms";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function computeLayout(spans: TraceSpan[], rootId: string | null): {
  nodes: NodePos[]; width: number; height: number;
} {
  const children = spans
    .filter(s => s.parent_span_id === rootId)
    .sort((a, b) => a.start_time.localeCompare(b.start_time));
  const nodes: NodePos[] = [];
  let row = 0, col = 0;

  for (const span of children) {
    const x = col * (NODE_W + GAP_X);
    const y = row * (NODE_H + GAP_Y);
    const attrs = parseAttrs(span.attributes);
    nodes.push({
      x, y, cx: x + NODE_W / 2, cy: y + NODE_H / 2,
      span, attrs, identity: getIdentity(span.name, attrs), row, col,
    });
    col++;
    if (col >= COLS && span !== children[children.length - 1]) { col = 0; row++; }
  }

  const maxCol = Math.min(children.length, COLS);
  return {
    nodes,
    width: maxCol * NODE_W + (maxCol - 1) * GAP_X,
    height: (row + 1) * NODE_H + row * GAP_Y,
  };
}

// ══════════════════════════════════════════════════════
// DATA FLOW GRAPH
// ══════════════════════════════════════════════════════

interface FlowGraphNode {
  id: string; label: string; identity: NodeIdentity;
  x: number; y: number; cx: number; cy: number;
}

interface FlowGraphEdge { from: string; to: string; type: string; }

function buildDataFlowGraph(edges: FlowGraphEdge[], spans: TraceSpan[], nodeTypes?: Record<string, string>): {
  nodes: FlowGraphNode[]; edges: FlowGraphEdge[]; width: number; height: number;
} | null {
  if (!edges || edges.length === 0) return null;

  const nodeIds = new Set<string>();
  for (const e of edges) { nodeIds.add(e.from); nodeIds.add(e.to); }

  function inferIdentity(name: string): NodeIdentity {
    const lower = name.toLowerCase();
    if (lower.endsWith(" db") || lower.endsWith("_db") || lower === "goal_metrics" || lower === "cron_runs" || lower === "daily_agent_activity") return "db";
    if (lower.endsWith(".py") || lower.includes("collect_") || lower.includes("compute")) return "script";
    if (lower.includes("cron") || lower.includes("scheduler")) return "cron";
    if (lower.includes("agent")) return "agent";
    if (lower.includes("log") || lower.includes("file") || lower.includes("config") || lower.includes("session") || lower.includes("workspace") || lower.includes("learning")) return "source";
    return "default";
  }

  // Topological sort
  const incoming = new Map<string, Set<string>>();
  const outgoing = new Map<string, Set<string>>();
  for (const id of nodeIds) { incoming.set(id, new Set()); outgoing.set(id, new Set()); }
  for (const e of edges) { incoming.get(e.to)?.add(e.from); outgoing.get(e.from)?.add(e.to); }

  const layers = new Map<string, number>();
  const queue: string[] = [];
  for (const id of nodeIds) {
    if (incoming.get(id)?.size === 0) { layers.set(id, 0); queue.push(id); }
  }
  while (queue.length > 0) {
    const current = queue.shift()!;
    const currentLayer = layers.get(current)!;
    for (const next of outgoing.get(current) || []) {
      if (currentLayer + 1 > (layers.get(next) ?? -1)) {
        layers.set(next, currentLayer + 1);
        queue.push(next);
      }
    }
  }
  for (const id of nodeIds) { if (!layers.has(id)) layers.set(id, 0); }

  const layerGroups = new Map<number, string[]>();
  for (const [id, layer] of layers) {
    if (!layerGroups.has(layer)) layerGroups.set(layer, []);
    layerGroups.get(layer)!.push(id);
  }

  const graphNodes: FlowGraphNode[] = [];
  const maxLayer = Math.max(...layers.values());
  const colWidth = NODE_W + GAP_X;

  for (let layer = 0; layer <= maxLayer; layer++) {
    const ids = layerGroups.get(layer) || [];
    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      graphNodes.push({
        id,
        label: id.length > 20 ? id.slice(0, 18) + "…" : id,
        identity: (nodeTypes?.[id] as NodeIdentity) || inferIdentity(id),
        x: layer * colWidth, y: i * (NODE_H + GAP_Y),
        cx: layer * colWidth + NODE_W / 2,
        cy: i * (NODE_H + GAP_Y) + NODE_H / 2,
      });
    }
  }

  const maxNodesInLayer = Math.max(...[...layerGroups.values()].map(g => g.length));
  return {
    nodes: graphNodes, edges,
    width: (maxLayer + 1) * colWidth - GAP_X,
    height: maxNodesInLayer * (NODE_H + GAP_Y) - GAP_Y,
  };
}

// ══════════════════════════════════════════════════════
// SVG RENDERERS
// ══════════════════════════════════════════════════════

function renderNode(node: NodePos) {
  const { x, y, cx, cy, identity, span, attrs } = node;
  const color = IDENTITY_COLORS[identity];
  const shape = IDENTITY_SHAPE[identity];
  const statusColor = STATUS_COLORS[span.status] || STATUS_COLORS.unset;
  const label = shortName(span.name);
  const duration = formatDuration(span.duration_ms);
  const dbTable = attrs["db.table"] as string | undefined;
  let subText = duration;
  if (identity === "db" && dbTable) subText = dbTable + (duration ? ` · ${duration}` : "");

  return (
    <g key={span.span_id}>
      {shape === "cylinder" ? (
        <>
          <path d={`M ${x} ${y+6} Q ${x} ${y}, ${cx} ${y} Q ${x+NODE_W} ${y}, ${x+NODE_W} ${y+6} L ${x+NODE_W} ${y+NODE_H-6} Q ${x+NODE_W} ${y+NODE_H}, ${cx} ${y+NODE_H} Q ${x} ${y+NODE_H}, ${x} ${y+NODE_H-6} Z`}
            fill={color.fill} stroke="#D4B896" strokeWidth={1} />
          <ellipse cx={cx} cy={y+6} rx={NODE_W/2} ry={6} fill={color.fill} stroke="#D4B896" strokeWidth={1} />
        </>
      ) : shape === "pill" ? (
        <rect x={x} y={y} width={NODE_W} height={NODE_H} rx={NODE_H/2} ry={NODE_H/2} fill={color.fill} />
      ) : shape === "rounded" ? (
        <rect x={x} y={y} width={NODE_W} height={NODE_H} rx={14} ry={14} fill={color.fill} />
      ) : (
        <rect x={x} y={y} width={NODE_W} height={NODE_H} rx={6} ry={6} fill={color.fill} />
      )}
      <circle cx={x+10} cy={cy} r={3} fill={statusColor} />
      <text x={x+18} y={cy-(subText?4:0)} dominantBaseline="central" fill={color.text}
        fontSize="10" fontWeight="600" fontFamily="'Inter', system-ui, sans-serif">{label}</text>
      {subText && (
        <text x={x+18} y={cy+10} dominantBaseline="central" fill={color.text}
          fontSize="8" fontWeight="400" fontFamily="'Inter', system-ui, sans-serif" opacity={0.7}>{subText}</text>
      )}
    </g>
  );
}

function renderGraphNode(node: FlowGraphNode) {
  const color = IDENTITY_COLORS[node.identity];
  const shape = IDENTITY_SHAPE[node.identity];
  const { x, y, cx, cy, label } = node;

  return (
    <g key={node.id}>
      {shape === "cylinder" ? (
        <>
          <path d={`M ${x} ${y+6} Q ${x} ${y}, ${cx} ${y} Q ${x+NODE_W} ${y}, ${x+NODE_W} ${y+6} L ${x+NODE_W} ${y+NODE_H-6} Q ${x+NODE_W} ${y+NODE_H}, ${cx} ${y+NODE_H} Q ${x} ${y+NODE_H}, ${x} ${y+NODE_H-6} Z`}
            fill={color.fill} stroke="#D4B896" strokeWidth={1} />
          <ellipse cx={cx} cy={y+6} rx={NODE_W/2} ry={6} fill={color.fill} stroke="#D4B896" strokeWidth={1} />
        </>
      ) : shape === "pill" ? (
        <rect x={x} y={y} width={NODE_W} height={NODE_H} rx={NODE_H/2} ry={NODE_H/2} fill={color.fill} />
      ) : shape === "rounded" ? (
        <rect x={x} y={y} width={NODE_W} height={NODE_H} rx={14} ry={14} fill={color.fill} />
      ) : (
        <rect x={x} y={y} width={NODE_W} height={NODE_H} rx={6} ry={6} fill={color.fill} />
      )}
      <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central"
        fill={color.text} fontSize="10" fontWeight="600" fontFamily="'Inter', system-ui, sans-serif">{label}</text>
    </g>
  );
}

function renderArrow(from: NodePos, to: NodePos, i: number) {
  const color = "#C4C9CE";
  if (from.row === to.row) {
    const x1 = from.x + NODE_W, x2 = to.x;
    return (
      <g key={`arrow-${i}`}>
        <line x1={x1} y1={from.cy} x2={x2-6} y2={to.cy} stroke={color} strokeWidth={1.5} />
        <polygon points={`${x2-6},${to.cy-4} ${x2},${to.cy} ${x2-6},${to.cy+4}`} fill={color} />
      </g>
    );
  } else {
    const x1 = from.cx, y1 = from.y + NODE_H, x2 = to.cx, y2 = to.y;
    const midY = (y1 + y2) / 2;
    return (
      <g key={`arrow-${i}`}>
        <path d={`M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2-6}`}
          stroke={color} strokeWidth={1.5} fill="none" />
        <polygon points={`${x2-4},${y2-6} ${x2},${y2} ${x2+4},${y2-6}`} fill={color} />
      </g>
    );
  }
}

function renderGraphEdge(edge: FlowGraphEdge, fromNode: FlowGraphNode, toNode: FlowGraphNode, i: number) {
  const color = "#C4C9CE";
  const x1 = fromNode.x + NODE_W, y1 = fromNode.cy;
  const x2 = toNode.x, y2 = toNode.cy;

  if (Math.abs(y1 - y2) < 2) {
    return (
      <g key={`edge-${i}`}>
        <line x1={x1} y1={y1} x2={x2-6} y2={y2} stroke={color} strokeWidth={1.5} />
        <polygon points={`${x2-6},${y2-4} ${x2},${y2} ${x2-6},${y2+4}`} fill={color} />
      </g>
    );
  } else {
    const midX = (x1 + x2) / 2;
    return (
      <g key={`edge-${i}`}>
        <path d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2-6} ${y2}`}
          stroke={color} strokeWidth={1.5} fill="none" />
        <polygon points={`${x2-6},${y2-4} ${x2},${y2} ${x2-6},${y2+4}`} fill={color} />
      </g>
    );
  }
}

// ══════════════════════════════════════════════════════
// IDENTITY LEGEND
// ══════════════════════════════════════════════════════

function IdentityLegend({ identities }: { identities: NodeIdentity[] }) {
  const unique = [...new Set(identities)].filter(i => i !== "default");
  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {unique.map(id => (
        <div key={id} className="flex items-center gap-1.5">
          {IDENTITY_SHAPE[id] === "cylinder" ? (
            <svg width="14" height="12" viewBox="0 0 14 12">
              <ellipse cx="7" cy="3" rx="6" ry="2.5" fill={IDENTITY_COLORS[id].fill} stroke="#D4B896" strokeWidth={0.5} />
              <rect x="1" y="3" width="12" height="6" fill={IDENTITY_COLORS[id].fill} />
              <ellipse cx="7" cy="9" rx="6" ry="2.5" fill={IDENTITY_COLORS[id].fill} stroke="#D4B896" strokeWidth={0.5} />
            </svg>
          ) : IDENTITY_SHAPE[id] === "pill" ? (
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: IDENTITY_COLORS[id].fill }} />
          ) : (
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: IDENTITY_COLORS[id].fill }} />
          )}
          <span className="text-[9px] text-gray-400 font-medium">{IDENTITY_LABELS[id]}</span>
        </div>
      ))}
    </div>
  );
}

// ══════════════════════════════════════════════════════
// DETAIL PANEL
// ══════════════════════════════════════════════════════

function getDepth(span: TraceSpan, allSpans: TraceSpan[]): number {
  let depth = 0;
  let parentId = span.parent_span_id;
  while (parentId) {
    depth++;
    const parent = allSpans.find(s => s.span_id === parentId);
    parentId = parent?.parent_span_id || null;
  }
  return depth;
}

function TraceDetail({ spans: rawSpans, onClose }: { spans: TraceSpan[]; onClose: () => void }) {
  const spans = [...rawSpans].sort((a, b) => a.start_time.localeCompare(b.start_time));
  const root = spans.find(s => !s.parent_span_id) || spans[0];
  const rootAttrs = parseAttrs(root.attributes);

  return (
    <>
      <motion.div
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose}
      />
      <motion.div
        className="fixed top-0 right-0 h-full w-[560px] max-w-[90vw] bg-white shadow-2xl z-50 overflow-y-auto"
        initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 30, stiffness: 300 }}
      >
        <div className="p-6 space-y-6">
          <button onClick={onClose}
            className="absolute top-5 right-5 w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700 transition-colors text-sm font-bold cursor-pointer">
            ✕
          </button>

          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">🔭</span>
            <div>
              <h2 className="text-lg font-bold text-gray-800">{root.name}</h2>
              <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
                <span>{formatDate(root.start_time)} {formatTime(root.start_time)}</span>
                <span>·</span>
                <span>{spans.length} spans</span>
                <span>·</span>
                <span>{formatDuration(spans.reduce((s, sp) => s + (sp.duration_ms || 0), 0))} total</span>
              </div>
            </div>
          </div>

          {Object.keys(rootAttrs).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(rootAttrs)
                .filter(([k]) => k !== "data_flow_edges" && k !== "node_types")
                .map(([k, v]) => (
                  <span key={k} className="text-[10px] px-2.5 py-1 rounded-full bg-gray-50 text-gray-600 font-mono border border-gray-100">
                    {k}: {String(typeof v === "object" ? JSON.stringify(v) : v).slice(0, 80)}
                  </span>
                ))}
            </div>
          )}

          <div className="border-t border-gray-100 my-4" />

          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-[0.15em] mb-3">
            Execution Trace
          </h3>
          <div className="relative pl-4">
            <div className="absolute left-[19px] top-[20px] bottom-[20px] w-0.5 bg-gray-200" />
            {spans.map((span) => {
              const depth = getDepth(span, spans);
              const attrs = parseAttrs(span.attributes);
              const identity = getIdentity(span.name, attrs);
              const idColor = IDENTITY_COLORS[identity];
              const sColor = STATUS_COLORS[span.status] || STATUS_COLORS.unset;

              return (
                <div key={span.span_id} className="relative flex items-start hover:bg-gray-50/40 transition-colors rounded-lg"
                  style={{ paddingLeft: depth * 20 }}>
                  <div className="relative shrink-0 flex items-start" style={{ width: 32 }}>
                    <div className="relative z-10 w-3 h-3 rounded-full border-2 border-white shadow-sm"
                      style={{ backgroundColor: sColor, marginTop: 14, marginLeft: 1 }} />
                    <div className="w-2.5 h-2.5 rounded-sm"
                      style={{ backgroundColor: idColor.fill, marginTop: 15, marginLeft: 4 }} />
                  </div>
                  <div className="flex-1 min-w-0 py-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-gray-700">{span.name}</span>
                      <span className="text-[10px] text-gray-400 font-mono shrink-0">{formatDuration(span.duration_ms)}</span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-gray-50 text-gray-400 font-mono shrink-0">
                        {IDENTITY_LABELS[identity]}
                      </span>
                    </div>
                    {Object.keys(attrs).length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {Object.entries(attrs)
                          .filter(([k]) => k !== "data_flow_edges" && k !== "node_types")
                          .slice(0, 6)
                          .map(([k, v]) => (
                            <span key={k} className="text-[9px] px-1.5 py-0.5 rounded bg-gray-50 text-gray-400 font-mono">
                              {k}={String(typeof v === "object" ? JSON.stringify(v) : v).slice(0, 60)}
                            </span>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="border-t border-gray-100 mt-6 pt-4">
            <div className="flex items-center gap-4">
              <span className="text-[9px] text-gray-400 uppercase tracking-wider font-semibold">Legend:</span>
              {(["db", "script", "cron", "source", "agent"] as NodeIdentity[]).map(id => (
                <div key={id} className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: IDENTITY_COLORS[id].fill }} />
                  <span className="text-[9px] text-gray-400">{IDENTITY_LABELS[id]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </>
  );
}

// ══════════════════════════════════════════════════════
// MAIN TRACE FLOW CARD
// ══════════════════════════════════════════════════════

interface TraceFlowCardProps {
  spans: TraceSpan[];
  traceId: string;
  index: number;
}

export function TraceFlowCard({ spans, traceId, index }: TraceFlowCardProps) {
  const [showDetail, setShowDetail] = useState(false);
  const root = spans.find(s => !s.parent_span_id) || spans[0];
  const rootAttrs = parseAttrs(root.attributes);
  const statusColor = STATUS_COLORS[root.status] || STATUS_COLORS.unset;
  const totalMs = spans.reduce((sum, s) => sum + (s.duration_ms || 0), 0);

  const linearLayout = computeLayout(spans, root?.span_id || null);
  const dataFlowEdges = rootAttrs.data_flow_edges as FlowGraphEdge[] | undefined;
  const dataFlowNodeTypes = rootAttrs.node_types as Record<string, string> | undefined;
  const dataFlowGraph = dataFlowEdges ? buildDataFlowGraph(dataFlowEdges, spans, dataFlowNodeTypes) : null;
  const pad = 12;

  return (
    <>
      <motion.div
        className="relative cursor-pointer group"
        style={{
          borderRadius: "16px",
          background: "rgba(255, 255, 255, 0.55)",
          backdropFilter: "blur(24px)",
          border: "1px solid rgba(255, 255, 255, 0.6)",
          boxShadow: "0 4px 24px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.03)",
        }}
        initial={{ opacity: 0, y: 20, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, delay: index * 0.06 }}
        whileHover={{
          y: -4,
          boxShadow: "0 12px 40px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04)",
        }}
        onClick={() => setShowDetail(true)}
      >
        <div className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <span className="text-2xl">🔭</span>
              <div>
                <h3 className="text-sm font-bold text-gray-800 leading-tight">
                  {root.name.replace(/_/g, " ")}
                </h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor }} />
                    {root.status === "ok" ? "Success" : root.status}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[9px] font-medium px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600">
                    🔭 Traced
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 text-[10px] text-gray-400 mb-3">
            <span className="flex items-center gap-1"><span className="text-gray-300">⬡</span> {spans.length} spans</span>
            <span className="flex items-center gap-1"><span className="text-gray-300">⏱</span> {formatDuration(totalMs)}</span>
            <span className="flex items-center gap-1"><span className="text-gray-300">📅</span> {formatDate(root.start_time)} {formatTime(root.start_time)}</span>
          </div>

          {dataFlowGraph ? (
            <>
              <svg width={dataFlowGraph.width + pad*2}
                viewBox={`${-pad} ${-pad} ${dataFlowGraph.width+pad*2} ${dataFlowGraph.height+pad*2}`}
                className="overflow-visible" style={{ maxWidth: "100%" }}>
                {dataFlowGraph.edges.map((edge, i) => {
                  const from = dataFlowGraph.nodes.find(n => n.id === edge.from);
                  const to = dataFlowGraph.nodes.find(n => n.id === edge.to);
                  if (!from || !to) return null;
                  return renderGraphEdge(edge, from, to, i);
                })}
                {dataFlowGraph.nodes.map(node => renderGraphNode(node))}
              </svg>
              <IdentityLegend identities={dataFlowGraph.nodes.map(n => n.identity)} />
            </>
          ) : linearLayout.nodes.length > 0 ? (
            <>
              <svg width={linearLayout.width + pad*2}
                viewBox={`${-pad} ${-pad} ${linearLayout.width+pad*2} ${linearLayout.height+pad*2}`}
                className="overflow-visible" style={{ maxWidth: "100%" }}>
                {linearLayout.nodes.map((node, i) => {
                  if (i === 0) return null;
                  return renderArrow(linearLayout.nodes[i-1], node, i);
                })}
                {linearLayout.nodes.map(node => renderNode(node))}
              </svg>
              <IdentityLegend identities={linearLayout.nodes.map(n => n.identity)} />
            </>
          ) : null}
        </div>

        <div className="absolute inset-x-0 bottom-0 h-8 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-[9px] text-gray-300 font-medium">Click to expand trace →</span>
        </div>
      </motion.div>

      <AnimatePresence>
        {showDetail && <TraceDetail spans={spans} onClose={() => setShowDetail(false)} />}
      </AnimatePresence>
    </>
  );
}
