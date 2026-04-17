# Knowledge Wiki Plugin: Implementation Design

> **Date:** 2026-04-15
> **Status:** Implementation-ready design
> **Scope:** OpenClaw plugin (`extensions/knowledge-wiki/`) — single unified plugin
> **Builds on:** [Digital Me Vision](./2026-04-14_digital_me_vision.md), [Digital Me Technical Design](./2026-04-14_digital_me_technical_design.md), [Knowledge Flywheel V2](./2026-03-23_knowledge_flywheel_v2.md)
> **Companion plugins:** `proactive-learning` (agent ops manual), `task-orchestrator` (task management)

---

## 1. Design Goal

Build a **personal knowledge wiki flywheel** as an OpenClaw plugin that:

1. Manages a `raw/ → concepts/ → queries/` wiki on the filesystem
2. Exposes MCP tools so any agent (Claude Code, Hermes, Antigravity) can read, query, and contribute
3. Automates the flywheel: concept compilation, staleness detection, concept-primed raw generation
4. Keeps the wiki human-readable in Obsidian at all times

**Non-goal:** This plugin does NOT replace `proactive-learning` (agent ops manual) or `memory-core` (session memory). It is a separate system for personal/team research knowledge.

---

## 2. Why an OpenClaw Plugin (Not Standalone)

### The Architecture Decision

We evaluated three approaches: pure OpenClaw plugin, standalone MCP server, and hybrid. The plugin approach won because **nearly every wiki operation needs intelligence**:

| Operation | Needs LLM/Embeddings? | Why |
|---|---|---|
| `search` | Yes — semantic embeddings | "task recovery blind spots" must match "Advisor Knowledge Blindness" |
| `tag` | Yes — LLM classification | Assigning topics requires understanding article content against existing concept taxonomy |
| `prime` | Yes — semantic similarity | Finding which concepts are relevant to a task description |
| `ingest_raw` | Yes — auto-tagging on write | New articles need topic assignment at ingest time |
| `compile` | Yes — LLM synthesis | Core compilation is entirely LLM-powered |
| `query` | Yes — LLM synthesis | Cross-concept Q&A is LLM-powered |
| `lint` | Yes — LLM contradiction detection | Finding inconsistencies between articles requires understanding |
| `read_concept` | No — pure filesystem | Only a few operations are pure filesystem reads |
| `read_raw` | No — pure filesystem | |
| `index` | No — pure filesystem | |
| `status` | No — SQLite query | |

A standalone server would need to duplicate OpenClaw's entire LLM infrastructure (model configuration, local models, Gemini embeddings, API keys, provider routing) or call back to OpenClaw for every intelligent operation — which is worse than just being a plugin.

### What OpenClaw Provides That a Standalone Server Can't

| Capability | How the Plugin Uses It |
|---|---|
| **Local models (Gemini, etc.)** | Compilation, tagging, Q&A synthesis — uses whatever models you've already configured |
| **LanceDB embeddings** | Semantic search via `memorySearch.extraPaths` — zero embedding infra to build |
| **Cron scheduling** | Weekly lint passes, change digests, dream cycle — via `task-orchestrator` workflows |
| **Heartbeat** | Idle-time concept recompilation during dream cycles |
| **`before_prompt_build` hook** | Automatic concept priming for internal agents — zero agent-side code |
| **`subagent.run()` dispatch** | Compilation and Q&A run as isolated subagent tasks — don't block the main agent |
| **MCP auto-exposure** | `plugin-tools-serve.ts` auto-discovers the `wiki` tool — zero MCP server code |
| **File watching pattern** | Proactive-learning already has the `fs.watch()` + debounce pattern — reuse it |

### Reliability Through Graceful Degradation

The concern about gateway downtime is addressed by layered fallbacks, not by process isolation:

```
Level 1 (normal):    Embeddings + LLM + cron + hooks — full flywheel
Level 2 (LLM down):  FTS5 keyword search fallback, reads still work, compilation waits
Level 3 (gateway down): Filesystem reads via Obsidian, any agent can cat the markdown files
Level 4 (disk only):  ~/KnowledgeWiki/ is always human-readable — it's just markdown
```

Every hook and tool handler is **fail-open**: errors return empty results, never block agents. The SQLite index is disposable — rebuilt from markdown files at `gateway_start`. Compilation uses atomic writes (temp file + rename) — a failed compile leaves the old concept untouched.

**Actual gateway reliability:** Logs show 25+ hour stable uptime with auto-recovery from provider restarts. The EAGAIN/lock issues from February were during active development, not recurring production failures. Claude Code's MCP connection is non-blocking — if the gateway is briefly unavailable during restart (~30 seconds), tools fail gracefully and the agent continues without wiki context (same as working without a wiki at all).

---

## 3. Relationship to Existing Plugins

```
┌─────────────────────────────────────────────────────────────────┐
│ PERSONAL KNOWLEDGE (this plugin: knowledge-wiki)                │
│ ~/KnowledgeWiki/                                                │
│ "What do we understand about task orchestration?"               │
│ Consumer: Jing (human), agents doing research/analysis          │
│ Structure: raw/ → concepts/ → queries/                          │
│ Flywheel: compile, prime, Q&A file-back, lint, dream cycle      │
│ Intelligence: embeddings (search, tag, prime), LLM (compile,    │
│   query, lint) — all via OpenClaw's configured providers        │
└─────────────────────────┬───────────────────────────────────────┘
                          │ compile-down (extract actionable rules)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT OPS MANUAL (proactive-learning)                           │
│ ~/.openclaw/shared_learnings/                                   │
│ "NEVER use build_audio.py — use add_audio_effect.py instead"   │
│ Consumer: agents during task execution                          │
│ Structure: flat files with route-based lookup                   │
│ Intelligence: keyword route matching (fast, deterministic)      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ SESSION MEMORY (memory-core)                                    │
│ memory/*.md per agent                                           │
│ "Last session we discussed X, user prefers Y"                   │
│ Consumer: individual agent sessions                             │
│ Structure: per-agent, per-session                               │
└─────────────────────────────────────────────────────────────────┘
```

The three systems are complementary. The knowledge wiki is the only one
organized by **concept** rather than by **agent** or **incident**.

---

## 4. Wiki Filesystem Layout

```
{wikiDir}/                          # configurable, default: ~/KnowledgeWiki
├── raw/                            # Chronological investigation notes (immutable once written)
│   ├── 2026-03-26_task_dependency_graph_design.md
│   ├── 2026-04-15_openclaw_task_system_update.md
│   └── ...
│
├── concepts/                       # Compiled concept articles (always-current, recompiled)
│   ├── _index.md                   # Auto-maintained topic map
│   ├── task-orchestration.md
│   ├── knowledge-flywheel.md
│   ├── mcp-architecture.md
│   └── ...
│
├── queries/                        # Q&A explorations (derived, may file back)
│   ├── 2026-04-15_advisor-knowledge-blindness.md
│   └── ...
│
└── _meta/                          # Auto-generated health reports
    ├── staleness-report.md
    ├── coverage-map.md
    └── change-digest.md
```

### Frontmatter Schema

Every file uses YAML frontmatter for machine-readable metadata:

**raw/ articles:**
```yaml
---
title: "Task Dependency Graph Design"
date: 2026-03-26
topics: [task-orchestration, agent-collaboration]
sources: ["openclaw/src/plugins/", "ClawTeam comparison"]
status: active            # active | superseded | stale
superseded_by: null       # path to newer raw article if superseded
---
```

