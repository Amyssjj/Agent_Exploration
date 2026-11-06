import { createContext, useContext, useEffect, useMemo, useState } from "react";

export type Lang = "zh" | "en";

type DictNode = { [key: string]: string | DictNode };

const STORAGE_KEY = "oa-dashboard-lang";

const dict = {
  zh: {
    app: {
      title: "OA 仪表盘",
      subtitle: "我们的系统有变好吗？",
      footer: "OA · 运营分析",
      loading: "加载中",
      connectionError: "连接错误",
      ensureServer: "请确认服务已运行：",
      tabs: {
        systemHealth: "系统健康",
        mechanism: "运行机制",
      },
      lang: {
        zh: "中文",
        en: "English",
      },
    },
    health: {
      overallHealth: "总体健康度",
      noData: "暂无数据",
      noGoals: "未配置目标",
      noGoalsHint: "运行 oa init 以完成目标初始化",
    },
    goal: {
      metrics: "指标说明",
      dataStartingSoon: "数据采集中",
      collectDaily: "建议每日运行",
      metricDefinition: "指标定义",
      datasource: "数据源",
      definition: "定义",
      calculation: "计算方式",
      purpose: "用途",
      cronStartingTomorrow: "Cron 运行追踪将从下一次采集开始显示",
      cronStartingHint: "记录到按时段数据后，这里会显示组合图表",
      teamLoading: "团队健康数据加载中...",
      daysActivePerAgent: "各 Agent 活跃天数",
      sess: "次会话",
      daySuffix: "天",
    },
    chart: {
      successRate: "成功率",
      succeeded: "成功",
      failed: "失败",
      missed: "缺失",
      activeAgents: "活跃 Agent 数",
      sessions: "会话数",
      traced: "已追踪",
      success: "成功",
      clickToExpand: "点击展开 Trace →",
      executionTrace: "执行链路",
      legend: "图例",
      spans: "个 Span",
      total: "总计",
      latestRuns: "最近一次运行",
      pipelines: "条流水线",
      pipelineTraces: "流水线 Trace",
    },
    mechanism: {
      howItWorks: "工作方式",
      collect: "采集",
      collectType: "数据流水线",
      collectDesc: "扫描 OpenClaw 中的 cron 运行、agent 会话和 memory 文件。",
      analyze: "分析",
      analyzeType: "目标流水线",
      analyzeDesc: "执行每个目标的流水线，计算指标、趋势和健康状态。",
      visualize: "可视化",
      visualizeType: "仪表盘",
      visualizeDesc: "实时展示健康卡片、趋势图和 trace 流向。",
      footer: "运行机制视图 · 数据流与流水线追踪",
    },
    identity: {
      db: "数据库",
      script: "脚本",
      cron: "定时任务",
      agent: "Agent",
      source: "数据源",
      default: "步骤",
    },
    builtinGoal: {
      cron_reliability: "Cron 可靠性",
      team_health: "团队健康",
      "Cron Reliability": "Cron 可靠性",
      "Team Health": "团队健康",
    },
    metric: {
      success_rate: "成功率",
      active_agent_count: "活跃 Agent 数",
      memory_discipline: "记忆记录率",
      Success_Rate: "成功率",
      Succeeded: "成功",
      Failed: "失败",
      Missed: "缺失",
      Sessions: "会话数",
      "#DAA (Daily Active Agents)": "#DAA（日活跃 Agent）",
      "Sessions per Day": "每日会话数",
      "Memory Logged": "已写入记忆",
      "Per-Agent Activity (bar chart)": "按 Agent 活跃度（柱状图）",
    },
  },
  en: {
    app: {
      title: "OA Dashboard",
      subtitle: "Is our machine getting better?",
      footer: "OA — Operational Analytics",
      loading: "Loading",
      connectionError: "Connection Error",
      ensureServer: "Ensure the API server is running:",
      tabs: {
        systemHealth: "System Health",
        mechanism: "Mechanism",
      },
      lang: {
        zh: "中文",
        en: "English",
      },
    },
    health: {
      overallHealth: "Overall Health",
      noData: "No data",
      noGoals: "No goals configured",
      noGoalsHint: "Run oa init to set up goals",
    },
    goal: {
      metrics: "Metrics",
      dataStartingSoon: "Data collection starting soon",
      collectDaily: "Run oa collect daily",
      metricDefinition: "Metrics Definition",
      datasource: "Datasource",
      definition: "Definition",
      calculation: "Calculation",
      purpose: "Purpose",
      cronStartingTomorrow: "Cron run tracking starting tomorrow",
      cronStartingHint: "Combined chart will appear once per-slot data is recorded",
      teamLoading: "Team health data loading...",
      daysActivePerAgent: "Days Active per Agent",
      sess: "sess",
      daySuffix: "d",
    },
    chart: {
      successRate: "Success Rate",
      succeeded: "Succeeded",
      failed: "Failed",
      missed: "Missed",
      activeAgents: "Active Agents",
      sessions: "Sessions",
      traced: "Traced",
      success: "Success",
      clickToExpand: "Click to expand trace →",
      executionTrace: "Execution Trace",
      legend: "Legend",
      spans: "spans",
      total: "total",
      latestRuns: "latest runs",
      pipelines: "pipelines",
      pipelineTraces: "Pipeline Traces",
    },
    mechanism: {
      howItWorks: "How It Works",
      collect: "Collect",
      collectType: "Data Pipeline",
      collectDesc: "Scans OpenClaw for cron runs, agent sessions, and memory files.",
      analyze: "Analyze",
      analyzeType: "Goal Pipelines",
      analyzeDesc: "Runs each goal's pipeline to compute metrics, trends, and health status.",
      visualize: "Visualize",
      visualizeType: "Dashboard",
      visualizeDesc: "Serves real-time health cards, trend charts, and trace flows.",
      footer: "Mechanism View — data flow + pipeline traces",
    },
    identity: {
      db: "Database",
      script: "Script",
      cron: "Cron",
      agent: "Agent",
      source: "Source",
      default: "Step",
    },
    builtinGoal: {
      cron_reliability: "Cron Reliability",
      team_health: "Team Health",
      "Cron Reliability": "Cron Reliability",
      "Team Health": "Team Health",
    },
    metric: {
      success_rate: "Success Rate",
      active_agent_count: "Active Agent Count",
      memory_discipline: "Memory Discipline",
      Success_Rate: "Success Rate",
      Succeeded: "Succeeded",
      Failed: "Failed",
      Missed: "Missed",
      Sessions: "Sessions",
      "#DAA (Daily Active Agents)": "#DAA (Daily Active Agents)",
      "Sessions per Day": "Sessions per Day",
      "Memory Logged": "Memory Logged",
      "Per-Agent Activity (bar chart)": "Per-Agent Activity (bar chart)",
    },
  },
} as const;

