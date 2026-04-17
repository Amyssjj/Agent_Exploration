---
title: "Knowledge Flywheel Architecture"
date: 2026-03-19
topics: [knowledge-flywheel]
status: active
---

# Knowledge Flywheel Architecture

> **Date:** 2026-03-19  
> **Goal:** Design an enforced knowledge flywheel that creates network effects — the more agents use, the smarter everyone gets  
> **Builds on:** [DB Memory Architecture](./2026-03-10_db_memory_architecture.md), [Memory Search Low Usage Analysis](./2026-03-19_memory_search_low_usage_analysis.md), [Enforced vs Soft Features](./2026-03-19_enforced_vs_soft_features.md)

---

## The Flywheel Model

```
     ┌──────────────────────────────────────────────────┐
     │                                                  │
     ▼                                                  │
  USAGE (enforced)         DISTILLATION (enforced)      │
  ┌─────────────┐         ┌──────────────────┐          │
  │ agent:boot- │         │ Successful exec/ │          │
  │ strap hook  │─reads──►│ tool outcomes    │          │
  │ auto-injects│         │ auto-extracted   │          │
  │ relevant    │         │ by hooks         │          │
  │ knowledge   │         └────────┬─────────┘          │
  └─────────────┘                  │                    │
        │                          │ writes             │
        │                          ▼                    │
        │     ORGANIZATION (enforced)                   │
        │     ┌──────────────────────────┐              │
        │     │ Dedup, merge, score      │              │
        │     │ Auto-prune stale entries │──────────────┘
        │     │ SQLite vector + FTS5     │     richer knowledge
        └─────│ File watcher auto-index  │     = better results
              └──────────────────────────┘     = more usage
```

**Network effect:** Each successful execution distills knowledge → enriches the store → improves future injections → makes agents more successful → more distillation.

---

## Storage Layer: Markdown + SQLite (Already Built)

### Why Not PostgreSQL?

We evaluated three storage options for the centralized knowledge hub:

| Factor | Markdown Only | SQLite (OpenClaw built-in) | PostgreSQL + pgvector |
|:--|:-:|:-:|:-:|
| Human readable/editable | ✅ | ❌ | ❌ |
| Git trackable | ✅ | ❌ | ❌ |
| Zero infrastructure | ✅ | ✅ | ❌ |
| Vector search | via SQLite | ✅ native | ✅ native |
| Full-text search | via SQLite | ✅ FTS5 | ✅ tsvector |
| OpenClaw native | ✅ `extraPaths` | ✅ already used | ❌ custom plugin |
| Relational queries | ❌ | ✅ SQL | ✅ SQL |
| Multi-machine sync | ❌ | ❌ | ✅ |
| Scale limit | ~500 entries | ~100K entries | Unlimited |

### Chosen: Hybrid — Markdown Source of Truth + SQLite Search Engine

**Your existing setup already has both layers working:**

```
Source of Truth (human layer):
  ~/.clawdbot/shared_learnings/        ← 23 categorized .md files, ~62KB
  ├── discord_learnings.md             ← structured template entries
  ├── exec_shell_learnings.md
  ├── cron_scheduling_learnings.md
  └── ... (global, shared across all agents)

Search Engine (machine layer):
  ~/.openclaw/memory/{agentId}.sqlite  ← per-agent SQLite DBs
  ├── chunks table                     ← text + embeddings + metadata
  ├── files table                      ← tracked source files
  ├── FTS5 virtual table               ← full-text search
  └── sqlite-vec extension             ← cosine similarity vector search

Bridge:
  openclaw.json → memorySearch.extraPaths: ["~/.clawdbot/shared_learnings"]
  → file watcher auto-reindexes markdown changes into SQLite
```

**What this means:** You don't need a new database. The markdown files are the human-readable, git-trackable source of truth. SQLite is already the vector-searchable, FTS-enabled search engine. The `extraPaths` config already bridges them. **The missing pieces are enforced injection and enforced extraction.**