**concepts/ articles:**
```yaml
---
title: "Task Orchestration in OpenClaw"
slug: task-orchestration
compiled_from:            # provenance — which raw articles
  - raw/2026-03-26_task_dependency_graph_design.md
  - raw/2026-03-28_task_management_grounded_design.md
  - raw/2026-03-30_task_orchestrator_plugin_design.md
last_compiled: 2026-04-15
open_questions: 2         # count, for quick scanning
---
```

**queries/ articles:**
```yaml
---
title: "Advisor Knowledge Blindness"
date: 2026-04-15
question: "What knowledge does the LLM advisor have access to during retry?"
concepts_read: [task-orchestration, knowledge-flywheel]
filed_back_to: [task-orchestration]   # which concepts were updated
---
```

---

## 5. MCP Tool Surface

The plugin registers a single `wiki` tool with action-based dispatch
(same pattern as `task-orchestrator`'s `tasks` tool).

### 5.1 Search and Read: Via `registerMemoryCorpusSupplement` (Not a Separate Tool)

**Key discovery:** OpenClaw's `memory_search` already supports a `corpus` parameter:

| `corpus` value | What it searches | Default? |
|---|---|---|
| `"memory"` | MEMORY.md + memory/*.md + shared_learnings (via extraPaths) | **Yes** — this is what agents get when they call `memory_search` normally |
| `"wiki"` | Only registered wiki corpus supplements | No — must be explicit |
| `"all"` | Both memory + wiki, results merged by score | No — must be explicit |

The plugin uses `api.registerMemoryCorpusSupplement()` to register its concepts
as a separate wiki corpus. This means:

- **No dilution.** Default `memory_search` calls never see wiki concepts.
- **Opt-in access.** Agents pass `corpus="wiki"` to search wiki only.
- **No separate search tool.** Search and read go through existing `memory_search` / `memory_get`.
- **Automatic integration.** memory-core handles corpus routing, score merging, etc.

```typescript
// In plugin registration:
api.registerMemoryCorpusSupplement({
  async search(params) {
    // Embed query using OpenClaw's configured model (same model, separate index)
    const embedding = await embedQuery(params.query);
    const results = await searchConceptIndex(embedding, params.maxResults);
    return results.map(r => ({
      corpus: "wiki" as const,
      path: r.path,
      title: r.title,
      kind: "concept",
      score: r.score,
      snippet: r.snippet,
    }));
  },
  async get(params) {
    // Read a specific concept/raw article by path
    const content = readArticle(params.lookup, params.fromLine, params.lineCount);
    if (!content) return null;
    return {
      corpus: "wiki" as const,
      path: params.lookup,
      title: content.title,
      kind: "concept",
      content: content.body,
      fromLine: params.fromLine,
      lineCount: params.lineCount,
    };
  },
});
```

**How agents use it:**

```
# Operational work (default, unchanged — wiki never appears):
memory_search("Gmail rate limit")
→ shared_learnings only → "use exponential backoff"

# Research query (explicit wiki corpus):
memory_search("task orchestration design", corpus="wiki")
→ wiki concepts only → concepts/task-orchestration.md

# Cross-cutting query (explicit all):
memory_search("task recovery", corpus="all")
→ both → shared_learning rule + concept article, ranked by score
```

### 5.2 Wiki Tool Actions (Write Operations + Intelligence)

The `wiki` tool handles everything that `memory_search` doesn't — write operations,
compilation, Q&A synthesis, and health checks:

| Action | Type | Intelligence | Description |
|---|---|---|---|
| `index` | Read | None | Return the concept index (`_index.md`) |
| `ingest_raw` | Write | LLM (auto-tag) | Add a new raw article to raw/, auto-assign topics |
| `compile` | Write | LLM (synthesis) | Recompile a concept from its raw sources |
| `query` | Write | LLM (synthesis) | Ask a cross-concept question, save answer to queries/ |
| `file_back` | Write | None | Append insight to a concept article (LLM already ran on caller side) |
| `lint` | Read | LLM (analysis) | Run health check: staleness, orphans, contradictions |
| `tag` | Write | LLM (classify) | Assign/update topic tags on a raw article |
| `prime` | Read | Embeddings | Return concept summaries relevant to a task description |
| `status` | Read | None | Wiki health: article counts, staleness, coverage |
| `digest` | Write | LLM + git | Scan tracked repos for changes, produce change digest |

### 5.3 Tool Schema

```typescript
// Search and read go through memory_search/memory_get (corpus="wiki")
// This tool handles write operations + intelligence only
const ACTIONS = [
  "index",
  "ingest_raw",
  "compile",
  "query",
  "file_back",
  "lint",
  "tag",
  "prime",
  "status",
  "digest",
] as const;

export const WikiToolSchema = Type.Object(
  {
    action: stringEnum(ACTIONS, {
      description: "Action to perform on the knowledge wiki",
    }),

    // query / prime
    query: Type.Optional(
      Type.String({ description: "Question text (for query action) or task description (for prime)" }),
    ),

    // compile / file_back
    slug: Type.Optional(
      Type.String({ description: "Concept slug (e.g. 'task-orchestration')" }),
    ),

    // tag
    rawPath: Type.Optional(
      Type.String({ description: "Raw article filename (e.g. '2026-03-26_task_dep...')" }),
    ),

    // ingest_raw
    title: Type.Optional(
      Type.String({ description: "Title for new raw article" }),
    ),
    content: Type.Optional(
      Type.String({ description: "Markdown content for new raw article" }),
    ),
    topics: Type.Optional(
      Type.String({ description: "Comma-separated topic slugs (optional — auto-tagged if omitted)" }),
    ),

    // file_back
    section: Type.Optional(
      Type.String({ description: "Section heading to add/update in concept" }),
    ),
    insight: Type.Optional(
      Type.String({ description: "New insight to file back into concept article" }),
    ),

    // tag
    addTopics: Type.Optional(
      Type.String({ description: "Comma-separated topics to add" }),
    ),
    removeTopics: Type.Optional(
      Type.String({ description: "Comma-separated topics to remove" }),
    ),

    // digest
    repo: Type.Optional(
      Type.String({ description: "Repo path for digest (default: all tracked repos)" }),
    ),
    sinceDays: Type.Optional(
      Type.Number({ description: "Look back N days for digest (default: 7)" }),
    ),
  },
  { additionalProperties: false },
);
```

### 5.4 How Each Agent Uses the Tools

**Claude Code** (via MCP — `openclaw mcp serve-tools`):
```
User: "Analyze the latest OpenClaw task system changes"

Claude Code:
  1. wiki.prime("OpenClaw task system changes")
     → Returns: concept summary + open questions + priming instructions
  2. [reads code diff with concept context in mind]
  3. wiki.ingest_raw(title, content)
     → Auto-tagged to task-orchestration by LLM
  4. wiki.compile("task-orchestration")
     → Recompiles concept from all sources including the new one
```

**Hermes Agent** (via MCP — `config.yaml`):
```
User: "What are the blind spots in our task recovery system?"

Hermes:
  1. memory_search("task recovery blind spots", corpus="wiki")
     → Searches wiki concepts only via corpus supplement
  2. memory_get("concepts/task-orchestration.md", corpus="wiki")
     → Reads full concept article
  3. memory_get("concepts/knowledge-flywheel.md", corpus="wiki")
     → Cross-reference second concept
  4. wiki.query("What are the blind spots in task recovery?")
     → LLM synthesizes cross-concept answer, saves to queries/
     → Returns answer + file-back suggestion
  5. wiki.file_back("task-orchestration", "Advisor Knowledge Blindness", insight)
```

**OpenClaw internal agents** (via Plugin SDK — native):
```
Cron (weekly lint):
  1. wiki.lint()
     → LLM analyzes staleness, orphans, contradictions
     → Writes report to _meta/staleness-report.md

Cron (weekly digest):
  1. wiki.digest()
     → Scans tracked repos git logs
     → Produces change digest to _meta/change-digest.md
     → Flags concepts for recompilation

Dream cycle (heartbeat/idle):
  1. Check _meta/staleness-report.md for stale concepts
  2. For each stale concept: wiki.compile(slug)
  3. Recompiles using configured local models
```

---

## 6. Plugin Architecture

### 6.1 Component Overview

```
extensions/knowledge-wiki/
├── openclaw.plugin.json            # Manifest
├── package.json
├── index.ts                        # Plugin entry (definePluginEntry)
└── src/
    ├── store.ts                    # SQLite index DB (metadata + FTS5, disposable)
    ├── wiki-fs.ts                  # Filesystem ops (read/write markdown, parse frontmatter)
    ├── tool.ts                     # Tool schema + action dispatch
    ├── compiler.ts                 # Concept compilation (LLM via subagent.run or inline)
    ├── tagger.ts                   # Topic tagging (LLM-powered classification)
    ├── linter.ts                   # Health check / staleness / contradiction detection (LLM)
    ├── search.ts                   # Semantic search (delegates to OpenClaw memory search)
    ├── priming.ts                  # Concept-primed prompt injection (embeddings for relevance)
    ├── digest.ts                   # Git change digest (git log + topic mapping)
    └── types.ts                    # Data types
```

### 6.2 Persistence: Markdown SOT + SQLite Index

**Markdown files** are the source of truth — human-readable, Obsidian-compatible, git-trackable.

**SQLite** (`~/.openclaw/data/knowledge-wiki.db`) is a search/metadata index only.
If the DB is deleted, it can be fully rebuilt from the markdown files at `gateway_start`.

```sql
-- Metadata index (rebuilt from frontmatter on startup)
CREATE TABLE articles (
  path TEXT PRIMARY KEY,            -- relative path from wikiDir
  folder TEXT NOT NULL,             -- 'raw', 'concepts', 'queries'
  title TEXT NOT NULL,
  slug TEXT,                        -- concept slug (null for raw/queries)
  status TEXT DEFAULT 'active',     -- active, superseded, stale
  created_at INTEGER,
  last_compiled INTEGER,            -- concepts only
  last_verified INTEGER,            -- last staleness check
  content_hash TEXT,                -- detect external edits (Obsidian)
  updated_at INTEGER NOT NULL
);

-- Topic tagging (many-to-many)
CREATE TABLE article_topics (
  path TEXT NOT NULL REFERENCES articles(path) ON DELETE CASCADE,
  topic TEXT NOT NULL,
  PRIMARY KEY (path, topic)
);
CREATE INDEX idx_topic ON article_topics(topic);

-- Compilation provenance
CREATE TABLE concept_sources (
  concept_slug TEXT NOT NULL,
  raw_path TEXT NOT NULL,
  PRIMARY KEY (concept_slug, raw_path)
);

-- FTS5 keyword search (fallback when embedding service is unavailable)
CREATE VIRTUAL TABLE articles_fts USING fts5(
  path, title, body,
  tokenize='porter unicode61'
);
```

**Search strategy (two-tier):**
1. **Primary: Semantic search** via OpenClaw's `memorySearch` infrastructure (LanceDB + Gemini embeddings). The wiki's `concepts/` directory is added to `memorySearch.extraPaths`. The plugin calls `api.runtime.memory.search()` (or equivalent memory search API).
2. **Fallback: FTS5 keyword search** if the embedding service is temporarily unavailable. Fail-open — returns keyword matches rather than nothing.

### 6.3 Registration Pattern

```typescript
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk/core";

export default definePluginEntry({
  id: "knowledge-wiki",
  name: "Knowledge Wiki",
  description:
    "Personal knowledge wiki flywheel: raw → concepts → queries with " +
    "concept-primed generation, Q&A file-back, and automated health checks.",
  configSchema: { /* see Section 8.1 */ },

  register(api: OpenClawPluginApi) {
    if (!api.runtime?.subagent) return; // skip build-time scanning

    const config = resolveConfig(api);
    const store = new WikiStore(resolveDbPath(api));
    const wikiFs = new WikiFs(config.wikiDir, store);
    const search = new WikiSearch(wikiFs, store, api);
    const tagger = new TopicTagger(wikiFs, store, api);
    const compiler = new ConceptCompiler(wikiFs, store, api);
    const linter = new WikiLinter(wikiFs, store, api);
    const primer = new ConceptPrimer(wikiFs, store, search);
    const digest = new ChangeDigest(wikiFs, store, config);

    // -- Tool registration (auto-exposed via MCP) --
    api.registerTool(
      buildWikiTool({ store, wikiFs, compiler, search, linter, tagger, primer, digest }),
    );

    // -- Concept priming hook (automatic for internal agents) --
    if (config.conceptPriming) {
      api.on("before_prompt_build", async (event, ctx) => {
        try {
          const priming = await primer.getPrimingContext(event, ctx);
          if (!priming) return {};
          return { prependContext: [priming] };
        } catch {
          return {}; // fail-open: never block agents
        }
      });
    }

    // -- File watcher for external edits (Obsidian) --
    wikiFs.startWatching(() => {
      store.rebuildIndexIncremental(wikiFs); // only re-index changed files
    });

    // -- Rebuild full index on gateway start --
    api.on("gateway_start", async () => {
      await store.rebuildIndex(wikiFs);
    });

    // -- Register cron for weekly lint --
    api.on("gateway_start", () => {
      if (config.lintCron) {
        api.logger.info(`Wiki lint scheduled: ${config.lintCron}`);
        // Registers with task-orchestrator's schedule system
      }
    });
  },
});
```

---

## 7. Core Mechanisms (Implementation Detail)

### 7.1 Semantic Search (Own Index, Shared Embedding Model)

**Why keyword search isn't enough:**
A user or agent searching "what happens when a task stalls" needs to find
`concepts/task-orchestration.md` even though the exact phrase "task stalls"
may not appear — the concept article might say "running task exceeds
stallThresholdMs" or "mark as stalled after inactivity period."

**Critical design choice: Separate index, not shared `memorySearch.extraPaths`.**

The wiki does NOT add `concepts/` to `memorySearch.extraPaths`. Doing so would
pollute `memory_search` results — agents searching for operational rules ("Gmail
rate limit") would get back 3000-word concept articles alongside the crisp
shared_learning rule they actually need. The two search systems serve different
consumers and must stay separate:

```
memory_search  →  shared_learnings/ + session memory
                  (operational: rules, patterns, gotchas for agents)
                  Owned by: memory-core + proactive-learning

