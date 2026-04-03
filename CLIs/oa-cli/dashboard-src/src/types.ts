export interface CronMissedSlot {
  cron_name: string;
  job_id: string;
  slot_time: string;
}

export interface CronUnsupportedSchedule {
  job_id: string;
  cron_name: string;
  schedule_kind: string | null;
  expr: string | null;
  reason: string;
}

export interface CronUnanchoredEveryJob {
  cron_name: string;
  job_id: string;
}

export interface CronPerJobBreakdown {
  expected_slots?: number;
  observed_slots?: number;
  exact_matches?: number;
  late_matches?: number;
  missed?: number;
  missed_slot_times?: string[];
  unexpected_runs?: number;
  supported_schedule?: boolean;
  unsupported_reason?: string;
  phase_policy?: string | null;
}

export interface CronReliabilityBreakdown {
  mode?: string;
  per_job?: Record<string, CronPerJobBreakdown>;
  enabled_jobs?: number;
  observed_jobs?: number;
  total_runs?: number;
  success?: number;
  failed?: number;
  unknown?: number;
  expected_slots?: number;
  observed_slots?: number;
  exact_matches?: number;
  late_matches?: number;
  missed?: number;
  missed_slots?: CronMissedSlot[];
  unexpected_runs?: number;
  unsupported_schedules?: CronUnsupportedSchedule[];
  success_rate_denominator?: number;
  late_tolerance_minutes?: number;
  slot_matching_policy?: string;
  no_anchor_every_policy?: string;
  unanchored_every_jobs?: CronUnanchoredEveryJob[];
  status_details?: Record<string, number>;
  failure_types?: Record<string, number>;
  note?: string;
}

export interface MetricData<TBreakdown = Record<string, unknown>> {
  value: number | null;
  unit: string;
  healthy: number;
  warning: number;
  direction: "higher" | "lower";
  trend: number | null;
  date: string | null;
  breakdown?: TBreakdown | null;
  status: string;
}

export interface GoalMetricHistoryEntry<TBreakdown = Record<string, unknown>> {
  date: string;
  metric: string;
  value: number | null;
  unit: string;
  breakdown?: TBreakdown | null;
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