### When to Graduate to PostgreSQL
- When you have 500+ knowledge entries (currently ~150)
- When agents run on multiple machines that can't share a filesystem
- When you need real-time cross-agent notifications ("CTO just learned X")
- When you need usage analytics that SQLite can't easily provide

---

## Three Pillars — Mapped to OpenClaw Extension Points

### Pillar 1: Enforced Usage (Knowledge Injection)

> **Problem solved:** Agents skip `memory_search` because it's soft. Sub-agents are denied it entirely.

#### Design: `knowledge-inject` Hook

```
Event: agent:bootstrap
Trigger: Every prompt assembly (every turn)
Uses: Existing MemorySearchManager → existing SQLite vector search
```

**Flow:**
1. Hook fires on `agent:bootstrap` (enforced, gateway-level)
2. Extracts the current user message from session context
3. Runs vector search against SQLite via `getMemorySearchManager` (searches `shared_learnings/` via `extraPaths`)
4. Filters results by relevance score (≥ 0.75) and recency
5. Injects a `KNOWLEDGE.md` bootstrap file with relevant snippets:
   ```markdown
   ## 🧠 Auto-Recalled Knowledge
   
   ### Discord Media Must Be Staged to Outbound Directory
   Source: shared_learnings/discord_learnings.md | Score: 0.92
   > Always copy files to ~/.openclaw/media/outbound/ first...
   
   ### Session Keys Require 3+ Segments  
   Source: shared_learnings/cross_agent_learnings.md | Score: 0.87
   > session_send keys require format: agent:<id>:<channel>:...
   ```
6. Appended to `context.bootstrapFiles` — same pattern as `bootstrap-extra-files`

**Existing code pattern:**
```typescript
// From bootstrap-extra-files/handler.ts — exact same injection API
context.bootstrapFiles = filterBootstrapFilesForSession(
  [...context.bootstrapFiles, ...extras],
  context.sessionKey,
);
```

**Why this works:**
- `agent:bootstrap` is **enforced** — runs at gateway level, agent cannot skip it
- Sub-agents also go through bootstrap → they get knowledge too (solving the deny-list problem)
- Uses the **existing SQLite search infrastructure** — no new database needed
- Entries from `shared_learnings/` are already indexed via `extraPaths`

---

### Pillar 2: Enforced Distillation (Knowledge Capture)

> **Problem solved:** Knowledge writing is soft — agents decide whether to save learnings.

Three extraction layers, ordered by enforcement strength:

#### A. Session-End Extraction (Highest Value)

```
Event: command:new / command:reset (existing session-memory hook)
Enhancement: Add structured knowledge extraction after conversation capture
```

**Current:** `session-memory` hook captures last ~15 messages and writes `memory/YYYY-MM-DD-slug.md`

**Enhancement:** After capturing, also send conversation through a structured extraction prompt:
```
Given this conversation, extract reusable learnings using this format:
### [Brief Title]
- **Context:** [Natural search-friendly description]
- **The Surprise:** [Unexpected behavior or root cause]
- **The Rule/Workaround:** [How to handle it going forward]
- **Citations:** 1
- **Created Date:** [YYYY-MM-DD]

Categories: scripts, patterns, gotchas, preferences
Skip if nothing new was learned.
```

Write extracted entries to `~/.clawdbot/shared_learnings/<category>_learnings.md` (append-only).  
SQLite auto-reindexes via file watcher → instantly searchable by all agents.

#### B. Enhanced Memory Flush (Pre-Compaction)

```
Event: Pre-compaction trigger (existing, enforced)
Enhancement: Structured extraction prompt
```

**Current:** `"Pre-compaction memory flush. Store durable memories only in memory/YYYY-MM-DD.md"`

**Enhancement:** Add to the flush prompt:
```
Additionally, extract any reusable knowledge using the shared_learnings template format.
Append to ~/.clawdbot/shared_learnings/<category>_learnings.md
Check for duplicates: if the learning is already captured, increment Citations count instead.
```