wiki.search    →  concepts/ (primary) + raw/ (fallback)
                  (research: understanding, design decisions for humans + research agents)
                  Owned by: knowledge-wiki plugin (this plugin)
```

The wiki uses the **same embedding model** (Gemini `gemini-embedding-001` via
OpenClaw's configured provider) but maintains its **own separate vector index**.

**Implementation:**

```typescript
class WikiSearch {
  // Own embedding index — NOT shared with memory_search
  private embeddings: Map<string, Float32Array> = new Map();

  constructor(
    private wikiFs: WikiFs,
    private store: WikiStore,
    private api: OpenClawPluginApi,
  ) {}

  // Called at gateway_start and after compilation/ingest
  async rebuildEmbeddings(): Promise<void> {
    const concepts = this.store.getAllConcepts();
    for (const c of concepts) {
      const content = this.wikiFs.readConcept(c.slug);
      // Use OpenClaw's configured embedding model (same model, separate index)
      const embedding = await this.api.runtime.memory.embed(
        `${content.title}\n${content.summary}\n${content.openQuestions}`
      );
      this.embeddings.set(c.slug, embedding);
      // Also persist to SQLite for faster startup
      this.store.saveEmbedding(c.slug, embedding);
    }
  }

  async search(query: string, maxResults = 5): Promise<SearchResult[]> {
    try {
      // 1. Embed the query using OpenClaw's configured embedding model
      const queryEmbedding = await this.api.runtime.memory.embed(query);

      // 2. Search OUR index (concepts/ only), not the system memory index
      const scored = [...this.embeddings.entries()]
        .map(([slug, emb]) => ({ slug, score: cosineSimilarity(queryEmbedding, emb) }))
        .sort((a, b) => b.score - a.score)
        .slice(0, maxResults);

      return scored.map(s => ({
        slug: s.slug,
        path: `concepts/${s.slug}.md`,
        score: s.score,
        title: this.store.getTitle(s.slug),
      }));
    } catch {
      // Fallback: FTS5 keyword search when embedding service is unavailable
      return this.store.fts5Search(query, maxResults);
    }
  }
}
```

### 7.2 Topic Tagger (LLM-Powered Classification)

**Trigger:** Called during `ingest_raw` if topics are not provided, or via `wiki.tag()`.

```typescript
class TopicTagger {
  async autoTag(articlePath: string): Promise<string[]> {
    // 1. Read the new article
    const content = this.wikiFs.read(articlePath);

    // 2. Read existing concept index for the topic vocabulary
    const existingTopics = this.store.getAllTopicSlugs();

    // 3. LLM classification — use configured model (local Gemini, etc.)
    const prompt = `
Given this article and the existing topic vocabulary, assign 1-3 topics.

Existing topics: ${existingTopics.join(", ")}
You may also propose ONE new topic if none fit well.

Article title: ${content.title}
Article excerpt (first 500 chars): ${content.body.slice(0, 500)}

Return JSON: { "topics": ["topic-slug-1", "topic-slug-2"] }
`;

    const response = await this.callLLM(prompt);
    const topics = JSON.parse(response).topics;

    // 4. Update frontmatter and SQLite index
    this.wikiFs.updateFrontmatter(articlePath, { topics });
    this.store.setTopics(articlePath, topics);

    return topics;
  }

