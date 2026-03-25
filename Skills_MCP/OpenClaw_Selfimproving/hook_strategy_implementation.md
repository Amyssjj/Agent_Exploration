# Knowledge Flywheel v2 — Hook Strategy

**Date:** March 22, 2026
**Status:** Deployed & Live
**Plugin:** `proactive-learning` v3 (`~/openclaw/extensions/proactive-learning/index.ts`)

---

## Executive Summary

The Knowledge Flywheel is a plugin that makes our AI agent team learn from experience. When an agent discovers something unexpected (e.g., "Discord modals don't support select dropdowns"), that learning gets captured in markdown files and automatically delivered to other agents at the right moment — preventing the same mistake from happening twice.

The plugin uses **7 hooks** across 3 OpenClaw lifecycle events. No LLM calls anywhere in the plugin — everything is deterministic (keywords, regex, hashmap lookups).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Session Lifecycle                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐                                        │
│  │ before_prompt_build │──→ Hook 1: Domain Injection         │
│  └──────────────────┘      (planning-time knowledge)         │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐                                        │
│  │  before_tool_call │──→ Hook 2: Route-Based Lookup         │
│  │                   │──→ Hook 3: Mechanical Enforcement     │
│  │                   │──→ Hook 7: Exec Safety Enforcement    │
│  └──────────────────┘      (execution-time knowledge +       │
│           │                 guardrails)                       │
│           ▼                                                  │
│  ┌──────────────────┐                                        │
│  │  after_tool_call  │──→ Hook 4: Failure Logging            │
│  │                   │──→ Hook 6: Auto #agent-comms Post     │
│  └──────────────────┘      (post-execution learning +        │
│           │                 coordination)                     │
│           ▼                                                  │
│  ┌──────────────────┐                                        │
│  │    agent_end      │──→ Hook 5: Cron Failure Reporter      │
│  └──────────────────┘      (session-end detection)           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## The Three Layers

### Layer 1: Planning (before_prompt_build)

Knowledge delivered **before the agent starts thinking**. Influences what the agent decides to do.

### Layer 2: Execution (before_tool_call)

Knowledge delivered **between the agent's decision and the actual tool call**. Can adjust how the agent executes, or block dangerous actions entirely.

### Layer 3: Post-Execution (after_tool_call / agent_end)

Captures failures and coordinates follow-up actions. Feeds data back into the system for future improvement.

---

## Detailed Hook Reference

### Hook 1: Domain Injection (`before_prompt_build`)

**Why:** Agents need domain-specific knowledge during planning. A YouTube video agent needs story arc rules; a COO agent needs session_send protocols.

**What:** Reads curated markdown files from `shared_learnings/` and injects them into the system prompt based on keyword or provenance matching.

**How:**
1. Extract text from the user's prompt (turn 1) or recent messages (turn 2+)
2. Match against domain keyword lists (e.g., "manim", "render", "venv" → `yt_render_rules.md`)
3. Check agent targeting (e.g., `yt_*` domains only inject for the `youtube` agent)
4. For provenance-based domains (like `session_send`), check if the message came from a specific tool
5. Build injection context from matched curated files
6. Return via `appendSystemContext` (cacheable, no context decay)

**Domains (8 configured):**

| Domain | File | Target Agent | Matching |
|--------|------|-------------|----------|
| story_arc | yt_story_arc_rules.md | youtube | Keywords: topic, story, arc, narrative |
| voiceover | yt_voiceover_rules.md | youtube | Keywords: voiceover, script, 金句, 语气 |
| design | yt_design_rules.md | youtube | Keywords: design, layout, font, visual |
| scene_spec | yt_scene_spec_rules.md | youtube | Keywords: scene, spec, card, animation |
| render | yt_render_rules.md | youtube | Keywords: render, manim, python, venv |
| production | yt_production_rules.md | youtube | Keywords: audio, ffmpeg, concat, mix |
| sharing | yt_sharing_rules.md | youtube | Keywords: deliver, share, upload |
| session_send | protocols_session_send.md | All agents | Provenance: sourceTool=sessions_send |

