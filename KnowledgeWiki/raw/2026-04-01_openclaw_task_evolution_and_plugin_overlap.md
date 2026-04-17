---
title: "OpenClaw Core Task Evolution (3/30–3/31) & Task-Orchestrator Plugin Overlap Analysis"
date: 2026-04-01
topics: [task-orchestration]
status: active
---

# OpenClaw Core Task Evolution (3/30–3/31) & Task-Orchestrator Plugin Overlap Analysis

> **Date:** 2026-04-01
> **Status:** Research analysis
> **Scope:** OpenClaw core task system improvements + overlap with `extensions/task-orchestrator/` plugin
> **Goal:** Establish robust, reliable, consistent multi-agent task management — plugin must be self-contained

---

## 1. What OpenClaw Core Improved (March 30–31, 2026)

Six major changes landed in the core task system:

### 1.1 Owner-Key Task Access Boundaries

**Commit:** `7cd0ff2d88` — refactor(tasks): add owner-key task access boundaries

The biggest architectural change. Tasks now have two-part ownership:

- **`ownerKey`** — the actual owner identifier (session key or system identifier)
- **`scopeKind`** — either `"session"` (requires owner validation) or `"system"` (no requester needed)

New access-controlled query layer in `task-owner-access.ts`:
- `listTasksForRelatedSessionKeyForOwner()` — only returns tasks the caller owns
- `findTaskByRunIdForOwner()` — validates ownership before returning
- `getTaskByIdForOwner()` — access-controlled task lookup
- `resolveTaskForLookupTokenForOwner()` — multi-step lookup with ownership validation

Each runtime gets properly scoped:
| Runtime | ownerKey | scopeKind |
|---------|----------|-----------|
| ACP runs | `requesterInternalKey` | `session` |
| Subagent runs | `requesterSessionKey` | `session` |
| Cron jobs | `system:cron:{jobId}` | `system` |
| CLI execution | system-scoped | `system` |

Index changes: `taskIdsBySessionKey` → split into `taskIdsByOwnerKey` + `taskIdsByRelatedSessionKey`.

### 1.2 Atomic Task-Store Writes

**Commit:** `66413487c8` — fix(tasks): make task-store writes atomic

Critical reliability improvement:
- SQLite: `PRAGMA synchronous = NORMAL` → `PRAGMA synchronous = FULL` (every write fully synced before returning)
- New compound operations: `upsertTaskWithDeliveryStateToSqlite()` and `deleteTaskAndDeliveryStateFromSqlite()` — atomically update/delete task + delivery state together
- Runtime prefers compound operations with fallback to individual writes

### 1.3 Flow Registry Removal

**Commit:** `1a313caff3` — refactor(tasks): remove flow registry layer

~3,400 lines deleted across 14 files. The separate "flow" concept (flow-registry, flow-runtime, `/flows` command) was consolidated into the task model. Simpler mental model — tasks now handle the lifecycle previously split between flows and tasks.

### 1.4 Agent-to-Agent Turns Raised

**Commit:** `ff97c7702d` — agent-to-agent: raise max ping-pong turns from 5 to 15

`session.agentToAgent.maxPingPongTurns` config (0–15 range). Enables more complex multi-agent exchanges without hitting the cap.

### 1.5 Hook Session Key Rebinding

**Commit:** `1ca12ec8bf` — fix(hooks): rebind hook agent session keys to the target agent

When hooks triggered agents, session keys weren't properly rebound — hook agents could inherit the caller's namespace. Fix: `normalizeHookDispatchSessionKey()` rebinds non-target-agent prefixes (e.g., `agent:main:slack:channel:c123` → `agent:hooks:slack:channel:c123`). Each agent now gets its own isolated session-scoped namespace.

### 1.6 Task Count in `/status`

**Commit:** `58ee76fc84` — feat(status): show session task counts in slash status

New observability: active task count, total task count, runtime type, latest task title and progress summary — all visible in `/status` output.

### 1.7 Task Execution Seam Integration

**Commits:** `a23b4dd5bc`, `2a72a6d507`, `cc278a76a4`

Task executor now routes through plugin runtime seam, enabling bundled/external plugins to provide task execution without modifying core.

### 1.8 Runtime-Internal Export Boundary

New `src/tasks/runtime-internal.ts` — clean public API for task registry operations (CRUD, lifecycle, status, queries, owner-scoped variants).

---

## 2. Task-Orchestrator Plugin Capabilities Summary

Our plugin (`extensions/task-orchestrator/`) provides:

| Layer | Capabilities |
|-------|-------------|
| **Data Model** | Goals (hierarchical), Tasks (11 states), Attempts, Checkpoints, Handoffs, Workflows |
| **Dependency Graph** | `blockedBy` array with edge-triggered resolution — tasks become "ready" when all blockers complete |
| **Dispatch Modes** | `spawn` (subagent), `manual`, `approval`, `notify`, `wake` |
| **Worker Contract** | System prompt injection with checkpoint/handoff rules, blocker escalation protocol |
| **Structured Handoff** | Mandatory `tasks.handoff` with deliverableState, summary, artifactPaths, recommendedNextStep |
| **Upstream Failure** | Per-task `onUpstreamFailure`: `skip` / `wait` / `continue` |
| **Approval Gates** | Human-in-the-loop via `before_tool_call` hook, 5-min timeout |
| **Stall Detection** | Configurable threshold (default 1hr), auto-marks stalled |
| **Context Injection** | Upstream outputs + last 5 session messages injected into dependents |
| **Board** | Full visual board injected into every prompt via `before_prompt_build` |
| **Workflow Templates** | Save/instantiate/export/import with variable interpolation |
| **Retry** | Restart (clear state) vs Resume (include checkpoint context) |
| **Persistence** | Own SQLite store with 5 tables + indexes |

---

## 3. Overlap Analysis

| Capability | OpenClaw Core (3/31) | Our Plugin | Overlap? |
|---|---|---|---|
| **Task CRUD** | Registry with SQLite | Own SQLite store | **Yes — dual stores** |
| **Owner scoping** | `ownerKey` + `scopeKind` | Session-key based (`orch:{agentId}:{taskId}`) | **Parallel patterns** |
| **Atomic writes** | `PRAGMA synchronous = FULL` + compound ops | Standard SQLite transactions | **Gap in plugin** |
| **Subagent spawning** | Built-in subagent registry | Via `api.runtime.subagent.run()` | **Plugin uses core API** ✓ |
| **Task status tracking** | Running/terminal/lost | 11 states incl. stalled, awaiting_approval | **Plugin extends** |
| **Progress updates** | `setTaskProgressById` | `tasks.checkpoint` with phase/percent/blocker | **Plugin is richer** |
| **Dependency graph** | None — tasks are flat | `blockedBy` with edge-triggered resolution | **Plugin only** |
| **Structured handoff** | No explicit contract | Mandatory `tasks.handoff` | **Plugin only** |
| **Upstream failure policy** | None | `skip` / `wait` / `continue` per task | **Plugin only** |
| **Approval gates** | None | Human-in-the-loop via hook | **Plugin only** |
| **Stall detection** | None | Configurable threshold | **Plugin only** |
| **Workflow templates** | Removed (flow registry) | Save/instantiate/export/import | **Plugin fills the gap** |
| **Worker contract** | No prescribed protocol | Detailed system prompt | **Plugin only** |
| **Context injection** | No cross-task context | Upstream outputs injected | **Plugin only** |
| **Board visualization** | Task count in `/status` | Full board in every prompt | **Plugin extends** |
| **Hierarchical goals** | None | Parent/child goals with cascade | **Plugin only** |
| **Retry with resume** | None | Restart vs resume modes | **Plugin only** |

---

## 4. Architecture Relationship

```
┌─────────────────────────────────────────────────────┐
│                  YOUR PLUGIN                         │
│  (Orchestration Brain)                               │
│                                                      │
│  Goals → Dependency Graph → Dispatch → Monitor       │
│  Worker Contract · Checkpoints · Handoffs            │
│  Approval Gates · Stall Detection · Templates        │
│  Board Visualization · Context Chaining              │
│                                                      │
│  Own SQLite: goals, tasks, attempts, workflows       │
├─────────────────────────────────────────────────────┤
│              Plugin SDK Boundary                     │
│  api.runtime.subagent.run()                          │
│  api.on("subagent_ended", ...)                       │
│  api.on("before_prompt_build", ...)                  │
│  api.registerTool() / api.registerCommand()          │
├─────────────────────────────────────────────────────┤
│                 OPENCLAW CORE                        │
│  (Execution Substrate)                               │
│                                                      │
│  Task Registry · Owner-Key Scoping · Atomic Writes   │
│  Subagent Lifecycle · Session Isolation              │
│  Hook Dispatch · Agent-to-Agent Comms                │
│  /status Observability                               │
└─────────────────────────────────────────────────────┘
```

**Core** = "run this subagent, track its lifecycle, scope its access."
**Plugin** = "what to run, in what order, with what context, and what to do when things fail."

---

## 5. Recommendations for Self-Contained Plugin

### 5.1 Adopt Core's Durability Pattern

Add `PRAGMA synchronous = FULL` to the plugin's SQLite store (one line). Core proved this prevents corruption on crashes — free reliability win.

### 5.2 Align Session Key Scoping

