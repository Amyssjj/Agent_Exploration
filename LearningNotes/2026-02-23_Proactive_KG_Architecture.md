# Proactive Knowledge Graph Architecture in OpenClaw

*Created at: 2026-02-23*

This document outlines the architectural strategy for transitioning OpenClaw agents from a reactive semantic search model to a proactive, structured Knowledge Graph Multi-Agent System (KG-MAS).

---

## 1. Problem
OpenClaw's default "Shared Learning" mechanism relies on vector embeddings of unstructured markdown files (`memorySearch.extraPaths`). While excellent for long-form SOPs, it presents three core problems for agentic workflows:
1. **Context Bloat:** Vector search retrieves large text chunks, consuming valuable tokens when injected into subagent prompts.
2. **Poor Relational Logic:** Semantic search cannot easily resolve multi-hop dependencies (e.g., `Script X` -> uses -> `API Y` -> has limitation -> `Rate Limit Z`).
3. **Context Drift:** In long-running sessions, main agents forget to proactively query or update shared learnings because the instructions in `SOUL.md` fall out of their effective attention window.

## 2. Insights
To build truly proactive agents, we must separate **Knowledge Storage** from **System Enforcement**:
1. **Hybrid Storage:** A structured Knowledge Graph for discrete operational facts. Markdown embeddings for unstructured guides.
2. **System over Agent:** We cannot rely on the LLM to "remember" to pass knowledge to subagents. We must mechanically inject knowledge using OpenClaw's native Plugin Hooks.
3. **Mechanical Reflection:** We cannot rely on the LLM to "remember" to write learnings after a 3-hour debug session. We must mechanically enforce reflection using OpenClaw's Heartbeat cron system.

## 3. Method (The Architecture)

The architecture connects knowledge storage with OpenClaw's lifecycle hooks to create a proactive learning loop.

### Phase 1: Proactive Injection (System → Agent)
When an agent spawns a subagent or executes a tool, the system intercepts the action to inject relevant knowledge *before* the LLM sees it.

*   **Strategic Injection (`before_prompt_build` Hook):**
    *   When `sessions_spawn` is called, the plugin intercepts the subagent creation.
    *   It verifies the session is a subagent via `isSubagentSessionKey(ctx.sessionKey)`.
    *   It queries the knowledge store (initially `memory_search`, later a KG) using the task prompt.
    *   It prepends the results as `prependContext` to the subagent's `systemPrompt`.
    *   The subagent wakes up already knowing the constraints.
*   **Operational Injection (`before_tool_call` Hook):**
    *   When an agent calls a technical tool (e.g., `run_python`).
    *   The plugin queries the knowledge store for environment or flag requirements specific to that script.
    *   It mutates the `params` object, silently injecting environment variables before execution.

### Phase 2: Proactive Accumulation (Agent → System)
How agents write new discoveries back to the knowledge store without getting distracted.

*   **Subagent Extraction (`agent_end` Hook):**
    *   When a short-lived subagent finishes, the `agent_end` hook captures their entire chat transcript.
    *   The plugin sends the transcript to a background LLM process to extract new technical learnings and write them to the knowledge store.
*   **Main Agent Enforcement (`HEARTBEAT.md`):**
    *   OpenClaw's cron system periodically forces the agent to read `HEARTBEAT.md`.
    *   The heartbeat checklist mandates: *"Review the last 30 minutes of logs. Did you solve a bug? Log it now."*

### Phase 3: Workflow Orchestration vs Hooks
*   **Rule:** Never use Hooks for business logic (e.g., "If file is approved, spawn writer").
*   **Implementation:** Use explicit state-machine checklists in `SOUL.md` combined with `HEARTBEAT.md` verifications to ensure the LLM actively uses `fs_rename` and `sessions_spawn` to advance workflows visibly.

---

## 4. Current System: Text Embeddings (`shared_learnings`)