#### C. Cron-Driven Issue Fixer Pattern (Already Working)

Your issue fixer cron job already has the **"Knowledge Flywheel — Extract Learning (DO NOT SKIP)"** step that writes to `shared_learnings/`. This pattern can be replicated to other cron jobs:
- Daily digest → extract cross-agent patterns
- Heartbeat → extract operational learnings

---

### Pillar 3: Enforced Organization (Knowledge Maintenance)

> **Problem solved:** Without maintenance, knowledge becomes duplicated, stale, and noisy.

#### A. Current Structure (Keep, Enhance)

Your `shared_learnings/` structure is already well-organized by domain:
```
~/.clawdbot/shared_learnings/
├── discord_learnings.md          ← 7 entries
├── exec_shell_learnings.md       ← ~8 entries
├── cron_scheduling_learnings.md  ← ~8 entries
├── cross_agent_learnings.md      ← inter-agent patterns
├── manim_animation_learnings.md  ← largest, ~10KB
├── yt_*.md                       ← YouTube production rules
└── README.md                     ← index + writing guide
```

**Enhancement:** Add metadata to entries for freshness tracking:
```markdown
### Discord Media Must Be Staged to Outbound Directory
<!-- last_used: 2026-03-19, use_count: 7, source_agent: coo -->
- **Context:** Sending images to Discord...
```

#### B. Deduplication (Before Write)

Before appending a new entry in any extraction hook:
1. Run `memory_search` with the candidate entry's Context text
2. If score > 0.90 → **skip** (duplicate exists)
3. If score 0.75–0.90 → **merge** (update existing entry, increment Citations)
4. If score < 0.75 → **write** as new entry

Uses the **existing SQLite hybrid search** (BM25 + vector, 0.3/0.7 weighting).

#### C. Cron-Based Maintenance

```
Event: cron (weekly)
Task: Knowledge graph maintenance
```

1. Scan all `shared_learnings/*.md` for near-duplicate entries (vector similarity > 0.88)
2. Merge duplicates, keeping the most complete version
3. Update `use_count` tracking from injection hook logs
4. Update `README.md` index with current file stats

---

## Implementation Strategy

| Component | Extension Point | What Exists | What's New |
|:--|:--|:--|:--|
| **Knowledge injection** | `agent:bootstrap` hook | Hook API + `bootstrap-extra-files` pattern | New `knowledge-inject` bundled hook |
| **Search engine** | SQLite + sqlite-vec + FTS5 | Fully built, per-agent DBs running | Nothing — already works |
| **Indexing bridge** | `extraPaths` + file watcher | Already configured for `shared_learnings/` | Nothing — already bridges |
| **Session-end extraction** | `session-memory` hook | Captures conversations on `/new`/`/reset` | Add structured extraction step |
| **Pre-compaction extraction** | Memory flush prompt | Triggered automatically near compaction | Enhanced prompt (config change) |
| **Deduplication** | `MemorySearchManager.search()` | Hybrid search with scoring | Dedup logic before write |
| **Maintenance** | Cron system | Job scheduler running | New weekly maintenance job |

---

## What This Achieves

```
WITHOUT FLYWHEEL:
Agent A solves problem → writes nothing → Agent B hits same problem → solves from scratch

WITH FLYWHEEL (enforced at every step):
Agent A solves problem
  → session-memory hook extracts learning (ENFORCED)
  → writes to shared_learnings/*.md with dedup check
  → SQLite auto-reindexes via file watcher (ENFORCED)
  → Agent B starts new session
  → agent:bootstrap hook searches SQLite (ENFORCED)
  → injects relevant knowledge into prompt (ENFORCED)
  → Agent B avoids the problem → solves faster
  → new patterns extracted → knowledge grows → everyone benefits
```

---

## Phased Implementation