Plugin currently builds `orch:{agentId}:{taskId}:{attempt}` session keys manually. Core now provides `ownerKey` + `scopeKind`. Consider:
- Setting `ownerKey` on subagent runs dispatched by the plugin
- Using `scopeKind: "session"` for user-triggered goals, `scopeKind: "system"` for cron/template-triggered workflows

This lets core's `/status` and access control see plugin tasks in a unified view.

### 5.3 Keep Separate Stores (Don't Merge)

Despite the dual-store overlap, **keep the plugin's own SQLite store** for orchestration-specific data (goals, dependencies, workflows, checkpoints, handoffs). Reasons:
- Self-containment: plugin works independently of core task schema changes
- Core's task model is flat — forcing dependency graphs into it would fight the design
- Plugin uninstall cleanly removes all orchestration state
- No coupling to core internals that break on upgrades

### 5.4 Keep What Core Doesn't Have

These are legitimately plugin concerns and should remain plugin-owned:
- Dependency graph + resolution logic
- Worker contract / system prompt injection
- Approval gates
- Stall detection
- Workflow templates with variable interpolation
- Board visualization
- Upstream failure policies
- Structured handoff protocol
- Retry with resume (checkpoint context)

### 5.5 Watch for Core Convergence

Core removed the flow registry but may re-introduce orchestration primitives. Monitor:
- Any new `src/tasks/` files related to dependencies or workflows
- Changes to `task-registry.types.ts` that add graph-like fields
- New task dispatch modes in core

If core adds dependency support, consider adapting to use it rather than maintaining a parallel implementation.

### 5.6 Import Boundary Compliance

Current plugin correctly uses only `openclaw/plugin-sdk/*` imports. **Keep it this way.** Do not import:
- `src/tasks/runtime-internal.ts` (tempting but breaks on upgrades)
- `src/tasks/task-registry.ts` (core internals)
- Any `src/**` paths

---

## 6. Core Bug: `subagent_ended` Does Not Fire for Plugin SDK Runs

**Filed:** openclaw/openclaw#59164

### The Problem

`api.on("subagent_ended", handler)` never fires for sessions created via `api.runtime.subagent.run()`. The hook only fires for the internal `sessions_spawn` tool path.

### Root Cause

`api.runtime.subagent.run()` dispatches to the gateway `"agent"` method (`server-plugins.ts:328`), which calls `agentCommandFromIngress()` directly (`server-methods/agent.ts:264`). This path **never calls `registerSubagentRun()`**, so no `SubagentRunRecord` is created, and `emitSubagentEndedHookOnce()` is never triggered.

### Workaround: Worker Self-Reports

Instead of relying on the broken hook, the plugin now completes tasks directly in `recordHandoff()` when the worker calls `tasks.handoff` with `deliverableState: "complete"`:

1. Worker calls `tasks.handoff` with `deliverableState: "complete"` → task finalized immediately
2. Worker calls `tasks.handoff` with `deliverableState: "partial"` → task stays running, stall detection catches it
3. `onSubagentEnded()` is now idempotent — if the worker already self-reported, it skips state transitions

This makes the plugin **independent of the broken hook** while remaining compatible if core fixes it later.

### 5.2 Status: ownerKey Alignment Deferred

The Plugin SDK's `SubagentRunParams` does not expose `ownerKey` or `scopeKind`. This would require a new SDK seam — filed as a future enhancement, not a plugin-side change.

---

## 7. Changes Applied (2026-04-01)

1. **5.1 adopted** — `PRAGMA synchronous = FULL` added to `extensions/task-orchestrator/src/store.ts`
2. **Worker self-report completion** — `recordHandoff()` in `resolver.ts` now finalizes tasks on `deliverableState: "complete"` (completes task, finalizes attempt, cascades dependents)
3. **Idempotent `onSubagentEnded()`** — skips state transitions if task already completed via handoff
4. **Core bug filed** — openclaw/openclaw#59164

---

## 8. Summary

OpenClaw 3/30–3/31 hardened the **execution substrate**: ownership scoping, atomic writes, session isolation, and observability. It deliberately stayed flat and unopinionated about orchestration (even removing the flow registry).

Our task-orchestrator plugin fills the **orchestration layer**: dependency graphs, structured handoffs, approval gates, stall detection, workflow templates, and context chaining.

**They are complementary, not competing.** The self-contained plugin strategy is the right architecture: use core's SDK surface for subagent lifecycle and hooks, own everything else in the plugin's SQLite store, and stay behind the `openclaw/plugin-sdk/*` import boundary.