### Filesystem Layout
```
~/.clawdbot/
├── shared_learnings/               ← Structured learning entries (source of truth)
│   ├── discord_learnings.md        ← 3 entries (media staging, bot visibility, read receipts)
│   ├── manim_animation_learnings.md← 8 entries (design.py, make_text, Python 3.12, etc.)
│   ├── exec_shell_learnings.md     ← Shell execution gotchas
│   ├── video_production_learnings.md
│   ├── cross_agent_learnings.md    ← Inter-agent communication patterns
│   ├── cron_scheduling_learnings.md
│   ├── gateway_config_learnings.md
│   ├── macos_infra_learnings.md
│   ├── shared_learnings_meta.md
│   └── auto_extracted_learnings.md ← NEW. Written by proactive-learning plugin
~/.openclaw/
├── memory/                         ← Per-agent SQLite databases with Gemini embeddings
│   ├── main.sqlite                 ← MotusCTO embeddings (chunks table)
│   ├── youtube.sqlite              ← MarketingVideo embeddings
│   ├── writer.sqlite               ← MarketingWriter embeddings
│   ├── cpo.sqlite / coo.sqlite / podcast.sqlite
│   └── ...                         ← All contain pre-computed 768-dim Gemini vectors
└── openclaw.json                   ← memorySearch.extraPaths → ~/.clawdbot/shared_learnings/
```

### How It Works Today
1. Agents write structured markdown entries to `~/.openclaw/shared_learnings/` (each with Context, Surprise, Rule/Workaround, Citations, Created/Updated dates).
2. `openclaw memory index` scans those files and computes Gemini vector embeddings, stored in each agent's `*.sqlite` DB.
3. Agents call `memory_search("discord rate limits")` → returns semantically similar text chunks.

### Strengths
- **Zero setup:** Already natively built into OpenClaw.
- **Well-structured entries:** Each learning has metadata (Citations count, Created/Updated dates).
- **Handles unstructured data:** Debug transcripts, SOPs, and narrative guides are easily searchable.

### Weaknesses
- **No automatic injection:** Agents must *remember* to call `memory_search` before starting work.
- **Semantic noise at scale:** As entries grow past ~100, vector search returns increasingly irrelevant chunks.
- **Contradictions:** If an old entry says "limit is 50" and a new one says "limit is 100," both are returned.

---

## 5. Future System: The Knowledge Graph Layer

The KG does **not replace** `shared_learnings`. It lives **alongside** it as a precision layer for structured facts.

### Proposed Filesystem Layout
```
~/.openclaw/
├── shared_learnings/               ← UNCHANGED. Historical journals.
├── memory/                         ← UNCHANGED. Per-agent vector embeddings.
├── knowledge_graph/                ← NEW. Structured KG database.
│   └── kg.sqlite                   ← Single shared SQLite DB (nodes + edges tables)
└── skills/
    └── knowledge-graph/            ← NEW. The KG Skill.
        ├── SKILL.md                ← Instructions for agents on how/when to use KG tools.
        └── tools/
            ├── kg_query.sh         ← Query an entity's facts.
            ├── kg_add_node.sh      ← Add/update a structured fact.
            └── kg_add_edge.sh      ← Connect two entities with a relationship.
```

### How The Two Systems Coexist

#### Non-Overlapping Ownership
| System | Owns | Analogy |
| :--- | :--- | :--- |
| `shared_learnings/*.md` | **Historical Journals** — append-only logs of what happened | A lab notebook |
| `knowledge_graph/kg.sqlite` | **Current State of Truth** — the latest known fact | A reference manual |

#### Knowledge Flow Direction
Knowledge flows **one way:** Journals → KG. The markdown logs record *what happened*. The KG extracts and maintains *what is currently true*.
```
Agent encounters surprise
       │
       ▼
Writes raw narrative to shared_learnings/*.md
  ("Hit 429 error. Discovered limit is 100/min, not 50.")
       │
       ▼
agent_end Hook OR HEARTBEAT extracts the structured fact
       │
       ▼
Updates kg.sqlite: Node(Discord API).rate_limit = 100
  (overwrites old value deterministically)
```

