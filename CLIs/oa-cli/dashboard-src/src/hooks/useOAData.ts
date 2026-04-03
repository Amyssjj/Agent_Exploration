import { useState, useEffect, useCallback } from "react";
import type {
  GoalSummary,
  HealthSummary,
  TraceSpan,
  CronRun,
  AgentActivity,
  GoalMetricHistoryEntry,
} from "../types";
import { getVisualTestFixture, isVisualTestMode } from "../lib/runtimeFlags";

interface OAData {
  goals: GoalSummary[];
  health: HealthSummary | null;
  traces: TraceSpan[];
  cronRuns: CronRun[];
  teamHealth: AgentActivity[];
  goalMetrics: Record<string, GoalMetricHistoryEntry[]>;
  isLoading: boolean;
  error: string | null;
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export function useOAData(refreshMs: number = 30000): OAData {
  const visualTestMode = isVisualTestMode();
  const visualFixture = getVisualTestFixture();
  const hasVisualFixture = visualFixture !== null;
  const [goals, setGoals] = useState<GoalSummary[]>(() => visualFixture?.goals ?? []);
  const [health, setHealth] = useState<HealthSummary | null>(() => visualFixture?.health ?? null);
  const [traces, setTraces] = useState<TraceSpan[]>(() => visualFixture?.traces ?? []);
  const [cronRuns, setCronRuns] = useState<CronRun[]>(() => visualFixture?.cronRuns ?? []);
  const [teamHealth, setTeamHealth] = useState<AgentActivity[]>(() => visualFixture?.teamHealth ?? []);
  const [goalMetrics, setGoalMetrics] = useState<Record<string, GoalMetricHistoryEntry[]>>(
    () => visualFixture?.goalMetrics ?? {},
  );
  const [isLoading, setIsLoading] = useState(!hasVisualFixture);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [g, h, t, c, th, gm] = await Promise.all([
        fetchJSON<GoalSummary[]>("/api/goals"),
        fetchJSON<HealthSummary>("/api/health"),
        fetchJSON<TraceSpan[]>("/api/traces"),
        fetchJSON<CronRun[]>("/api/cron-chart"),
        fetchJSON<AgentActivity[]>("/api/team-health"),
        fetchJSON<Record<string, GoalMetricHistoryEntry[]>>("/api/goals/metrics"),
      ]);
      setGoals(g);
      setHealth(h);
      setTraces(t);
      setCronRuns(c);
      setTeamHealth(th);
      setGoalMetrics(gm);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasVisualFixture) {
      return;
    }

    load();
    if (visualTestMode) {
      return;
    }
    const timer = setInterval(load, refreshMs);
    return () => clearInterval(timer);
  }, [hasVisualFixture, load, refreshMs, visualTestMode]);

  return { goals, health, traces, cronRuns, teamHealth, goalMetrics, isLoading, error };
}
