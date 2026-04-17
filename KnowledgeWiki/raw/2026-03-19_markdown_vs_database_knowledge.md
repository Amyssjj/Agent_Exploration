---
title: "Knowledge Store: Markdown Files vs Database — Pros & Cons"
date: 2026-03-19
topics: [knowledge-flywheel]
status: active
---

# Knowledge Store: Markdown Files vs Database — Pros & Cons

> **Date:** 2026-03-19  
> **Context:** Your current setup uses `~/.clawdbot/shared_learnings/` (23 categorized markdown files) exposed to all agents via `extraPaths` in `openclaw.json`, indexed by the built-in memory search vector store. Should this stay as markdown files, or move to a centralized database (PostgreSQL + pgvector)?

---

## Your Current Setup

```
~/.clawdbot/shared_learnings/         ← global, shared across all agents
├── discord_learnings.md              ← 7 entries, 5.4KB
├── exec_shell_learnings.md           ← ~8 entries, 4.9KB  
├── cron_scheduling_learnings.md      ← ~8 entries, 5.0KB
├── manim_animation_learnings.md      ← largest, 10KB
├── ... (23 files total, ~62KB)
└── README.md                         ← index + writing guide

openclaw.json:
  memorySearch.extraPaths: ["~/.clawdbot/shared_learnings"]
```

**How it works today:**
1. Agents write entries using structured template (Context/Surprise/Rule/Citations)
2. Files are indexed by memory search vector store (SQLite + embeddings)
3. `memory_search` can find entries via semantic search
4. But agents often **don't call** `memory_search` (the original problem)

---

## Comparison

### 📄 Markdown Files (Current Approach)

| | |
|:--|:--|
| ✅ **Human readable/editable** | You can `cat`, `grep`, edit in VS Code. No SQL needed |
| ✅ **Git-trackable** | Full version history, diff, blame, branching for free |
| ✅ **Zero infrastructure** | No database to run, no migrations, no connection strings |
| ✅ **Already works with OpenClaw** | `extraPaths` + memory search indexes them automatically |
| ✅ **Agent-native format** | LLMs are excellent at reading/writing markdown |
| ✅ **Inspectable** | You can see exactly what was learned by opening a file |
| ✅ **Portable** | Copy folder to another machine = done |
| ❌ **No relational queries** | Can't do "show me all learnings by CTO agent from last 7 days" |
| ❌ **No atomic dedup** | Two agents can write near-duplicate entries simultaneously |
| ❌ **Linear scaling** | As files grow (100KB+), parsing and indexing slow down |
| ❌ **No cross-field search** | Can't combine "citations > 3 AND category=discord" |
| ❌ **Stale embeddings** | After edit, need re-index; not instant |
| ❌ **No usage tracking** | Can't track which entries agents actually used |

### 🗄️ Database (PostgreSQL + pgvector)

| | |
|:--|:--|
| ✅ **Relational queries** | "Find discord learnings from last week with citations > 2" |
| ✅ **Atomic operations** | Concurrent writes don't collide; transaction safety |
| ✅ **Instant indexing** | Embedding computed on INSERT; immediately searchable |
| ✅ **Usage tracking** | `use_count`, `last_used_at`, `used_by_agent` columns |
| ✅ **Built-in dedup** | Check similarity before INSERT in same transaction |
| ✅ **Scales to thousands** | HNSW index handles 100K+ entries efficiently |
| ✅ **Cross-agent metadata** | Track provenance: who learned it, when, confidence |
| ❌ **Infrastructure overhead** | Need PostgreSQL running, migrations, backups |
| ❌ **Not human-browsable** | Need SQL/UI tool to inspect entries; can't just `cat` the file |
| ❌ **Not git-trackable** | Lose version history, diff, PR review |
| ❌ **Not OpenClaw-native** | Need custom plugin/tools; `extraPaths` doesn't work |
| ❌ **Agent write complexity** | Agents need `db_memory_save` tool instead of simple `write` |
| ❌ **Overhead for your scale** | ~23 files, ~62KB total — database is massively overkill |
| ❌ **Migration risk** | Existing learnings need ETL; existing cron prompts need rewrite |

---

## The Honest Assessment for Your Scale

### Right now: **Markdown files win decisively**

Your setup has ~62KB across 23 files. That's maybe 150 entries. At this scale:
- SQLite vector search handles this in milliseconds
- The categorized file structure IS your relational schema (file = category)
- You can read and QA every entry by hand
- `extraPaths` already makes them globally available

**The problem you're solving isn't "markdown is slow" — it's "agents don't search before acting."** Moving to PostgreSQL doesn't fix that. An agent that skips `memory_search` will also skip `db_memory_search`.

### The real inflection point for database: **~500+ entries OR 3+ machines**

A database becomes worth the infrastructure cost when:
1. **Volume:** 500+ entries where category files hit 50KB+ each and need sub-file granularity
2. **Multi-host:** Agents running on different machines that can't share a filesystem
3. **Usage analytics:** You need to know which learnings are actually used vs. stale
4. **Real-time dedup:** Two agents solving similar problems simultaneously

---

## Recommended: Hybrid Approach (Best of Both)

Keep markdown as the **source of truth**; add lightweight enforcement layers:

```
WRITE PATH (enforced):
  Agent solves problem
    → session-memory hook extracts learning (enforced)
    → dedup check via memory_search (>0.90 = skip)
    → write to shared_learnings/<category>.md (append)
    → vector index auto-updates via file watcher

READ PATH (enforced):  
  Agent starts session / receives message
    → agent:bootstrap hook fires (enforced)
    → runs memory_search against shared_learnings (enforced)
    → injects relevant entries as bootstrap context (enforced)
    → agent sees knowledge without calling any tool
```

**What this gives you:**
- ✅ Keep human-readable, git-trackable, zero-infrastructure markdown
- ✅ Enforced injection so agents get knowledge without `memory_search`
- ✅ Enforced extraction so learnings are captured after successful fixes
- ✅ Dedup before write via existing vector search
- ✅ No database to run or maintain

**When to graduate to database:**
- When `shared_learnings/` exceeds 500 entries
- When you have agents on multiple machines
- When you need usage analytics that markdown can't provide
- When you want real-time cross-agent notifications ("CTO just learned something relevant to Writer")

---

## Summary

| Factor | Markdown | Database | Winner at Your Scale |
|:--|:-:|:-:|:--|
| Human readability | ✅ | ❌ | **Markdown** |
| Git tracking | ✅ | ❌ | **Markdown** |
| Zero infrastructure | ✅ | ❌ | **Markdown** |
| OpenClaw native | ✅ | ❌ | **Markdown** |
| Agent write simplicity | ✅ | ❌ | **Markdown** |
| Relational queries | ❌ | ✅ | Tie (not needed yet) |
| Usage tracking | ❌ | ✅ | Database (nice-to-have) |
| Atomic dedup | ❌ | ✅ | Database (nice-to-have) |
| Scale (>500 entries) | ❌ | ✅ | Database (future) |
| Multi-machine | ❌ | ✅ | Database (future) |

**Bottom line:** Fix the enforcement problem (injection + extraction) first. That's where the flywheel breaks. The storage layer (markdown vs DB) is not the bottleneck — *usage* is.