  private async callLLM(prompt: string): Promise<string> {
    // Use OpenClaw's configured model infrastructure
    // Option A: api.runtime.subagent.run() for isolated LLM call
    // Option B: api.runtime.inference.complete() if available on plugin API
    // Option C: Direct provider call via api.runtime
    // Choose based on what's available on the plugin SDK surface
  }
}
```

### 7.3 Concept Compiler (LLM Synthesis via Subagent)

**Trigger:** `wiki.compile(slug)` — manual, auto after `ingest_raw` if configured, or dream cycle.

```typescript
class ConceptCompiler {
  async compile(slug: string): Promise<void> {
    // 1. Get all raw articles tagged to this concept
    const sourcePaths = this.store.getSourcesForConcept(slug);
    if (sourcePaths.length === 0) throw new Error(`No sources for concept: ${slug}`);

    // 2. Read existing concept (if any) to preserve filed-back Q&A sections
    const existingConcept = this.wikiFs.readConceptSafe(slug);

    // 3. Read all source articles, sorted chronologically
    const sources = sourcePaths
      .map(p => ({ path: p, ...this.wikiFs.readWithFrontmatter(p) }))
      .sort((a, b) => a.date - b.date);

    // 4. Compile via subagent (isolated LLM task, uses configured local models)
    const compiled = await this.api.runtime.subagent.run({
      sessionKey: `system:wiki-compiler:${slug}`,
      message: this.buildCompilationPrompt(slug, existingConcept, sources),
      idempotencyKey: `wiki-compile-${slug}-${Date.now()}`,
    });

    // 5. Wait for completion
    const result = await this.api.runtime.subagent.waitForRun({
      runId: compiled.runId,
      timeoutMs: 120_000, // 2 min max for compilation
    });

    // 6. Extract compiled content from subagent's response
    const compiledContent = await this.extractResult(compiled.runId);

    // 7. Atomic write: temp file → rename (never lose the old concept)
    this.wikiFs.writeConceptAtomic(slug, compiledContent, {
      compiled_from: sourcePaths,
      last_compiled: new Date().toISOString(),
    });

    // 8. Update concept index
    this.wikiFs.updateConceptIndex();

    // 9. Clean up subagent session
    await this.api.runtime.subagent.deleteSession({
      sessionKey: `system:wiki-compiler:${slug}`,
    });
  }
}
```

**Compilation prompt:**

```markdown
You are compiling a concept article for a personal knowledge wiki.

## Input
- Concept slug: {slug}
- Existing concept article (if any — preserve filed-back Q&A sections): {existingConcept}
- Source articles ({count} total, chronological): {sources}

## Rules
1. Produce ONE canonical article representing CURRENT understanding
2. Structure by subtopic, NOT by source article or date
3. If sources contradict, use the LATEST source as authoritative
4. Include a "Key Decisions and Why" table with settled-when dates
5. Include an "Open Questions" section — unresolved issues surfaced across sources
6. Include an "Evolution Timeline" at the bottom — compressed chronology
7. PRESERVE any "## Known Limitation" or "## Design Lessons" sections from
   the existing concept — these are filed-back Q&A insights
8. Link back to raw sources with relative paths: [title](../raw/filename.md)
9. DO NOT summarize each source sequentially — synthesize across them
10. A reader should understand the current state in 2 minutes without reading any raw article
```

### 7.4 Concept Priming (Embeddings-Powered, Automatic for Internal Agents)

**Trigger:**
- Internal agents: `before_prompt_build` hook (automatic, every session)
- External agents: `wiki.prime(taskDescription)` tool action (explicit, per behavioral contract)

```typescript
class ConceptPrimer {
  async getPrimingContext(
    event: PluginHookBeforePromptBuildEvent,
    ctx: PluginHookContext,
  ): Promise<string | null> {
    // 1. Extract topic signal from latest user message
    const userMessage = this.extractLatestUserMessage(event);
    if (!userMessage) return null;

    // 2. Semantic search for relevant concepts (embeddings)
    const relevant = await this.search.search(userMessage, 2);
    if (relevant.length === 0) return null;

    // 3. Build compact priming block (within token budget)
    const blocks: string[] = [];
    let tokenBudget = this.config.primingMaxTokens;

    for (const result of relevant) {
      const concept = this.wikiFs.readConcept(result.slug);
      if (!concept) continue;

      // Extract key sections only (not full article)
      const summary = this.extractPrimingSummary(concept);
      const estimatedTokens = Math.ceil(summary.length / 4);
      if (estimatedTokens > tokenBudget) break;

      blocks.push(summary);
      tokenBudget -= estimatedTokens;
    }

    if (blocks.length === 0) return null;

    // 4. Wrap with priming instruction
    return [
      "# Knowledge Wiki — Concept Priming",
      "",
      "The following represents what is already known about topics relevant",
      "to this task. Focus on what is NEW relative to this understanding.",
      "If you discover something that changes or extends this knowledge,",
      "use the `wiki` tool: `ingest_raw` to record, `file_back` to enrich.",
      "",
      ...blocks,
    ].join("\n");
  }