#### Staleness Handling
- KG nodes carry `updated_at` timestamps. If a fact is older than 30 days, it's injected with a caveat: "⚠️ Last verified 45 days ago."
- Markdown files are **never deleted**. They serve as the evidence trail for why a KG fact exists.

### Writing: Two Channels, Different Purposes
| What the Agent Learned | Where It Goes | Why |
| :--- | :--- | :--- |
| A 500-word debugging transcript | `shared_learnings/*.md` | Unstructured, best for semantic search |
| "Discord API rate limit is 50/min" | `kg.sqlite` as a Node with properties | Structured fact, perfect for surgical injection |
| "render_video.py requires DISPLAY=:0" | `kg.sqlite` as Node→Edge→Node | Relational fact, queryable by tool name |

### Reading: Two Channels, Different Purposes
| Use Case | Which System | Why |
| :--- | :--- | :--- |
| Agent wants the full debugging story | `memory_search` (text embeddings) | Needs the narrative context |
| Hook needs to inject 3 key facts into a subagent prompt | `kg_query` (Knowledge Graph) | Needs surgical, few-token facts |
| Hook needs exact env vars before `run_python` | `kg_query` (Knowledge Graph) | Needs key-value pairs, not paragraphs |

---

## 6. Implementation Decision: Phased Rollout

### Phase 1 (Now): Hook Plugin with Gemini Embedding Search + `agent_end` Extraction
The `proactive-learning` plugin is installed at `/Users/jingshi/openclaw/extensions/proactive-learning/` and uses the same Gemini embedding infrastructure that `openclaw memory index` already provides. It delivers semantic search accuracy with no new infrastructure.

**What we built:**
- **Injection (`before_prompt_build`):** Intercepts subagent creation, calls the Gemini `embedContent` API once to vectorize the task prompt (~200ms), then performs cosine similarity search against all pre-indexed chunks in `~/.openclaw/memory/*.sqlite`. Top results (score ≥ 0.3) are prepended as `prependContext`.
- **Extraction (`agent_end`):** When a subagent completes, scans the full transcript for surprise patterns (error, workaround, rate limit, etc.) and appends extracted learnings to `auto_extracted_learnings.md` in the shared_learnings directory.
- Safety checks via `isSubagentSessionKey` to protect main agents.
- The Gemini API key is read from the existing `memorySearch.remote.apiKey` config — no extra configuration needed.

> **Important:** The query embedding MUST use the same model (`gemini-embedding-001`) as was used during indexing. Using a different model (e.g., local Ollama) would produce incompatible vector spaces.

### Phase 2 (Later): Knowledge Graph Precision Layer
When `shared_learnings` grows past ~100 entries and vector search starts returning noise or contradictions, we layer the KG on top:

**What we build:**
- `kg.sqlite` database with `nodes` and `edges` tables.
- `knowledge-graph` Skill with `kg_query`, `kg_add_node`, `kg_add_edge` tools.
- Update the Hook Plugin to query the KG instead of (or in addition to) `memory_search`.
- `agent_end` hook for automatic subagent transcript extraction.

---

## 7. Application / Impact
Implementing this architecture fundamentally changes OpenClaw agent behavior:
*   **Zero-Shot Competence:** Subagents require less trial-and-error because constraints are injected mechanically before they start.
*   **Token Efficiency:** Injecting targeted search results (and later, discrete KG properties) uses far fewer tokens than forcing agents to search manually.
*   **Institutional Memory:** The combination of `agent_end` extraction and `HEARTBEAT.md` enforcement guarantees that the swarm permanently learns from every "surprise."

---

## 8. Current Implementation: Scenario Walkthrough

The Phase 1 plugin (`proactive-learning`) is installed at `/Users/jingshi/openclaw/extensions/proactive-learning/` and enabled in `openclaw.json`. Here is exactly what happens at runtime.

### Scenario A: `before_prompt_build` — Injection

**When it fires:** Every turn, for every agent, right before the prompt is sent to the LLM.