## Appendix
 ---
  Current State: What's Fragile

  1. Implicit dependency chains using time offsets
  7:00  coo-data-collection  (must finish before...)
  7:00  coo-daily-summary    (must finish before...)
  7:15  coo-digest-publish   (assumes summary is ready)
  If data-collection runs long, summary stages stale data. If summary runs long, publish fires on nothing. The
  15-minute gap is a hope, not a guarantee.

  2. No retry on transient failures
  Yesterday's cron history shows 4 failures — LLM timeouts, rate limits, overloaded API. These are all transient.
  Nothing retries them. The coo-issue-fixer failed 3 times in a row before succeeding on the 4th scheduled run (8h
  later).

  3. Two disconnected databases, no feedback loop
  - system_monitor.db records cron run outcomes but can't trigger retries
  - task-orchestrator.db has retry/dependency machinery but doesn't know about cron jobs
  - Mission Control dashboard shows failures you notice manually

  4. LLM interpretation layer
  Every cron job sends a message → agent interprets it → calls tools. The agent is a probabilistic intermediary
  between a deterministic schedule and deterministic work.

  ---
  Proposed Architecture: Plugin DB as Central Brain

  ┌─────────────────────────────────────────────────────────┐
  │              task-orchestrator.db (CENTRAL)              │
  │                                                         │
  │  schedules        →  when to run (cron expressions)     │
  │  workflow_templates → what to run (reusable plans)       │
  │  goals + tasks    →  execution state + dependencies     │
  │  attempts         →  retry history + failure tracking    │
  ├─────────────────────────────────────────────────────────┤
  │              system_monitor.db (OBSERVABILITY)           │
  │                                                         │
  │  cron_runs        →  historical record (read-only view) │
  │  goal_metrics     →  business metrics                   │
  │  feedback/issues  →  quality tracking                   │
  └─────────────────────────────────────────────────────────┘

  Wake mechanisms (dumb alarm clocks):
    • 1 openclaw cron job: "orchestrator:tick" every 15min
    • agent_end hook: opportunistic scan on every agent turn

  What Changes

  Before (7 independent cron jobs):
  cron → agent → LLM interprets → maybe does the right thing → no retry
  cron → agent → LLM interprets → maybe does the right thing → no retry
  cron → agent → LLM interprets → maybe does the right thing → no retry
  ...×7

  After (1 cron tick + workflow templates):
  cron tick → before_dispatch intercepts → scanSchedules()
    → due workflow found → instantiate as goal with dependency graph
      → task A (data-collection) dispatches
      → task B (daily-summary) blocked by A, auto-dispatches when A completes
      → task C (digest-publish) blocked by B, auto-dispatches when B completes
    → failure? → retry policy kicks in (auto_once for transient, manual for persistent)
    → all done? → log to system_monitor.db for dashboard

  The 7 Jobs Become 3 Workflow Templates

  ┌───────────────┬───────────────────────────────────────────────────┬────────────────────────────────────────┐
  │   Workflow    │             Tasks (with dependencies)             │                Schedule                │
  ├───────────────┼───────────────────────────────────────────────────┼────────────────────────────────────────┤
  │ daily-ops     │ data-collection → daily-summary → digest-publish  │ 0 7 * * *                              │
  ├───────────────┼───────────────────────────────────────────────────┼────────────────────────────────────────┤
  │ maintenance   │ context-audit ∥ issue-fixer ∥ learning-notes-sync │ 0 8 * * * + issue-fixer repeats 0      │
  │               │  (parallel)                                       │ 12,16,20 * * *                         │
  ├───────────────┼───────────────────────────────────────────────────┼────────────────────────────────────────┤
  │ weekly-review │ digest-trend-review (depends on accumulated       │ 0 9 * * 2,5                            │
  │               │ daily-ops data)                                   │                                        │
  └───────────────┴───────────────────────────────────────────────────┴────────────────────────────────────────┘

  Key wins:
  - daily-summary can't run until data-collection succeeds — deterministic, not time-offset
  - digest-publish can't run until daily-summary succeeds
  - Transient LLM failures get retryPolicy: "auto_once" — automatic retry without waiting 4+ hours for the next
  cron slot
  - One cron tick replaces 7 — less gateway load, simpler config
  - Mission Control reads from task-orchestrator.db for richer status (task-level, not just pass/fail)

  What Stays the Same

  - Mission Control dashboard — just reads from a richer source
  - system_monitor.db — keeps accumulating metrics, the plugin writes completion records there too
  - Worker contract — subagents still get checkpoint/handoff protocol

  ---
  Want me to implement this? The work would be:

  1. schedules table + scan logic in the plugin
  2. Convert the 3 workflow templates from your 7 cron jobs
  3. before_dispatch handler for "orchestrator:tick" interception
  4. Retire 6 of 7 cron jobs, replace with 1 tick
  5. Bridge write — plugin logs completions to system_monitor.db so Mission Control dashboard still works