  // Extracts: title, one-line summary, open questions, key decisions
  // NOT the full article — keeps within token budget
  private extractPrimingSummary(concept: ConceptArticle): string {
    return [
      `## Existing Knowledge: ${concept.title}`,
      "",
      concept.summary,      // first paragraph or explicit summary section
      "",
      "### Open Questions",
      concept.openQuestions, // extracted from ## Open Questions section
      "",
      "### Key Decisions",
      concept.keyDecisions,  // extracted from decision table
    ].join("\n");
  }
}
```

### 7.5 Q&A with File-Back

**Trigger:** `wiki.query(question)` — any agent asks a cross-concept question.

```typescript
async function handleQuery(params: { query: string }): Promise<string> {
  // 1. Semantic search for relevant concepts
  const relevant = await search.search(params.query, 3);

  // 2. Read full concept articles (not just summaries — Q&A needs depth)
  const concepts = relevant.map(r => ({
    slug: r.slug,
    content: wikiFs.readConcept(r.slug),
  }));

  // 3. Synthesize answer via LLM (subagent for isolation)
  const answer = await synthesizeViaSubagent({
    question: params.query,
    concepts,
    prompt: `
Synthesize an answer from these concept articles. Focus on:
1. Cross-cutting connections between concepts
2. Gaps — things the concepts SHOULD cover but don't
3. Contradictions between concepts

If you discover a non-obvious insight, suggest it for file-back.

Return JSON:
{
  "answer": "markdown answer text",
  "fileBackSuggestion": "description of insight to file back" | null,
  "suggestedSlug": "concept-slug" | null,
  "suggestedSection": "Section Heading" | null
}
`,
  });

  // 4. Save to queries/
  const queryPath = wikiFs.writeQuery({
    title: summarizeQuestion(params.query),
    date: new Date().toISOString(),
    question: params.query,
    answer: answer.content,
    concepts_read: relevant.map(r => r.slug),
    filed_back_to: [],
  });

  // 5. Return answer + file-back suggestion
  return [
    answer.content,
    "",
    "---",
    `Saved to: queries/${queryPath}`,
    answer.fileBackSuggestion
      ? [
          "",
          `**File-back opportunity:** ${answer.fileBackSuggestion}`,
          `To file back: wiki.file_back(slug="${answer.suggestedSlug}", ` +
          `section="${answer.suggestedSection}", insight="...")`,
        ].join("\n")
      : "",
  ].join("\n");
}
```

### 7.6 Lint Pass (LLM-Powered Health Check)

**Trigger:** `wiki.lint()` — manual or weekly cron via `task-orchestrator`.

```typescript
class WikiLinter {
  async lint(): Promise<LintReport> {
    const report: LintReport = {
      stale: [],
      orphaned: [],
      thinCoverage: [],
      contradictions: [],
      stats: this.store.getStats(),
    };

    const concepts = this.store.getAllConcepts();

    // 1. Staleness: concepts whose sources have newer raw articles
    for (const c of concepts) {
      const newestSource = this.store.getNewestSourceDate(c.slug);
      if (newestSource && newestSource > c.last_compiled) {
        report.stale.push({
          slug: c.slug,
          reason: "New raw material since last compilation",
          lastCompiled: c.last_compiled,
          newestSource,
        });
      }
      const daysSinceVerified = c.last_verified
        ? (Date.now() - c.last_verified) / 86_400_000
        : Infinity;
      if (daysSinceVerified > this.config.stalenessDays) {
        report.stale.push({
          slug: c.slug,
          reason: `Not verified in ${Math.floor(daysSinceVerified)} days`,
        });
      }
    }

    // 2. Orphaned raw articles (not tagged to any concept)
    for (const r of this.store.getAllRaw()) {
      if (this.store.getTopicsForArticle(r.path).length === 0) {
        report.orphaned.push(r.path);
      }
    }

    // 3. Thin coverage (concepts with ≤1 source)
    for (const c of concepts) {
      const count = this.store.getSourceCount(c.slug);
      if (count <= 1) {
        report.thinCoverage.push({ slug: c.slug, sourceCount: count });
      }
    }

    // 4. Contradiction detection (LLM — compare concept pairs)
    //    Only check concepts that share topics or have cross-references
    const relatedPairs = this.store.getRelatedConceptPairs();
    for (const [slugA, slugB] of relatedPairs) {
      const contentA = this.wikiFs.readConcept(slugA);
      const contentB = this.wikiFs.readConcept(slugB);
      const contradictions = await this.detectContradictions(contentA, contentB);
      if (contradictions.length > 0) {
        report.contradictions.push({ slugA, slugB, issues: contradictions });
      }
    }

    // 5. Write report to _meta/
    this.wikiFs.writeMeta("staleness-report.md", formatLintReport(report));

    return report;
  }
}
```

### 7.7 Change Digest (Git + Cron)

**Trigger:** Weekly cron via `task-orchestrator`, or manual `wiki.digest()`.

```typescript
class ChangeDigest {
  async digest(sinceDays = 7): Promise<DigestResult> {
    const since = new Date(Date.now() - sinceDays * 86_400_000).toISOString().split("T")[0];
    const results: DigestEntry[] = [];

    for (const repo of this.config.trackedRepos) {
      // 1. Get git log for tracked directories
      const log = await execGit(repo.path,
        `log --since="${since}" --stat --oneline -- ${repo.watchDirs.join(" ")}`
      );
      if (!log.trim()) continue;

      // 2. Map changed directories to concept topics
      const affectedTopics = new Set<string>();
      for (const [dir, topic] of Object.entries(repo.topicMapping)) {
        if (log.includes(dir)) affectedTopics.add(topic);
      }

      // 3. Create digest entry (signal, not raw article)
      if (affectedTopics.size > 0) {
        results.push({
          repo: repo.path,
          since,
          affectedTopics: [...affectedTopics],
          commitSummary: log.slice(0, 2000), // truncated for readability
        });
      }
    }

    // 4. Write digest to _meta/
    this.wikiFs.writeMeta("change-digest.md", formatDigest(results));

    // 5. Flag affected concepts for recompilation
    for (const entry of results) {
      for (const topic of entry.affectedTopics) {
        this.store.flagForRecompilation(topic);
      }
    }

    return { entries: results, conceptsFlagged: results.flatMap(e => e.affectedTopics) };
  }
}
```

**The digest is a signal, not a raw article.** It tells the dream cycle "these concepts may be stale because the underlying code changed." The dream cycle then spawns a concept-primed agent to do the actual analysis — preserving the quality bar.

### 7.8 Dream Cycle (Heartbeat + Cron Integration)

**How it uses OpenClaw's scheduling infrastructure:**

```typescript
// Registered in plugin's gateway_start handler

// Option A: Task-orchestrator workflow template
const WIKI_DREAM_WORKFLOW = {
  id: "wiki-dream-cycle",
  name: "Knowledge Wiki Dream Cycle",
  steps: [
    {
      name: "digest",
      task: "Run wiki.digest() to scan tracked repos for changes",
      dispatch: { mode: "spawn", agentId: "system" },
    },
    {
      name: "lint",
      task: "Run wiki.lint() to check wiki health",
      dispatch: { mode: "spawn", agentId: "system" },
      blockedByNames: ["digest"],
    },
    {
      name: "recompile",
      task: "For each stale concept flagged by lint or digest, run wiki.compile(slug)",
      dispatch: { mode: "spawn", agentId: "system" },
      blockedByNames: ["lint"],
    },
  ],
};

