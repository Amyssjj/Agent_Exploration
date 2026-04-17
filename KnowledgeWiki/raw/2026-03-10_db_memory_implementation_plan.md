---
title: "OpenClaw DB Memory Plugin Architecture"
date: 2026-03-10
topics: [shared-knowledge]
status: active
---

# OpenClaw DB Memory Plugin Architecture

This architecture design replaces OpenClaw's native filesystem-based memory with a robust, relational PostgreSQL vector database. We will also implement a proactive RAG injection system using the `before_prompt_build` hook to automatically supply the agent with relevant context *before* it even has to ask for it.

## 1. Database Schema (PostgreSQL + pgvector)

Using a relational database allows us to store rich metadata alongside the vector embeddings. This unlocks hybrid search (semantic + exact match filtering).

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE agent_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    topic VARCHAR(255),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(1536) -- Assuming OpenAI text-embedding-3-small
);

-- Index for fast vector similarity search
CREATE INDEX ON agent_memories USING hnsw (embedding vector_cosine_ops);
-- Index for fast metadata filtering
CREATE INDEX ON agent_memories (agent_id, topic);
```

## 2. Core Plugin Tools

We will create two custom OpenClaw tools to interface with this database.

### 1. `db_memory_save` (Explicit Extraction Tool)
*   **Purpose:** Allows the agent to explicitly save a permanent fact or lesson to the database during its `HEARTBEAT.md` reflection cycle.
*   **Implementation:**
    1.  Receives the `content` and optional `topic` from the agent.
    2.  Calls an embedding API (e.g., OpenAI, Gemini) to generate the `VECTOR(1536)` for the `content`.
    3.  Executes an `INSERT INTO agent_memories` SQL query with the agent's ID, session ID, content, and the generated vector.

### 2. `agent_end` Hook (Background Extraction)
*   **Purpose:** To automagically extract memory without the agent doing it explicitly.
*   **Implementation:**
    1. Hook into `agent_end`.
    2. Parse the `messages` array from the successful turn. 
    3. Pass the diff/new messages to a fast LLM (like `gpt-4o-mini`) to ask if there are new facts.
    4. If there are, run the embedding API and `INSERT INTO agent_memories`.

### 3. `after_tool_call` Hook (Targeted Interception)
*   **Purpose:** To deterministically save important outputs (e.g., successful bash scripts).
*   **Implementation:**
    1. Hook into `after_tool_call`.
    2. Check if `toolName` is `exec` or `github_commit`.
    3. Construct a memory payload and `INSERT INTO agent_memories`.

### `db_memory_search` (Explicit Retrieval)
*   **Purpose:** Allows the agent to actively query the database if it needs specific information during a task.
*   **Implementation:**
    1.  Receives a `query` string and optional metadata filters (e.g., `topic`).
    2.  Embeds the `query` into a vector.
    3.  Executes a vector similarity search (e.g., `<->` operator in `pgvector`), filtering by `agent_id` or `topic`.
    4.  Returns the top `N` text chunks directly to the agent's context.

## 3. Proactive RAG Injection (`before_prompt_build` hook)

To improve precision and recall, we don't want to rely solely on the agent remembering to call `db_memory_search`. We can proactively inject relevant context into the system prompt *before* the LLM executes a turn.

This is exactly where the `before_prompt_build` hook shines.

### Workflow
When the agent receives a new user message or task in a session:
1.  **Hook Triggered:** The `before_prompt_build` hook fires passing the `current_user_message` (or the last few messages in the session buffer).
2.  **Pre-check Search:** The plugin intercepts this and silently calls the equivalent of `db_memory_search` under the hood. It embeds the `current_user_message` and queries the PostgreSQL database for the top 3 most relevant `agent_memories`.
3.  **Similarity Threshold:** We apply a strict cosine similarity threshold (e.g., `similarity > 0.85`). If nothing is highly relevant, we inject nothing (saving tokens and avoiding hallucination).
4.  **Prompt Injection:** If highly relevant memories are found, the hook appends them dynamically to the agent's system prompt or as a hidden "System Note" just before the user's message.

*Example Injected Prompt Context:*
```text
[SYSTEM: PROACTIVE MEMORY RECALL]
Based on the current task, here is relevant context from your past sessions:
- On 2026-03-01: "The authentication API requires a Bearer token with the 'v2-' prefix."
- On 2026-03-05: "Deployments to staging must be approved by the @sec-ops team."
```

## 4. The Complete Loop using this Plugin

1.  **Task Start:** User asks the agent to build a new feature.
2.  **Proactive Recall (Hook):** `before_prompt_build` searches the DB, finds a relevant architecture decision from last week, and injects it into the prompt. The agent executes the task flawlessly because it already has the context.
3.  **Task Execution:** The agent works. If it hits a specific snag not covered by the proactive recall, it manually calls the `db_memory_search` tool.
4.  **Task Completion:** The agent finishes.
5.  **Reflection (Cron):** The `every 30m` cron job wakes the agent up. The agent reviews its logs, realizes it solved a novel bug, and calls `db_memory_save` to write the solution.
6.  **Indexing:** The embedding is calculated and inserted into PostgreSQL *instantly*. No background syncing required.
