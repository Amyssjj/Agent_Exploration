import type {
  AgentActivity,
  CronRun,
  GoalMetricHistoryEntry,
  GoalSummary,
  HealthSummary,
  TraceSpan,
} from "../types";

export interface VisualTestFixtureData {
  goals: GoalSummary[];
  health: HealthSummary | null;
  traces: TraceSpan[];
  cronRuns: CronRun[];
  teamHealth: AgentActivity[];
  goalMetrics: Record<string, GoalMetricHistoryEntry[]>;
}

declare global {
  interface Window {
    __OA_VISUAL_TEST_FIXTURE__?: VisualTestFixtureData;
  }
}

export function isVisualTestMode(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  return new URLSearchParams(window.location.search).has("visual-test");
}

export function getVisualTestFixture(): VisualTestFixtureData | null {
  if (!isVisualTestMode() || typeof window === "undefined") {
    return null;
  }

  return window.__OA_VISUAL_TEST_FIXTURE__ ?? null;
}