**Key design decisions:**
- Keyword matching is simple but reliable — no LLM needed, no false positives from semantic similarity
- Provenance-based matching is fully deterministic — checks message metadata, not content
- Curated file cache means files are read once per gateway lifecycle (fast)
- Per-agent targeting prevents irrelevant knowledge injection (YouTube rules don't pollute COO)

---

### Hook 2: Route-Based Learning Lookup (`before_tool_call`) ⭐ NEW

**Why:** The old Hook 2 used semantic search (embeddings) to find relevant learnings before every tool call. This caused:
- 4-20 second latency per tool call
- False positives (e.g., `session_status` call matching "gotcha" learnings at 0.71 score)
- Broke Discord modal interactions (3-second timeout exceeded)

**What:** Replaced semantic search with a deterministic hashmap. Each learning entry in `shared_learnings/*.md` has a `Route:` field declaring exactly which tool + parameter patterns it applies to. At gateway startup, all learnings are parsed into a `Map<toolName, RoutedLearning[]>`. On each tool call, O(1) lookup finds matching learnings.

**How:**
1. **Startup:** `parseAllLearnings(dir)` reads all `*.md` files in `shared_learnings/`
2. Splits each file by `### ` headings to find individual entries
3. Extracts `Route:`, `The Rule:`, and `Citations:` fields from each entry
4. Parses `tool=<name>` from Route, builds hashmap keyed by tool name
5. **Per tool call:** Looks up `routeMap.get(event.toolName)` → gets candidate learnings
6. `matchesRoute()` checks parameter conditions against actual tool call params
7. Matched learnings are logged for future citation tracking

**Route syntax examples:**
```
Route: tool=exec, params.command contains "git push"
Route: tool=message, params.filePath OR params.media
Route: tool=sessions_send
Route: none (general knowledge, not routed)
```

**Matching logic:**
- `tool=X` — must match tool name exactly
- `params.field contains "pattern"` — string inclusion check on param value
- `params.X OR params.Y` — existence check (param is not null/undefined)
- No conditions after tool name — matches all calls to that tool

**File watcher:**
- `fs.watch()` on `shared_learnings/` directory with 1-second debounce
- Any file change → hashmap rebuilt from scratch
- No gateway restart needed when adding/editing learnings

**Key design decisions:**
- **0ms lookup** vs 4-20s semantic search — eliminates the latency problem entirely
- **Zero false positives** — exact route matching, no fuzzy similarity scores
- **Agent writes Route at discovery time** — the agent has the most context about when a learning applies
- **Markdown files** — human readable, git trackable, agent writable, no DB needed
- **Fail-open** — any error in route lookup is caught and swallowed, never blocks tool calls

**Current status (March 22):**
- ✅ 67 learnings across 15 files have Route fields backfilled
- ✅ Deployed and live after gateway restart
- ✅ File watcher active for live reload
- ⏳ Citation tracking (Hook 4 enhancement) deferred — needs lazy-init search manager

---

### Hook 3: Mechanical Tool Enforcement (`before_tool_call`)

**Why:** The YouTube agent must use a Python virtual environment for Manim rendering, and needs the DISPLAY env var set. Without enforcement, it repeatedly uses system Python (breaking imports) or forgets DISPLAY (breaking rendering).

**What:** Automatically rewrites tool call parameters for specific agents. No LLM decision involved.

**How:**
1. Only fires for `exec` / `run_command` tool calls
2. Checks if the calling agent has enforcement rules configured
3. **Command rewriting:** Replaces patterns in the command string (e.g., `python3 -m manim` → `.venv/bin/python -m manim`)
4. **Environment injection:** Adds required env vars if not already set (e.g., `DISPLAY=:0`)
5. Returns mutated params — the tool call proceeds with corrected parameters

**Configured rewrites:**

| Agent | Rewrite | Env |
|-------|---------|-----|
| youtube | `python3 -m manim` → `.venv/bin/python -m manim` | `DISPLAY=:0` |
| youtube | `python -m manim` → `.venv/bin/python -m manim` | |

**Key design decisions:**
- Hooks are laws, prompts are suggestions — agent can't forget or override enforcement
- Only mutates, never blocks (the agent's intent was correct, just the execution was wrong)
- Per-agent config prevents cross-contamination

---

### Hook 4: Failure Logging (`after_tool_call`)

**Why:** When a tool call fails, we need to capture it for analysis. The heartbeat and issue-fixer crons use this data to detect patterns and fix recurring problems.

**What:** On any tool call error, inserts a record into the `issues` table in `system_monitor.db`.

**How:**
1. Checks `event.error` — no-op on success
2. Builds an issue record with: tool name, error message, agent ID, session ID, timestamp
3. SQL-escapes all strings (doubles single quotes) to prevent injection
4. Inserts via `sqlite3` CLI (execSync, 5-second timeout)
5. Fire-and-forget — errors in logging itself are caught and swallowed

**Issue format:**
- ID: `HOOK-<timestamp>`
- Type: `inter_agent`
- Reporter: `after_tool_call`
- Status: `open` (picked up by issue-fixer cron)

**Future enhancement:** Post-failure semantic search to find learnings that *would have helped*. This feeds the citation tracking system (Approach C — most honest attribution, no false positives).

---

### Hook 5: Cron Failure Auto-Reporter (`agent_end`)

**Why:** Cron jobs can fail silently — the job technically "ran" but accomplished nothing (e.g., exec approval timeout). The heartbeat can't detect these "successful but unproductive" crons.

**What:** Fires at the end of every agent session. If the trigger was `cron` and the session failed, inserts an issue with deduplication.

**How:**
1. Checks `ctx.trigger === "cron"` and `event.success === false`
2. Dedupe check: queries for existing open issues with same agent+title pattern from last 24h
3. If no duplicate exists, inserts a new `CRON-<timestamp>` issue
4. Fire-and-forget — never throws from agent_end

**Key design decisions:**
- Deterministic: no LLM, no heuristics — fires on every failed cron run
- Deduplication prevents issue flooding from repeated cron failures
- Fills the gap where heartbeat's cron check only sees "job ran" but not "job succeeded"

---

### Hook 6: Auto #agent-comms Posting (`after_tool_call`)

**Why:** Agents were supposed to post in #agent-comms when communicating with each other, but they'd forget (prompts are suggestions). This removes the LLM decision entirely.

**What:** When any agent successfully calls `sessions_send`, automatically posts a log entry to #agent-comms Discord channel.

**How:**
1. Checks for successful `sessions_send` calls only
2. Extracts sender agent, target agent, and message preview (first 120 chars)
3. Formats: `[sender → target] preview...`
4. Posts via Discord runtime API to #agent-comms (channel ID: 1466483636390989946)
5. Self-send detection: skips if sender === target (avoids noise)
6. Fire-and-forget — posting failures don't affect the original tool call

**Priority:** 20 (lower than Hook 4's default, so failure logging runs first)

---

### Hook 7: Universal Exec Safety Enforcement (`before_tool_call`)

**Why:** Agents repeatedly violate safe-scripting rules despite prompt instructions. Chained commands (`&&`, `||`, `;`), shell redirections (`>`, `2>`), and using `cat`/`head`/`tail` instead of the `read` tool cause approval timeouts, security risks, and exec policy blocks.

**What:** Hard-blocks dangerous shell patterns before they execute. Unlike Hook 3 (which mutates), Hook 7 blocks and returns an error message explaining the correct approach.

**Rules:**

| Rule | Pattern | Block Message |
|------|---------|---------------|
| 1. Chained operators | `&&`, `\|\|`, `;` | "Run each command as a separate exec call" |
| 2. Shell redirections | `>`, `>>`, `2>` | "Use the write tool to create files" |
| 3. Shell file readers | `cat`, `head`, `tail` as commands | "Use the read tool instead" |
| 4. Piped readers | `\| cat`, `\| head`, `\| tail` | "Run without the pipe" |

**Priority:** 5 (higher than Hook 3's default, so safety blocks fire before enforcement mutations)

**Key design decisions:**
- Blocklist approach with clear error messages — agent learns the correct tool/pattern
- Regex-based detection is fast and deterministic
- Universal: applies to ALL agents, not per-agent config
- Fail-open on regex errors (though regex shouldn't fail)

---

## How Knowledge Flows Through the System

```
Agent encounters unexpected behavior
         │
         ▼
Agent writes learning to shared_learnings/*.md
(with Route: field declaring when it applies)
         │
         ▼
File watcher detects change → rebuilds hashmap (1s debounce)
         │
         ▼
Next time ANY agent calls matching tool:
  Hook 1 (planning): broad domain knowledge in system prompt
  Hook 2 (execution): specific learning injected at tool call
  Hook 7 (enforcement): dangerous patterns hard-blocked
         │
         ▼
After tool call:
  Hook 4: failures logged to issues table
  Hook 6: cross-agent comms auto-posted
         │
         ▼
Issue-fixer cron picks up failures → closes or escalates
Heartbeat cron monitors overall system health
```

---

## Learning Entry Format

Each learning in `shared_learnings/*.md` follows this structure:

```markdown
### [Brief Title]
- **Context:** What you were attempting (natural search phrasing)
- **The Surprise:** The unexpected behavior
- **The Rule/Workaround:** How to handle it
- **Route:** tool=<tool_name>, params.<field> contains "<pattern>"
- **Citations:** 1
- **Created:** [YYYY-MM-DD]
```

The `Route` field is the key innovation — it declares exactly when a learning should fire:
- `tool=exec, params.command contains "git push"` — injected when agent runs git push
- `tool=message, params.filePath OR params.media` — injected when agent sends media
- `tool=sessions_send` — injected on any cross-agent message
- `none` — general knowledge, not tied to a specific tool call

---

## What's Next

### Citation Tracking (Hook 4 Enhancement)
- **Goal:** Measure whether learnings actually help
- **Approach C (planned):** Post-failure semantic search only — find learnings that *would have helped* after a tool fails
- **+1 citation:** Learning matched a post-failure search (would have prevented the error)
- **Avoids false attribution:** No positive citations from injection alone (too far from outcome)

### Planning-Time Route Injection
- **Gap:** Currently, Hook 2 fires at `before_tool_call` — after the agent has already decided to make the call
- **Opportunity:** Some learnings should influence planning (e.g., "don't use `git push --force`")
- **Current coverage:** Hook 1 (domain injection) + Hook 7 (hard block) cover most planning-time cases
- **Future:** Evaluate whether specific learnings need a planning-time injection path

---

## Performance Characteristics

| Hook | Timing | Latency | Failure Mode |
|------|--------|---------|-------------|
| Hook 1 | before_prompt_build | <1ms (cached file reads) | Fail-open (no injection) |
| Hook 2 | before_tool_call | <1ms (hashmap lookup) | Fail-open (no injection) |
| Hook 3 | before_tool_call | <1ms (string replace) | Fail-open (no mutation) |
| Hook 4 | after_tool_call | ~50ms (sqlite3 write) | Fire-and-forget |
| Hook 5 | agent_end | ~50ms (sqlite3 write + dedupe query) | Fire-and-forget |
| Hook 6 | after_tool_call | ~200ms (Discord API call) | Fire-and-forget |
| Hook 7 | before_tool_call | <1ms (regex match) | Fail-open (no block) |

**Total overhead on happy path:** <2ms per tool call (Hooks 2 + 7 regex)
**Previous overhead (semantic search):** 4-20 seconds per tool call

---

## Key Lessons & Design Principles

1. **Hooks are laws, prompts are suggestions** — If agents must follow a rule, enforce it in a hook. Don't rely on prompt instructions.
2. **Deterministic > Semantic** — Regex and hashmap lookups are instant, predictable, and have zero false positives. Semantic search is great for discovery but terrible for enforcement.
3. **Fail-open everywhere** — Plugin errors should never block agent work. Every hook is wrapped in try/catch.
4. **Fire-and-forget for post-execution** — After-tool-call hooks log data but never throw. The agent's work is more important than our telemetry.
5. **Agent writes at discovery** — The agent encountering the surprise has the most context. It writes the learning AND the Route field. No cron extracts it later.
6. **Markdown over DB** — Human readable, git trackable, agent writable. The route hashmap is ephemeral (rebuilt from files on restart or file change).
7. **Three layers cover most cases** — Planning guidance (Hook 1) → Execution advisory (Hook 2) → Hard enforcement (Hook 7). Each layer catches what the previous one missed.

---

*Document generated by MotusCOO — March 22, 2026*
