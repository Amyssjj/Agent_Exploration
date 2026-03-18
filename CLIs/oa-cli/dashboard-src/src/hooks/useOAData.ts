import { useState, useEffect, useCallback } from "react";
import type { GoalSummary, HealthSummary, TraceSpan, CronRun, AgentActivity } from "../types";

interface OAData {
  goals: GoalSummary[];
  health: HealthSummary | null;
  traces: TraceSpan[];
  cronRuns: CronRun[];
  teamHealth: AgentActivity[];
  goalMetrics: Record<string, unknown[]>;
  isLoading: boolean;
  error: string | null;
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export function useOAData(refreshMs: number = 30000): OAData {
  const [goals, setGoals] = useState<GoalSummary[]>([]);
  const [health, setHealth] = useState<HealthSummary | null>(null);
  const [traces, setTraces] = useState<TraceSpan[]>([]);
  const [cronRuns, setCronRuns] = useState<CronRun[]>([]);
  const [teamHealth, setTeamHealth] = useState<AgentActivity[]>([]);
  const [goalMetrics, setGoalMetrics] = useState<Record<string, unknown[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [g, h, t, c, th, gm] = await Promise.all([
        fetchJSON<GoalSummary[]>("/api/goals"),
        fetchJSON<HealthSummary>("/api/health"),
        fetchJSON<TraceSpan[]>("/api/traces"),
        fetchJSON<CronRun[]>("/api/cron-chart"),
        fetchJSON<AgentActivity[]>("/api/team-health"),
        fetchJSON<Record<string, unknown[]>>("/api/goals/metrics"),
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
    load();
    const timer = setInterval(load, refreshMs);
    return () => clearInterval(timer);
  }, [load, refreshMs]);

  return { goals, health, traces, cronRuns, teamHealth, goalMetrics, isLoading, error };
}
