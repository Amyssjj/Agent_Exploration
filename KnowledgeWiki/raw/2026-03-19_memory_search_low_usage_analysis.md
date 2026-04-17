---
title: "Why `memory_search` Has Low Usage — Root Cause Analysis"
date: 2026-03-19
topics: [knowledge-flywheel]
status: active
---

# Why `memory_search` Has Low Usage — Root Cause Analysis

> **Date:** 2026-03-19  
> **Topic:** Memory search tool usage gap  
> **Scope:** System prompt, tool policy, memory architecture

## Summary

Despite OpenClaw's investment in cumulative knowledge (MEMORY.md, memory/*.md, shared learnings, knowledge distillation), the `memory_search` tool has very low actual usage. This analysis identifies **5 structural root causes** in the codebase.

---

## Root Cause 1: Sub-agents Are Always Denied `memory_search`

In [`pi-tools.policy.ts`](./../../src/agents/pi-tools.policy.ts) (lines 24–38), `memory_search` and `memory_get` are in the `SUBAGENT_TOOL_DENY_ALWAYS` list:

```typescript
const SUBAGENT_TOOL_DENY_ALWAYS = [
  "gateway",
  "agents_list",
  "whatsapp_login",
  "session_status",
  "cron",
  // Memory - pass relevant info in spawn prompt instead
  "memory_search",   // ← ALWAYS denied
  "memory_get",      // ← ALWAYS denied
  "sessions_send",
];
```

**Impact:** Every sub-agent spawned via `sessions_spawn` — regardless of depth — **cannot** access cumulative knowledge. The comment says "pass relevant info in spawn prompt instead," but this requires the parent agent to proactively search first. If the parent also skips search, the knowledge chain breaks entirely.

---

## Root Cause 2: Narrow System Prompt Trigger

In [`system-prompt.ts`](./../../src/agents/system-prompt.ts) (lines 38–64), the memory section:

```typescript
function buildMemorySection(params) {
  if (params.isMinimal) return [];       // Sub-agents get NO memory guidance
  if (!params.availableTools.has("memory_search")) return [];
  
  return [
    "## Memory Recall",
    "Before answering anything about prior work, decisions, dates, 
     people, preferences, or todos: run memory_search..."
  ];
}
```

**Problems:**
- **Minimal mode (sub-agents) = no memory section at all** — doubly ensuring sub-agents ignore memory
- Trigger condition is limited to "prior work, decisions, dates, people, preferences, or todos" — many knowledge-relevant queries (technical patterns, architectural decisions, debugging insights) **don't match**
- It's a soft "before answering" instruction — models frequently skip these

---

## Root Cause 3: No Proactive Memory Injection

The architecture is entirely **pull-based** — the agent must decide to call `memory_search`. There is no:
- Auto-injection of relevant memory snippets before the agent responds
- Automatic pre-search at session start that inserts memory context  
- Hook-based injection (e.g., `before_prompt_build` running a search)

The `sync.onSessionStart` and `sync.onSearch` config options in [`memory-search.ts`](./../../src/agents/memory-search.ts) only control **index syncing** (keeping the vector store current), not proactive retrieval.

---

## Root Cause 4: "Mandatory" Label Without Enforcement

The tool description in [`memory-tool.ts`](./../../src/agents/tools/memory-tool.ts) (line 88):

> "Mandatory recall step: semantically search MEMORY.md + memory/*.md..."

Despite calling it "mandatory," there is **no actual enforcement** — no pre-check, no chain-of-thought forcing, no error if the agent skips it. LLMs frequently ignore "mandatory" instructions when they feel confident they can answer without searching.

---

## Root Cause 5: MEMORY.md Bootstrap Reduces Perceived Need

In [`workspace.ts`](./../../src/agents/workspace.ts), `MEMORY.md` is loaded as a **context file** in the system prompt (under `# Project Context`):
- The agent already "sees" MEMORY.md content in context
- It doesn't feel the need to call `memory_search` for content it can already see
- But `memory/*.md` files (daily logs, distilled knowledge) are **NOT** in bootstrap context — only accessible via `memory_search`

---

## Knowledge Lifecycle Flow

```
Knowledge Created → memory/*.md files ──(requires memory_search)──→ Agent must proactively search ❌
                                                                    └── Sub-agents denied ❌
                                                                    └── Narrow trigger ❌

Curated Knowledge → MEMORY.md ──(bootstrap injection)──→ Agent sees in context ✅
```

**The write path works** (memory flush, daily logs). **The read-back path is broken**: main agents have the tool but skip it; sub-agents are blocked entirely.

---

## Potential Solutions

| Approach | Complexity | Impact |
|----------|-----------|--------|
| **A. Proactive injection** — auto-run `memory_search` per turn, prepend results | Medium | High |
| **B. Allow sub-agent `memory_search`** — remove from deny list or make configurable | Low | Medium |
| **C. Stronger system prompt** — broader triggers, more prominent placement | Low | Low-Med |
| **D. Pre-search at session start** — broad search on session begin, inject into first turn | Medium | Medium |
| **E. Hook-based injection** — `before_prompt_build` hook runs memory search automatically | Med-High | High |

---

## Key Files Referenced

| File | Role |
|------|------|
| `src/agents/pi-tools.policy.ts` | Sub-agent tool deny list (Root Cause 1) |
| `src/agents/system-prompt.ts` | Memory recall section builder (Root Cause 2) |
| `src/agents/memory-search.ts` | Memory search config resolution (Root Cause 3) |
| `src/agents/tools/memory-tool.ts` | Tool definition + "mandatory" label (Root Cause 4) |
| `src/agents/workspace.ts` | MEMORY.md bootstrap loading (Root Cause 5) |
| `src/agents/tool-catalog.ts` | Memory tools in "coding" profile |