interface I18nContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (path: string) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function getNestedValue(source: DictNode, path: string): string | undefined {
  const value = path.split(".").reduce<string | DictNode | undefined>((acc, key) => {
    if (!acc || typeof acc === "string") return acc;
    return acc[key];
  }, source);
  return typeof value === "string" ? value : undefined;
}

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    if (typeof window === "undefined") return "zh";
    const saved = window.localStorage.getItem(STORAGE_KEY);
    return saved === "en" || saved === "zh" ? saved : "zh";
  });

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, lang);
  }, [lang]);

  const value = useMemo<I18nContextValue>(() => ({
    lang,
    setLang,
    t: (path: string) => getNestedValue(dict[lang] as unknown as DictNode, path) || path,
  }), [lang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within LangProvider");
  return ctx;
}

export function localizeGoalName(name: string, lang: Lang): string {
  return getNestedValue(dict[lang].builtinGoal as unknown as DictNode, name) || name;
}

export function localizeMetricName(name: string, lang: Lang): string {
  const normalized = name.replace(/\s+/g, "_");
  return (
    getNestedValue(dict[lang].metric as unknown as DictNode, name) ||
    getNestedValue(dict[lang].metric as unknown as DictNode, normalized) ||
    name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

export function localizeIdentityLabel(key: string, lang: Lang): string {
  return getNestedValue(dict[lang].identity as unknown as DictNode, key) || key;
}

export function formatShortDate(date: string, lang: Lang): string {
  const locale = lang === "zh" ? "zh-CN" : "en-US";
  return new Date(date + "T00:00:00").toLocaleDateString(locale, { month: "short", day: "numeric" });
}

export function formatDateTime(date: string, lang: Lang): string {
  const locale = lang === "zh" ? "zh-CN" : "en-US";
  const dt = new Date(date);
  return `${dt.toLocaleDateString(locale, { month: "short", day: "numeric" })} ${dt.toLocaleTimeString(locale, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: lang !== "zh",
  })}`;
}

export function formatTime(date: string, lang: Lang): string {
  const locale = lang === "zh" ? "zh-CN" : "en-US";
  return new Date(date).toLocaleTimeString(locale, {
    hour: "numeric",
    minute: "2-digit",
    hour12: lang !== "zh",
  });
}