// Option B: Cron schedule
// schedule_add: cron "0 3 * * 0" (Sunday 3am) → runs wiki-dream-cycle workflow
// This uses task-orchestrator's existing schedule infrastructure
```

---

## 8. Plugin Configuration

### 8.1 `openclaw.plugin.json`

```json
{
  "id": "knowledge-wiki",
  "name": "Knowledge Wiki",
  "description": "Personal knowledge wiki flywheel with concept compilation, semantic search, Q&A file-back, and automated dream cycles.",
  "contracts": {
    "tools": ["wiki"]
  },
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "wikiDir": {
        "type": "string",
        "description": "Absolute path to wiki root directory containing raw/, concepts/, queries/, _meta/ subdirs."
      },
      "autoCompile": {
        "type": "boolean",
        "default": false,
        "description": "Auto-recompile affected concepts when new raw articles are ingested via ingest_raw."
      },
      "autoTag": {
        "type": "boolean",
        "default": true,
        "description": "Auto-assign topics via LLM when ingesting raw articles without explicit topics."
      },
      "conceptPriming": {
        "type": "boolean",
        "default": true,
        "description": "Inject relevant concept context into agent prompts via before_prompt_build hook."
      },
      "primingMaxTokens": {
        "type": "number",
        "default": 2000,
        "description": "Max tokens for concept priming injection per agent turn."
      },
      "stalenessDays": {
        "type": "number",
        "default": 30,
        "description": "Days before a concept is flagged as stale in lint reports."
      },
      "compilationModel": {
        "type": "string",
        "description": "Model to use for compilation/Q&A. Uses agent's default model if not set."
      },
      "trackedRepos": {
        "type": "array",
        "description": "Git repos to watch for changes relevant to wiki concepts.",
        "items": {
          "type": "object",
          "properties": {
            "path": { "type": "string", "description": "Absolute path to repo root" },
            "watchDirs": {
              "type": "array",
              "items": { "type": "string" },
              "description": "Directories within the repo to watch for changes"
            },
            "topicMapping": {
              "type": "object",
              "description": "Map of directory prefixes to concept slugs",
              "additionalProperties": { "type": "string" }
            }
          }
        }
      },
      "lintCron": {
        "type": "string",
        "default": "0 3 * * 0",
        "description": "Cron expression for weekly lint pass (default: Sunday 3am)"
      },
      "digestCron": {
        "type": "string",
        "default": "0 4 * * 1",
        "description": "Cron expression for weekly change digest (default: Monday 4am)"
      }
    }
  }
}
```

### 8.2 `openclaw.json` Integration

```json
{
  "plugins": {
    "knowledge-wiki": {
      "enabled": true,
      "config": {
        "wikiDir": "/Volumes/Motus_SSD/CommunitySharing/Agent_Exploration/KnowledgeWiki",
        "autoCompile": false,
        "autoTag": true,
        "conceptPriming": true,
        "compilationModel": "gemini-2.5-pro",
        "trackedRepos": [
          {
            "path": "~/openclaw",
            "watchDirs": ["src/tasks/", "extensions/task-orchestrator/", "extensions/proactive-learning/"],
            "topicMapping": {
              "src/tasks/": "task-orchestration",
              "extensions/task-orchestrator/": "task-orchestration",
              "extensions/proactive-learning/": "knowledge-flywheel"
            }
          }
        ]
      }
    }
  },
  "memorySearch": {
    "extraPaths": [
      "~/.clawdbot/shared_learnings",
      "~/.clawdbot/skills"
    ]
  }
}
```

Note: `concepts/` is deliberately NOT added to `memorySearch.extraPaths`. The wiki
maintains its own separate embedding index using the same model but a separate vector
store. This prevents search pollution — `memory_search` stays clean for operational
agent context (shared_learnings, session memory), while `wiki.search` serves research
knowledge. Same embedding model, separate indexes, separate consumers.

---

## 9. Cross-Platform Integration

### 9.1 How Each Agent Connects

| Agent | Connection | Intelligence Available | Concept Priming |
|---|---|---|---|
| **OpenClaw subagents** | Plugin SDK (native) | Full: embeddings, LLM, cron, hooks | Automatic via `before_prompt_build` |
| **Claude Code** | MCP via `openclaw mcp serve-tools` | Full: all tool actions available | Via `wiki.prime()` action + CLAUDE.md rules |
| **Hermes Agent** | MCP via `config.yaml` | Full: all tool actions available | Via `wiki.prime()` action + SKILLPACK rules |
| **Antigravity** | Filesystem + future MCP | Read-only (browse markdown in Obsidian) | Manual (read concept files) |
| **Human (you)** | Obsidian | Read + light edit (file watcher syncs) | Visual (browse concepts, graph view) |

### 9.2 No Separate MCP Server Needed

The `wiki` tool is auto-discovered by `plugin-tools-serve.ts` alongside existing tools:

```
openclaw mcp serve-tools  →  exposes:
  ├── memory_search    (from memory-core)
  ├── memory_get       (from memory-core)
  ├── tasks            (from task-orchestrator)
  └── wiki             (from knowledge-wiki)  ← NEW, zero config
```

Claude Code and Hermes connect via the existing `openclaw-brain` MCP server entry.
No new MCP server config, no new process, no new port.

### 9.3 Behavioral Contract Updates

### 9.3 Global Skills (Single Source of Truth)

Wiki workflow skills live in `~/.agents/skills/` — the global skill directory
shared by all agent platforms. Same pattern as the existing `digital-me` skill.

```
~/.agents/skills/
├── digital-me/SKILL.md              # existing — behavioral playbook
├── wiki-research/SKILL.md           # NEW — concept-primed investigation
├── wiki-ask/SKILL.md                # NEW — cross-concept Q&A
└── wiki-review/SKILL.md             # NEW — health check + compilation
```

The plugin does NOT bundle or serve skills. It registers the `wiki` tool;
the global skills reference that tool. Every platform (Claude Code, OpenClaw,
Antigravity) reads from `~/.agents/skills/` — one source of truth, zero drift.

**`~/.agents/skills/wiki-research/SKILL.md`:**

```markdown
---
name: wiki-research
description: >
  Concept-primed research workflow for the Knowledge Wiki. Use when analyzing
  codebases, articles, papers, or any new material. Primes with existing
  concept knowledge, then records delta-focused analysis. Does NOT compile —
  compilation is handled by wiki-review or the dream cycle. Triggers on:
  'research', 'analyze', 'investigate', 'learn about', 'deep dive'.
---

# Wiki Research — Concept-Primed Investigation

## Step 1: Prime
Call `wiki.prime({topic})`.
Read the returned concept summaries carefully — they represent
what is ALREADY KNOWN. Note the open questions.

If you need full depth on a concept:
  `memory_search({concept title}, corpus="wiki")`
  `memory_get({path}, corpus="wiki")`

## Step 2: Investigate
Analyze the target material (codebase diff, article, paper, etc.).

Your job is NOT to describe the material from scratch.
Your job is to describe:
1. What is NEW relative to existing concept understanding
2. What CHANGES or INVALIDATES existing knowledge
3. What RESOLVES open questions listed in the concept
4. What creates NEW open questions

## Step 3: Record
Call `wiki.ingest_raw(title={title}, content={your analysis})`.
Topics are auto-assigned by LLM. If you know the topic, pass it:
`topics="task-orchestration"`.

## Step 4: Cross-Check
If you noticed connections to OTHER concepts during investigation:
  Call `wiki.file_back(slug={other concept}, section={heading}, insight={connection})`.
This is how the wiki gets smarter — connections between concepts
that no single investigation would discover.

## Step 5: Flag
Note which concepts may need recompilation based on your findings.
Example: "Concept `task-orchestration` has new material — run wiki-review
or wait for dream cycle to recompile."

