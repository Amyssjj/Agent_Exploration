---
title: "OpenClaw vs ClawTeam: Multi-Agent Comparison Research"
date: 2026-03-26
topics: [agent-collaboration]
status: active
---

# OpenClaw vs ClawTeam: Multi-Agent Comparison Research

> **Date:** 2026-03-26
> **Context:** Comparative analysis of OpenClaw's local multi-agent infrastructure vs. the open-source [ClawTeam](https://github.com/HKUDS/ClawTeam) project (HKUDS, v0.2.0, MIT license, ~3,710 stars, launched 2026-03-18).

---

## 1. Architecture Overview

| Dimension | OpenClaw (Local) | ClawTeam (Open Source) |
|-----------|-----------------|----------------------|
| **Model** | Gateway-managed hierarchy (main -> orchestrator -> leaf, max depth 2) | Leader-worker hierarchy (1 leader + N workers) |
| **Agent runtime** | Native subagents + ACP harness (Claude Code, Codex, Gemini CLI) | Tmux-wrapped CLI agents (Claude Code, Codex, nanobot, Gemini, Kimi, Qwen, OpenCode) |
| **Isolation** | Per-session state; optional sandbox (Docker) | Git worktree per worker (real branches, merge semantics) |
| **Language** | TypeScript (ESM) | Python 3.10+ |
| **Storage** | In-memory registry + JSONL session files | Filesystem JSON (one file per task/message) |
| **Infrastructure** | Gateway process (always-on) | tmux + filesystem (zero-infrastructure) |

---

## 2. Multi-Agent Collaboration

| | OpenClaw | ClawTeam |
|--|---------|----------|
| **Communication** | Direct tool calls (`sessions_send`), auto-announce on completion, ping-pong turns (up to 15) | File-based mailbox (async inboxes), optional ZeroMQ P2P, typed messages |
| **Task management** | Implicit via subagent spawning (run/session modes), no formal task queue | Explicit task store with status, priority, dependencies, blocking/unblocking chains |
| **Cross-agent awareness** | Session history tool (`sessions_history`) to read transcripts | Auto-injected context: teammate diffs, file ownership maps, cross-branch logs |
| **Plan approval** | Not built-in (relies on human or leader judgment) | Formal plan submission/approval workflow via mailbox |

### OpenClaw Communication Detail

- **Subagent spawn** (`sessions_spawn`): One-shot `run` or persistent `session` mode with thread binding
- **Agent-to-agent** (`sessions_send`): Direct messaging with configurable ping-pong turns (0-15), disabled by default for safety
- **Auto-announce**: On subagent completion, results automatically delivered to requester's channel
- **Hooks**: `subagent_spawning`, `subagent_spawned`, `subagent_ended` for lifecycle coordination

### ClawTeam Communication Detail

- **Mailbox**: Each agent has a filesystem inbox directory; messages are typed JSON files (plain, join_request, plan_approval, shutdown, idle, broadcast)
- **Transport**: `FileTransport` (default, zero-dep) or `P2PTransport` (ZeroMQ with heartbeat/peer discovery)
- **Claimed message pattern**: Messages renamed `.json` -> `.consumed` during processing, quarantined to `dead_letters/` on parse failure

---

## 3. Workflow and Automation

| | OpenClaw | ClawTeam |
|--|---------|----------|
| **Scheduling** | Built-in cron tool, heartbeat system, remote triggers | None built-in (agents poll for work) |
| **Templates** | Agent skills (`.agents/skills/*.md`) for domain workflows | TOML team templates (`hedge-fund`, `software-dev`, `research-paper`, `code-review`, `strategy-room`) |
| **Lifecycle** | Hook system (before/after agent start, tool calls, LLM I/O, 20+ hook types) | on-exit hooks, idle reporting, structured shutdown protocol |
| **Spawning** | Programmatic via gateway API with depth/concurrency enforcement | `clawteam launch <template>` -- single command spawns entire team |

### ClawTeam Templates (Notable)

Declarative TOML files define entire team topologies:
```toml
# Example: software-dev.toml
[team]
name = "dev-team"
lead = "architect"

[[members]]
name = "architect"
role = "lead"
prompt = "You are the lead architect..."

[[members]]
name = "backend"
role = "worker"
prompt = "You implement backend features..."

[[tasks]]
subject = "Design API"
owner = "architect"

[[tasks]]
subject = "Implement endpoints"
owner = "backend"
blocked_by = ["Design API"]
```

One command (`clawteam launch software-dev --team myteam --goal "..."`) spawns the full topology.

---

## 4. Reliability and Safety

| | OpenClaw | ClawTeam |
|--|---------|----------|
| **Concurrency control** | Per-agent child limits (default 5), global lane cap (default 8), depth limits | OS file locks (advisory), atomic writes, stale lock detection |
| **Loop prevention** | Ping-pong turn limits, repeat-pattern detection, circuit breakers | None (relies on prompt instructions) |
| **Error recovery** | Announce retry with exponential backoff, session archive after timeout | Dead letter quarantine for malformed messages; no auto-restart |
| **Git safety** | Extensive CLAUDE.md rules (no stash, no branch switch, no force push, scope commits) | Each worker on isolated worktree branch -- conflicts deferred to merge time |
| **Sandboxing** | Configurable per-agent Docker sandbox, inheritance rules | None (agents run with full host access) |
| **Authentication** | OAuth credentials, session binding service | None (any local process can read/write `~/.clawteam/`) |

---

## 5. Pros and Cons

### OpenClaw Strengths