### Phase 1: Enforced Injection (Highest Impact, Lowest Effort)
- [ ] Build `knowledge-inject` bundled hook (`agent:bootstrap` → SQLite search → inject)
- [ ] Test with existing `shared_learnings/` content (already indexed)
- [ ] Verify sub-agents receive injected knowledge

### Phase 2: Enforced Extraction
- [ ] Enhance `session-memory` hook with structured knowledge extraction
- [ ] Enhance memory flush prompt with structured extraction sections
- [ ] Add dedup check before writing (vector similarity ≥ 0.90 = skip)

### Phase 3: Self-Maintenance
- [ ] Build weekly cron job for knowledge dedup and merge
- [ ] Add `<!-- last_used, use_count -->` metadata to entries
- [ ] Add freshness scoring to injection ranking
- [ ] Auto-update `README.md` index

### Phase 4: Scaling (When Needed)
- [ ] Migrate to PostgreSQL + pgvector when entries exceed 500 or agents span multiple machines
- [ ] Add usage analytics (which learnings are actually helping)
- [ ] Knowledge provenance chain (which agent learned what, when)

---

## Appendix A: Hybrid Search — How BM25 + Vector Works

### Current Configuration (Your Setup)

Your `openclaw.json` uses defaults (no `query.hybrid` override):

| Setting | Value | Meaning |
|:--|:--|:--|
| `hybrid.enabled` | `true` | Both search methods active |
| `vectorWeight` | **0.7** | 70% of final score from semantic similarity |
| `textWeight` | **0.3** | 30% of final score from keyword matching |
| `candidateMultiplier` | 4 | Fetches 4× more candidates than requested |
| `mmr.enabled` | `true` | Diversity re-ranking (avoids redundant results) |
| `temporalDecay.enabled` | `true` | Newer content scores higher |
| Embedding provider | Gemini (`gemini-embedding-001`) | 768-dimension vectors |
| Embedding store | `sqlite-vec` (cosine distance) | Per-agent SQLite DBs |
| Keyword store | FTS5 virtual table | BM25 scoring |

### How Each Component Works

**FTS5 + BM25 (keyword side, 30%):** Tokenizes the query into words, matches them against the FTS5 full-text index, and scores using BM25 — a probabilistic algorithm considering term frequency, document frequency, and document length. Finds *exact word matches* only.

**Vector Search (semantic side, 70%):** Converts the query into a 768-dim embedding via Gemini API, then runs cosine distance against pre-computed chunk embeddings via `sqlite-vec`. Finds *conceptually similar* text regardless of exact wording.

**Merge formula:**
```
final_score = 0.7 × vectorScore + 0.3 × textScore
→ temporal decay applied (newer = bonus)
→ MMR re-ranking (diversity)
```

### Why Hybrid Beats FTS5-Only

| Factor | FTS5 Only | Hybrid (BM25 + Vector) |
|:--|:--|:--|
| Exact keyword matches | ✅ Excellent | ✅ Still finds via 30% FTS weight |
| Semantic search | ❌ Fails — "sending images" won't find "staging media" | ✅ Embeddings bridge synonyms |
| Conversational queries | ❌ Poor — "that thing about the API" | ✅ Keyword extraction + semantic match |
| Speed | ✅ Fastest (no API call) | ❌ Needs Gemini API call per query |
| Cost | ✅ Free (local) | ❌ API cost per query |
| Offline | ✅ Works | ❌ Needs API (falls back to FTS-only) |

**Real-world proof from your setup:** Your `shared_learnings_meta.md` documents exactly why hybrid matters — an entry titled "NEVER Use build_audio.py" was invisible to the search `"add audio effect to video"` because FTS5 couldn't bridge the semantic gap. Vector search would connect those concepts via embeddings.

### Graceful Degradation

The system degrades automatically:
1. **No Gemini API** → falls back to FTS5-only mode (keyword extraction + BM25)
2. **No sqlite-vec** → falls back to brute-force cosine over all chunks in memory
3. **No embeddings at all** → FTS5-only if available, else no search