Do NOT compile yourself. Compilation is a maintenance operation that
may batch multiple new raw articles. It is handled by:
- `wiki-review` skill (manual, on-demand)
- Dream cycle (automated weekly cron)
```

**`~/.agents/skills/wiki-ask/SKILL.md`:**

```markdown
---
name: wiki-ask
description: >
  Cross-concept Q&A workflow for the Knowledge Wiki. Use when asking research
  questions that may span multiple concepts. Synthesizes across the wiki and
  suggests file-back for new insights. Triggers on: 'what do we know about',
  'wiki ask', 'knowledge question', 'cross-reference'.
---

# Wiki Ask — Cross-Concept Q&A

## Step 1: Search
Call `memory_search({question}, corpus="wiki")` to find relevant concepts.
If nothing found, try `memory_search({question}, corpus="all")` for broader results.

## Step 2: Deep Read
For each relevant concept:
  `memory_get({path}, corpus="wiki")` to read the full article.
Follow source links to raw/ if more depth needed.

## Step 3: Synthesize
Answer the question by synthesizing ACROSS concepts.
Focus on: cross-cutting connections, gaps, contradictions.
Do NOT just summarize one concept — the value is in connections.

## Step 4: Save
Call `wiki.query({question})` to save your synthesis to queries/.

## Step 5: File Back
If your synthesis revealed a non-obvious insight:
  - Identify which concept(s) should be enriched
  - Call `wiki.file_back(slug, section, insight)` for each
  - Add provenance: "Discovered via Q&A on {date}"

If no new insight: state "Answer fully covered by existing concepts."

## corpus parameter guide
- Default (no corpus): searches operational knowledge only (shared_learnings)
- corpus="wiki": searches compiled wiki concepts only
- corpus="all": searches both, results merged by relevance score
```

**`~/.agents/skills/wiki-review/SKILL.md`:**

```markdown
---
name: wiki-review
description: >
  Knowledge Wiki health check and maintenance. Runs lint, checks for staleness,
  orphaned articles, and contradictions. Can trigger recompilation for stale
  concepts. Triggers on: 'wiki review', 'wiki health', 'check wiki',
  'what needs updating', 'wiki status'.
---

# Wiki Review — Health Check + Maintenance

## Step 1: Status
Call `wiki.status()` to get overview: article counts, staleness, coverage.

## Step 2: Lint
Call `wiki.lint()` to generate detailed health report.
Report covers: stale concepts, orphaned raw articles, thin coverage,
contradictions between concepts.

## Step 3: Digest (if tracked repos configured)
Call `wiki.digest()` to check tracked repos for recent code changes
that may affect wiki concepts.

## Step 4: Present
Summarize to the user:
  - N concepts, M raw articles, K queries
  - X concepts are stale (list them with reasons)
  - Y raw articles are orphaned (suggest topic assignments)
  - Z contradictions found (quote the conflicting claims)
  - Recent repo changes affecting concepts A, B, C

## Step 5: Act (with user approval)
For each stale concept: "Recompile {concept}? It has new material since {date}."
If approved: call `wiki.compile(slug)`.
For orphaned articles: suggest topic assignments via `wiki.tag(rawPath, addTopics)`.
```

The `digital-me` skill should also be updated to reference the wiki skills:

```markdown
## Knowledge Wiki

