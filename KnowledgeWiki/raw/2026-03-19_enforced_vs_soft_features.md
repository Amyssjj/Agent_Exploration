---
title: "OpenClaw: Enforced (Code-Level) vs Soft (Prompt-Only) Features"
date: 2026-03-19
topics: [openclaw-internals]
status: active
---

# OpenClaw: Enforced (Code-Level) vs Soft (Prompt-Only) Features

> **Date:** 2026-03-19  
> **Context:** Which built-in features are actually enforced at the gateway/code level vs. relying on model compliance?

---

## ✅ Enforced at Code Level (Gateway / Hook / Runtime)

These features run regardless of what the LLM decides — they are **structural**, not prompt-based.

### 1. Memory Flush (Pre-Compaction)
**File:** `src/auto-reply/reply/memory-flush.ts`, `agent-runner-memory.ts`

- **What:** When a session approaches compaction threshold, OpenClaw injects a **silent agentic turn** telling the model to write memories to `memory/YYYY-MM-DD.md`
- **Enforcement:** The gateway **automatically triggers** this turn before compaction — the model doesn't choose whether to receive it
- **But:** The model still decides *what* to write. If it outputs `NO_REPLY`, nothing is saved. The flush **prompt** is soft; the **trigger** is enforced

### 2. Session-Memory Hook (`/new` and `/reset`)
**File:** `src/hooks/bundled/session-memory/handler.ts`

- **What:** When user runs `/new` or `/reset`, a hook fires that reads the last ~15 messages, generates a slug via LLM, and writes a memory file (`memory/YYYY-MM-DD-slug.md`)
- **Enforcement:** **Fully enforced** — this is a gateway hook, runs server-side, doesn't depend on the agent choosing to save
- **Note:** This is the **only** memory write that is 100% code-enforced. It captures conversation summaries, not the agent's learnings

### 3. Exec Approvals (Two-Layer Security)
**File:** `src/agents/bash-tools.exec-*`, `src/infra/exec-approvals.js`

- **What:** Shell commands go through a two-layer approval system (agent config allowlist + host-level `exec-approvals.json`)
- **Enforcement:** **Fully enforced** — the gateway intercepts `exec` tool calls, checks against allowlists, and blocks/prompts before execution. The agent cannot bypass this

### 4. Tool Deny Lists (Sub-Agent Policy)
**File:** `src/agents/pi-tools.policy.ts`

- **What:** Sub-agents are denied certain tools (`memory_search`, `gateway`, `cron`, etc.)
- **Enforcement:** **Fully enforced** — tools are filtered at the gateway level before being sent to the LLM. The model literally cannot call a denied tool

### 5. Bootstrap Context Injection (AGENTS.md, SOUL.md, MEMORY.md, TOOLS.md)
**File:** `src/agents/workspace.ts`, `bootstrap-files.ts`

- **What:** Workspace files are loaded into the system prompt as `# Project Context`
- **Enforcement:** **Fully enforced** — files are injected by the gateway before the LLM sees any prompt. The agent doesn't choose to read them; they're pre-loaded
- **But:** Whether the agent *follows* the instructions in those files is soft

### 6. Session Compaction
**File:** `src/agents/compaction.ts`

- **What:** When context exceeds limits, the session is automatically compacted (summarized + truncated)
- **Enforcement:** **Fully enforced** — the gateway does this automatically, not by asking the model

### 7. Vector Index Sync (Memory Search Indexing)
**File:** `src/agents/memory-search.ts`, `src/memory/manager.ts`

- **What:** `MEMORY.md` and `memory/*.md` files are indexed into a vector store on session start, on file watch, and on search
- **Enforcement:** **Fully enforced** — background indexing runs automatically. But *searching* the index still requires the agent to call `memory_search`

---

## ❌ Soft / Prompt-Only Features (Model Must Comply)

These rely on the LLM reading and following instructions. They have **no enforcement mechanism**.

### 1. `memory_search` Recall ← **Your concern**
- System prompt says: "Before answering anything about prior work, decisions, dates, people, preferences, or todos: run memory_search"
- Tool description says: "Mandatory recall step"
- **Reality:** Purely a prompt instruction. No pre-check, no forcing, no error if skipped

### 2. Skills Scanning
- System prompt says: "Before replying: scan `<available_skills>` entries. If exactly one skill clearly applies: read its SKILL.md"
- **Reality:** Prompt instruction. The model decides whether a skill applies

### 3. AGENTS.md / SOUL.md / TOOLS.md Behavioral Rules
- These files are injected into context (enforced), but **following their instructions** is soft
- Example: "Read AGENTS.md and MEMORY.md before responding" — the files are already injected, but the model decides whether to obey specific rules within them

### 4. Memory Writing (Daily Logs / Knowledge Distillation)
- The agent is told "decisions go to MEMORY.md, daily notes go to memory/YYYY-MM-DD.md"
- **Reality:** Prompt instruction. The agent decides whether to write
- **Exception:** The pre-compaction memory flush (item #1 above) is an enforced *trigger*, but the content written is still model-decided

### 5. Reply Tags / Silent Replies
- `NO_REPLY` and `[[reply_to_current]]` conventions are prompt instructions
- The gateway does *process* these tokens, but the model choosing to *use* them is soft

---

## Summary Table

| Feature | Trigger Enforced? | Behavior Enforced? | Notes |
|---------|:-:|:-:|-------|
| Memory flush (pre-compaction) | ✅ | ❌ | Turn is injected; what's written is up to model |
| Session-memory hook (/new, /reset) | ✅ | ✅ | Fully code-level, captures last ~15 messages |
| Exec approvals | ✅ | ✅ | Commands blocked until approved |
| Tool deny list | ✅ | ✅ | Tools removed before model sees them |
| Bootstrap injection | ✅ | ❌ | Files injected; following rules is soft |
| Compaction | ✅ | ✅ | Automatic context management |
| Vector index sync | ✅ | ✅ | Background indexing is automatic |
| `memory_search` recall | ❌ | ❌ | Entirely prompt-based |
| Skills scanning | ❌ | ❌ | Entirely prompt-based |
| Memory writing (learnings) | ❌ | ❌ | Entirely prompt-based |
| AGENTS.md behavioral rules | ❌ | ❌ | Content injected, compliance is soft |

---

## Key Takeaway

> **Memory writing is NOT enforced** — except for the session-memory hook on `/new`/`/reset` (which captures raw conversation, not distilled knowledge) and the memory flush trigger (which only fires near compaction and still depends on the model to write useful content).
>
> The entire **knowledge distillation → retrieval** loop is soft on both ends: the agent decides whether to write knowledge, and whether to search for it later. This is the fundamental gap.