```
User says: "Render the manim video for scene 3"
       │
       ▼
Main agent (MotusCTO) decides to spawn a subagent
       │
       ▼
sessions_spawn("youtube", "Render scene 3 of the manim animation...")
       │
       ▼
🔥 before_prompt_build FIRES for the new subagent
       │
       ▼
Plugin checks:
  1. Is this a subagent?        → ctx.sessionKey contains "subagent:" → YES ✅
  2. Is this the first turn?     → event.messages.length <= 1         → YES ✅
  3. Call Gemini embedContent API (~200ms):
     "Render scene 3 manim animation" → [0.12, -0.45, 0.78, ...] (768 dims)
  4. Cosine similarity search against ALL ~/.openclaw/memory/*.sqlite chunks:
       - youtube.sqlite: "design.py — Always Symlink"             (score: 0.72)
       - youtube.sqlite: "Always Use make_text()"                  (score: 0.58)
       - main.sqlite: "Python 3.14 Deadlocks with Cairo/Pango"    (score: 0.41)
     ↑ Note: "create animation" matches "manim rendering" because
       embeddings capture semantic similarity, not just keywords
  5. Return { prependContext: "<proactive-learnings>..." }
       │
       ▼
Subagent wakes up with these rules already in its system prompt.
It avoids design.py copy mistakes, uses make_text(), and uses Python 3.12.
```

**Safety guards:**
- `isSubagentSessionKey` — Skips main agents so long-running prompts aren't polluted.
- `event.messages.length > 1` — Only injects on first turn. Subsequent turns already have the learnings in context.

### Scenario B: `agent_end` — Extraction

**When it fires:** Once, when any agent session completes.

```
Subagent finishes rendering the manim video
       │
       ▼
🔥 agent_end FIRES with:
  event.messages = [full chat transcript]
  event.success = true
  event.durationMs = 45000
  ctx.agentId = "youtube"
  ctx.sessionKey = "agent:youtube:subagent:abc123"
       │
       ▼
Plugin checks:
  1. Is this a subagent?           → YES ✅
  2. Was the run successful?       → event.success === true → YES ✅
  3. Enough messages?              → 12 >= 4 minimum → YES ✅
  4. Extract all text into a transcript string
  5. Scan for surprise patterns:
     - /error|failed/   → found "error: Cairo deadlock"
     - /workaround|fix/ → found "fix: rebuilt venv with Python 3.12"
     → mightContainLearnings = TRUE ✅
  6. Append to auto_extracted_learnings.md:
       │
       ▼
New entry written:
  ### Auto-extracted from youtube subagent run
  - **Context:** Subagent youtube encountered this during a task.
  - **The Surprise:** error: Cairo deadlock when rendering with Python 3.14
  - **The Rule/Workaround:** fix: rebuilt venv with Python 3.12
  - **Citations:** 0
  - **Created Date:** 2026-02-23
```

**Safety guards:**
- `isSubagentSessionKey` — Main agents have long sessions where noise-to-signal is too high.
- `event.success` — Failed runs likely ended in error state, not a resolution.
- `minMessages: 4` — Trivially short conversations probably didn't encounter surprises.
- `SURPRISE_PATTERNS` — Only transcripts containing "error," "workaround," "rate limit," "deprecated," etc. are processed.

### The Closed Learning Loop

Together, the two hooks create a self-improving cycle:

```
Subagent runs → encounters surprise → agent_end extracts it
                                            │
                                            ▼
                               auto_extracted_learnings.md
                                            │
                          next openclaw memory index
                                            │
                                            ▼
                                  Vector embeddings updated
                                            │
                          next subagent spawned with related task
                                            │
                                            ▼
                        before_prompt_build injects the learning
                                            │
                                            ▼
                        Subagent avoids the same mistake ✅
```

---

## Appendix A: OpenClaw Plugin Hooks Reference
OpenClaw's Plugin API (`src/plugins/types.ts`) provides lifecycle interception points:

| Hook Name | Fires When | Can Modify | Primary Use Case |
| :--- | :--- | :--- | :--- |
| `before_prompt_build` | **Every turn**, before the prompt is sent to the LLM | `systemPrompt`, `prependContext` | Strategic Injection: prepending facts to subagent prompts |
| `before_agent_start` | **Once** when an agent session first boots | Initial messages, can block startup | History Manipulation: injecting initial system messages |
| `before_tool_call` | After LLM requests a tool, **before** execution | `params` object, can `block` the call | Operational Injection: mutating env vars, flags silently |
| `after_tool_call` | **After** a tool finishes executing | Read-only (observe result, duration) | Logging: tracking tool outcomes and errors |
| `agent_end` | When an agent session completes | Read-only (full message array) | Knowledge Extraction: mining transcripts for learnings |
| `subagent_spawning` | When parent requests a spawn, **before** child exists | Routing, model selection | Routing: altering the subagent's model or denying spawn |
| `subagent_ended` | When a subagent finishes | Read-only (outcome, reason) | Lifecycle tracking |
| `tool_result_persist` | Before a tool's output is saved to chat history | Can modify or truncate the message | Context Truncation: summarizing massive tool outputs |
| `llm_input` / `llm_output` | Raw LLM request/response payloads | Read-only | Token cost logging, observability |
| `before_compaction` | Before context window is truncated/summarized | Can read session file | History preservation before truncation |

### Key Distinction: `before_prompt_build` vs `before_agent_start` vs `subagent_spawning`
- **`subagent_spawning`**: Fires when the parent calls `sessions_spawn`. The child doesn't exist yet. Used for routing/model changes. Cannot inject prompt text.
- **`before_agent_start`**: Fires once when an agent session boots. Injects initial messages into the chat log. For main agents, this fires when they wake from heartbeat.
- **`before_prompt_build`**: Fires on **every turn** for **all agents** (main, subagent, cron). Modifies the actual system prompt text sent to the LLM. This is the most powerful hook for knowledge injection.

## Appendix B: Safety Checks
When writing Hook plugins that run globally, use OpenClaw `sessionKey` utilities to prevent modifying the wrong agent:
*   `isSubagentSessionKey(ctx.sessionKey)`: Ensures prompt injections only affect ephemeral subagents.
*   `isCronSessionKey(ctx.sessionKey)`: Identifies background heartbeat loops.
*   `ctx.agentId`: Allows per-agent rules (e.g., different injection logic for `youtube` vs `cpo`).

## Appendix C: Hooks vs Workflows Decision Framework
| Scenario | Use Hooks? | Use SOUL + Tools? | Why |
| :--- | :--- | :--- | :--- |
| Inject env vars before script execution | ✅ Yes | | System-level guardrail, LLM doesn't need to know |
| Inject KG facts into subagent prompts | ✅ Yes | | Mechanical enforcement, not agent discretion |
| Move file to `/approved/` on user approval | | ✅ Yes | Business logic — LLM needs to reason about conditions |
| Trigger writer agent after video approval | | ✅ Yes | Multi-step workflow — LLM orchestrates visibly |
| Enforce that workflows actually completed | | ✅ `HEARTBEAT.md` | Periodic verification via heartbeat checklist |

## Appendix D: Embedding Search Tradeoffs

The `before_prompt_build` hook uses Gemini embedding + SQLite vector search. Key tradeoffs:

| Dimension | Detail |
| :--- | :--- |
| **Latency** | ~200ms per subagent spawn (1 Gemini API call + local SQLite scan). Negligible vs the 3-5s an LLM turn takes. |
| **API Dependency** | Requires Gemini API availability. If the API is down, injection silently skips (fail-open). |
| **Model Lock-in** | Query vectors MUST use the same model as indexed documents (`gemini-embedding-001`). Switching models requires re-running `openclaw memory index`. |
| **Cross-Agent Search** | The plugin searches ALL agent SQLite databases, not just the spawning agent's. A youtube subagent can receive learnings originally indexed for the main agent. |
| **Re-indexing Gap** | Auto-extracted learnings written to `auto_extracted_learnings.md` are NOT immediately searchable. They require `openclaw memory index` to run before embeddings are available. The cron-indexed memory job handles this automatically. |