For research and knowledge management, use these companion skills:
- `wiki-research` — concept-primed investigation workflow
- `wiki-ask` — cross-concept Q&A with file-back
- `wiki-review` — health check and maintenance
```

---

## 10. Implementation Phases

### Phase 1: Foundation (Wiki FS + Index + Basic Tools)

- [ ] Create `extensions/knowledge-wiki/` plugin scaffold following existing patterns
- [ ] Implement `WikiFs` — read/write/watch markdown with YAML frontmatter parsing
- [ ] Implement `WikiStore` — SQLite index DB with rebuild-from-filesystem
- [ ] Implement `WikiSearch` — delegate to OpenClaw memory search + FTS5 fallback
- [ ] Implement basic tool actions: `index`, `read_concept`, `read_raw`, `search`, `status`
- [ ] Implement `ingest_raw` — write new raw articles with proper frontmatter
- [ ] Register `wiki` tool via `api.registerTool()`
- [ ] Test: OpenClaw internal agent can search and read the wiki via tool

**Migration step:** Copy existing `LearningNotes/2026-*.md` to `raw/`, create initial
`concepts/_index.md`, set up the wiki directory structure.

### Phase 2: Intelligence Layer (Tagging + Priming + Search)

- [ ] Implement `TopicTagger` — LLM-powered auto-tagging using configured models
- [ ] Implement `tag` tool action
- [ ] Add auto-tag to `ingest_raw` flow (when topics not provided)
- [ ] Implement `ConceptPrimer` — embeddings-powered concept relevance matching
- [ ] Implement `prime` tool action for external agents
- [ ] Implement `before_prompt_build` hook for automatic internal agent priming
- [ ] Run initial tagging pass on all existing raw articles → generate topic map
- [ ] Test: `wiki.prime("task orchestration")` returns relevant concept summaries

### Phase 3: Compilation

- [ ] Implement `ConceptCompiler` — LLM synthesis via `subagent.run()`
- [ ] Implement compilation prompt with synthesis rules
- [ ] Implement `compile` tool action with atomic writes
- [ ] Compile first concept: `task-orchestration` from 8 raw articles
- [ ] Compile 2-3 more concepts to validate the pattern
- [ ] Test: compiled concept is structurally better than any individual raw article

### Phase 4: Q&A + File-Back

- [ ] Implement `query` tool action — cross-concept synthesis + file-back suggestion
- [ ] Implement `file_back` tool action — append insight to concept with provenance
- [ ] Test the full Q&A loop: question → synthesis → file-back → enriched concept
- [ ] Run example Q&As from our earlier conversation (advisor blindness, design archaeology, gap discovery)

### Phase 5: Lint + Digest + Dream Cycle

- [ ] Implement `WikiLinter` — staleness, orphans, coverage, contradictions
- [ ] Implement `ChangeDigest` — git log scanning + topic mapping
- [ ] Implement `lint` and `digest` tool actions
- [ ] Create task-orchestrator workflow template: `wiki-dream-cycle`
- [ ] Register cron schedules for weekly lint and digest
- [ ] Verify wiki embedding index is separate from `memorySearch` index (no cross-pollution)
- [ ] Test: dream cycle detects stale concepts and triggers recompilation
- [ ] Test: `memory_search` returns zero wiki results; `wiki.search` returns zero shared_learnings

### Phase 6: External Agent Integration + Polish

- [ ] Verify `wiki` tool appears in MCP tool list for Claude Code
- [ ] Verify `wiki` tool appears in MCP tool list for Hermes Agent
- [ ] Update CLAW_SKILLPACK.md with wiki protocol
- [ ] Update CLAUDE.md with wiki protocol
- [ ] End-to-end test: Claude Code ingests raw → auto-tagged → cron compiles → Hermes queries
- [ ] Obsidian verification: graph view, backlinks, readability

---

## 11. Migration Plan (Existing LearningNotes → Wiki)

### Step 1: Create Wiki Structure
```bash
mkdir -p ~/KnowledgeWiki/{raw,concepts,queries,_meta}
```

### Step 2: Copy Existing Articles to raw/
```bash
cp /Volumes/Motus_SSD/.../LearningNotes/2026-*.md ~/KnowledgeWiki/raw/
```

### Step 3: Add YAML Frontmatter
LLM task: For each raw article, parse existing headers (`> Date:`, `> Builds on:`)
and generate YAML frontmatter. Topics initially empty (Phase 2 auto-tags them).

### Step 4: Auto-Tag All Raw Articles (Phase 2)
After the tagger is implemented, run a batch tagging pass.
Expected initial concept map (~10-15 topics):

| Concept Slug | Raw Count | Key Topics |
|---|---|---|
| `task-orchestration` | 8 | task graph, dispatch, resolver, checkpoint |
| `knowledge-flywheel` | 5 | memory search, proactive learning, injection |
| `agent-collaboration` | 4 | sessions_spawn, A2A, peer handoff |
| `mcp-architecture` | 3 | MCP server, tool surface, Digital Me |
| `exec-security` | 3 | exec approvals, two-layer flow |
| `openclaw-internals` | 3 | system prompt, session, token efficiency |
| `acp-integration` | 3 | thread-bound agents, debugging |
| `agent-files` | 2 | SOUL.md, MEMORY.md, TOOLS.md |
| `video-production` | 2 | story arc, Manim |
| `discord-operations` | 2 | commands, channels |

### Step 5: Compile Initial Concepts (Phase 3)
Run `wiki.compile(slug)` for each concept, starting with `task-orchestration`
(richest source material, 8 articles).

### Step 6: Verify in Obsidian
Open `~/KnowledgeWiki` as an Obsidian vault. Check:
- `concepts/_index.md` renders as a navigable table
- Concept articles link back to `raw/` sources
- Obsidian graph view shows concept→raw topology
- Search in Obsidian finds both concepts and raw articles

---

## 12. Key Design Decisions

| Decision | Rationale |
|---|---|
| **OpenClaw plugin (not standalone)** | Nearly every operation needs intelligence (embeddings, LLM). Plugin leverages configured local models, LanceDB, cron, heartbeat, hooks — standalone would duplicate all of this. Reliability via graceful degradation, not process isolation. |
| **Separate plugin, not extending proactive-learning** | Different consumer (human vs agents), different structure (concepts vs rules), different lifecycle (compiled vs static). proactive-learning is deterministic routes; this is semantic + LLM. |
| **Markdown SOT + SQLite index** | Human-readable, Obsidian-compatible, git-trackable. SQLite is disposable — rebuilt from markdown at gateway_start. |
| **`registerMemoryCorpusSupplement` (not extraPaths)** | Uses OpenClaw's built-in corpus separation: default `memory_search` returns shared_learnings only (operational), `corpus="wiki"` returns concepts only (research), `corpus="all"` merges both. No dilution — agents get concept articles only when they explicitly ask for them. Same embedding model, separate corpus, routed by the existing memory-core infrastructure. |
| **Compilation via subagent.run()** | Compilation is heavyweight (reads multiple articles, produces synthesis). Subagent provides isolation, timeout, idempotency via `idempotencyKey`. Uses configured models including local ones. |
| **Concept priming via summary, not full articles** | Context budget — full concept articles can be 5K+ tokens. Summary (title + open questions + key decisions) is ~500 tokens per concept. Agent can `read_concept` for full depth. |
| **Semantic search primary, FTS5 fallback** | Semantic search bridges vocabulary gaps ("task stalls" → "stallThresholdMs"). FTS5 is fail-open fallback when embedding service is temporarily unavailable. |
| **Auto-tag via LLM at ingest time** | Ensures every raw article is immediately discoverable via topic. Manual tagging is friction that causes orphaned articles. LLM uses existing topic vocabulary to maintain consistency. |
| **File-back as explicit action, not automatic** | Quality gate — not every Q&A answer should go back. The agent (or user) decides. But the Q&A response includes a file-back suggestion to reduce friction. |
| **Dream cycle via task-orchestrator workflows** | Reuses existing cron + workflow infrastructure. No new scheduling system. Dream cycle is a 3-step workflow: digest → lint → recompile. |
| **Digest as signal, not auto-raw-article** | Preserves quality bar. Auto-generated raw articles from git diffs would be shallow. The digest flags concepts for attention; a concept-primed agent does the real analysis. |
| **Atomic writes for concepts** | A failed compilation must never corrupt the existing concept. Write to temp file, rename on success. Old concept is untouched until new one is fully written. |
| **Fail-open on all hooks and searches** | Wiki unavailability must never block an agent. before_prompt_build returns {} on error. Search returns [] on error. Agent continues without wiki context. |

---

## 13. File Map

```
~/openclaw/extensions/knowledge-wiki/     # Plugin source (in my-extensions branch)
├── openclaw.plugin.json
├── package.json
├── index.ts                              # Plugin entry (~100 lines)
└── src/
    ├── store.ts                          # SQLite index + FTS5 (~200 lines)
    ├── wiki-fs.ts                        # Filesystem ops + frontmatter (~150 lines)
    ├── tool.ts                           # Tool schema + dispatch (~250 lines)
    ├── compiler.ts                       # LLM compilation via subagent (~150 lines)
    ├── tagger.ts                         # LLM topic classification (~100 lines)
    ├── linter.ts                         # Health check + contradiction detection (~150 lines)
    ├── search.ts                         # Semantic search + FTS5 fallback (~80 lines)
    ├── priming.ts                        # Concept-primed prompt injection (~100 lines)
    ├── digest.ts                         # Git change digest (~100 lines)
    └── types.ts                          # Data types (~80 lines)

~/KnowledgeWiki/                          # Wiki data (Obsidian vault, git-tracked)
├── raw/                                  # ~51 existing + growing
├── concepts/                             # ~10-15 compiled, always current
│   └── _index.md                         # Auto-maintained topic map
├── queries/                              # Q&A explorations
└── _meta/                                # Health reports (gitignored)

~/.openclaw/data/knowledge-wiki.db        # SQLite index (disposable, ~500KB)
~/.openclaw/openclaw.json                 # Plugin config entry

~/.agents/skills/                         # Global skills (single source of truth)
├── digital-me/SKILL.md                   # Updated to reference wiki skills
├── wiki-research/SKILL.md                # Concept-primed investigation
├── wiki-ask/SKILL.md                     # Cross-concept Q&A
└── wiki-review/SKILL.md                  # Health check + maintenance
```

---

## 14. Risk Assessment

| Risk | Mitigation |
|---|---|
| Gateway down → wiki inaccessible | Fail-open on all hooks. Filesystem always readable via Obsidian. Non-blocking MCP connection. Graceful degradation to read-only. |
| Compilation produces bad output | Atomic writes — old concept untouched until new one succeeds. Compilation prompt has strict rules. Human can review in Obsidian. |
| Auto-tagging assigns wrong topics | LLM uses existing topic vocabulary (closed set + 1 new proposal). Easy to fix via `wiki.tag()`. Lint catches orphaned articles. |
| Wiki knowledge dilutes agent operational context | Uses `registerMemoryCorpusSupplement` — wiki is a separate corpus. Default `memory_search` (no corpus param) never returns wiki content. Agents only see wiki results when they explicitly pass `corpus="wiki"` or `corpus="all"`. Built into OpenClaw's memory-core routing — no custom filtering needed. |
| Token budget blown by concept priming | `primingMaxTokens` config (default 2000). Priming extracts summaries, not full articles. Agent calls `read_concept` for depth only when needed. |
| Dream cycle runs during active work | Dream cycle workflow uses task-orchestrator's scheduling — respects agent activity. Compilation runs as isolated subagent, doesn't interfere with main sessions. |
| Obsidian edits conflict with plugin writes | File watcher detects external edits via `content_hash`. Plugin always reads before writing. Atomic writes prevent partial conflicts. |
| Embedding service temporarily unavailable | FTS5 keyword fallback. `search` returns keyword matches rather than nothing. Fail-open, not fail-closed. |