1. **Deep integration** -- agents communicate via structured tool calls, not prompt-based CLI invocations; more reliable than hoping agents parse and execute embedded shell commands
2. **Rich automation** -- cron, heartbeat, remote triggers, comprehensive hook system (20+ hook types)
3. **Safety-first** -- sandbox isolation, depth limits, turn limits, allowlists, tool scope restrictions by depth level
4. **Scalable communication** -- direct inter-agent messaging without filesystem polling
5. **Production-grade** -- battle-tested gateway with session persistence, retry logic, event streams, exponential backoff

### OpenClaw Weaknesses

1. **No formal task dependency graph** -- subagent spawning is ad-hoc; no built-in task status tracking, priority, or blocking chains
2. **No cross-agent context injection** -- agents can read transcripts but don't automatically get "what teammates are working on"
3. **No git worktree isolation by default** -- multi-agent safety relies on convention (CLAUDE.md rules) rather than enforcement
4. **No declarative team templates** -- can't launch a pre-defined team topology with one command
5. **Tight coupling** -- works primarily within the OpenClaw ecosystem

### ClawTeam Strengths

1. **Agent-agnostic** -- wraps any CLI coding agent; not tied to one ecosystem
2. **Git worktree isolation** -- true branch-per-worker with real merge semantics, eliminates an entire class of conflicts
3. **Explicit task management** -- status, priority, dependencies, ownership, duration tracking
4. **Cross-agent context** -- automatic awareness of what teammates changed and where files overlap (`agent_diff()`, `file_owners()`, `cross_branch_log()`)
5. **Declarative team templates** -- one TOML file + one command = full multi-agent team
6. **Zero infrastructure** -- filesystem + tmux, no Docker/Redis/cloud needed
7. **Web UI dashboard** -- real-time monitoring via SSE with Gource visualization
8. **MCP integration** -- Model Context Protocol server for external client integration

### ClawTeam Weaknesses

1. **Prompt-based coordination is fragile** -- relies on AI agents correctly interpreting CLI instructions embedded in their system prompt
2. **Polling-based** -- 1s filesystem polling, no push notifications or event-driven wakeup
3. **Single-machine only** (v0.2) -- no distributed support yet (Redis transport planned for v0.4)
4. **No sandboxing** -- agents have full host access
5. **No loop/runaway prevention** -- no turn limits or circuit breakers
6. **No authentication** -- any local process can read/write task/message files
7. **Young project** (v0.2, launched 2026-03-18) -- missing auth, multi-user, database backend
8. **tmux dependency** -- limits portability, adds setup friction
9. **File-based storage scalability** -- one file per message/task may hit inode limits at scale
10. **Cost tracking is self-reported** -- no automatic provider billing integration

---

## 6. What We Can Learn from ClawTeam

### High Priority

1. **Explicit task store with dependencies** (see companion design doc)
   - ClawTeam's task system (status, priority, `blocked_by`/`blocks` chains, ownership) is more structured than our spawn-and-forget model
   - Directly addresses the "nudge agents to hand off" pain point

2. **Cross-agent context injection**
   - `agent_diff()`, `file_owners()`, `cross_branch_log()` give each agent awareness of teammates' changes
   - Could be injected into subagent prompts to reduce merge conflicts and duplicated work

### Medium Priority

3. **Git worktree-per-agent isolation**
   - Instead of relying on CLAUDE.md safety rules, enforce isolation by default
   - OpenClaw already has `EnterWorktree` as a tool; could make it the default for multi-agent spawns

4. **Declarative team templates**
   - TOML-based team topology enables reproducible multi-agent setups
   - Could be added as a `tasks.plan` template system

### Lower Priority / Nice-to-Have

5. **Plan approval workflow** -- formal submit/review/approve cycle for worker plans
6. **Dead letter quarantine** -- preserve failed messages with error metadata instead of dropping
7. **Web dashboard** -- real-time task board visualization (SSE-based)

### What NOT to Copy

- **File-per-task storage** -- we already have a registry; a second store creates sync issues
- **Prompt-based coordination** -- injecting CLI commands into prompts is fragile; tool-based approach is more reliable
- **Advisory file locks** -- our in-process registry with single-writer gateway is inherently safer
- **Polling-based communication** -- our hook-driven events are zero-latency

---

## 7. ClawTeam Technical Details

### Key Code Locations

| Component | Path |
|-----------|------|
| Team manager | `clawteam/team/manager.py` |
| Agent identity | `clawteam/identity.py` |
| Tmux backend | `clawteam/spawn/tmux_backend.py` |
| CLI adapters | `clawteam/spawn/adapters.py` |
| Workspace (worktree) | `clawteam/workspace/manager.py` |
| Task store | `clawteam/store/file.py` |
| Mailbox | `clawteam/team/mailbox.py` |
| Plan approval | `clawteam/team/plan.py` |
| File transport | `clawteam/transport/file.py` |
| P2P transport | `clawteam/transport/p2p.py` |
| Cross-agent context | `clawteam/workspace/context.py` |
| Lifecycle | `clawteam/team/lifecycle.py` |
| Snapshot | `clawteam/team/snapshot.py` |
| Cost tracking | `clawteam/team/costs.py` |
| Web board | `clawteam/board/` |
| MCP server | `clawteam/mcp/` |
| Templates | `clawteam/templates/*.toml` |

### Tech Stack

- Python 3.10+, `typer` (CLI), `pydantic` (models), `rich` (TUI)
- Optional: `pyzmq` (P2P transport)
- tmux (process management), git worktrees (isolation)
- stdlib `http.server` + SSE (web dashboard)
- All storage: local JSON files under `~/.clawteam/`

### Roadmap (from Chinese docs)

- Phase 2 (v0.4): Redis transport
- Phase 3 (v0.5): Shared state across machines
- Phase 4 (v0.6): Multi-user authentication
