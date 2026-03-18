export interface MetricData {
  value: number | null;
  unit: string;
  healthy: number;
  warning: number;
  trend: number | null;
  date: string | null;
  status: string;
}

export interface GoalSummary {
  id: string;
  name: string;
  builtin: boolean;
  metrics: Record<string, MetricData>;
  sparkline: { date: string; value: number }[];
  healthStatus: string;
}

export interface HealthSummary {
  overall: string;
  goals: number;
  healthy: number;
  warning: number;
  critical: number;
  lastCollected: string | null;
}

export interface TraceSpan {
  span_id: string;
  trace_id: string;
  parent_span_id: string | null;
  name: string;
  service: string;
  status: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  attributes: Record<string, unknown> | null;
}

export interface CronRun {
  date: string;
  cron_name: string;
  status: string;
  job_id: string;
}

export interface AgentActivity {
  date: string;
  agent_id: string;
  session_count: number;
  memory_logged: number;
  last_active: string | null;
}
