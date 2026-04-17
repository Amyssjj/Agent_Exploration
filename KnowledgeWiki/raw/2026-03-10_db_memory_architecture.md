---
title: "OpenClaw DB Memory Plugin Architecture"
date: 2026-03-10
topics: [shared-knowledge]
status: active
---

# OpenClaw DB Memory Plugin Architecture

## Problem
OpenClaw's native memory system relies heavily on the local filesystem (saving Markdown files) combined with background SQLite vector indexing. This architecture creates several bottlenecks for advanced, multi-agent frameworks at scale:
*   **Latency & Synchronization:** Markdown files require a background cron job to compute embeddings and update SQLite, meaning memories are not instantly available to other agents.
*   **Lack of Relational Metadata:** Filesystem storage makes it difficult to execute complex queries like filtering memories by specific agents, projects, or dynamic tags.
*   **Context Misses (Recall):** Agents must proactively remember to use the `memory_search` tool to look up information. If an agent forgets to search, it hallucinates or fails, reducing overall execution precision.

## Insights
A sophisticated memory system shouldn't just be an archive; it should be a real-time, relational knowledge graph that proactively assists agents.
1.  **Relational + Vector is Superior:** By moving to a centralized relational database (like PostgreSQL with the `pgvector` extension), we can store rich metadata (agent IDs, timestamps, session links) in the exact same row as the vector embedding. This enables "Hybrid Search" (e.g., "Find semantically similar text, but ONLY if the author was the @SecurityAgent").
2.  **Instant Consistency:** Writing directly to a database via an API bypassing the filesystem means the moment one agent learns a fact, the embedding is calculated, and it is instantly queryable by every other agent globally.
3.  **Proactive Recall is Better than Reactive Search:** Instead of waiting for the agent to call `memory_search`, the system should intercept the user's prompt, perform a fast vector search under the hood, and inject highly relevant context directly into the agent's system prompt before it even starts thinking.

## Method
To achieve this, we will build a custom OpenClaw Plugin that replaces the native filesystem tools with Database tools and leverages pre-execution hooks.

### 1. Database Schema
Initialize a PostgreSQL database with `pgvector`:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE agent_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(1536) -- For OpenAI text-embedding-3-small
);

-- Index for fast hybrid search
CREATE INDEX ON agent_memories USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON agent_memories (agent_id);
```

### 2. Custom Extraction Methods (Writing to DB)
Instead of relying on the native `HEARTBEAT.md` chron job to write Markdown files to the filesystem, we can use three different methods to extract and save memory to Postgres depending on the desired level of autonomy.

#### Option A: Invisible Background Extraction (`agent_end` Hook)
*   **How it Works:** The `agent_end` hook fires every time an agent finishes a task or conversation turn. The plugin intercepts the `messages` array (the conversation history), passes it to a fast, cheap LLM (e.g., GPT-4o-mini), and asks it to extract permanent facts. If found, the plugin writes them to Postgres.
*   **Handling Long Conversations:** OpenClaw employs a Compaction system (`before_compaction` and `after_compaction` hooks) to truncate history when token limits are reached. The `agent_end` hook receives the *current window* of messages. For exceptionally long, multi-day sessions, we rely on the continuous `agent_end` evaluations happening sequentially, ensuring facts are extracted *before* they fall out of the context window.
*   **Pros:** Requires zero prompt engineering. The primary agent never "forgets" to save memory because it happens magically in the background.

#### Option B: Targeted Interception (`after_tool_call` Hook)
*   **How it Works:** The plugin listens for specific tool executions (like `exec` or `github_commit`). When the tool completes successfully, the hook automatically extracts the result and writes it as a memory.
*   **Pros:** Highly deterministc logging for critical actions without extra LLM extraction overhead.

#### Option C: The Mechanical Way (`db_memory_save` Tool)
*   **How it Works:** The plugin registers a new `db_memory_save` tool. The agent's system prompt (or `HEARTBEAT.md` cron job) instructs the agent to intentionally call this tool when it learns something new. 
*   **Pros:** Exact parity with how OpenClaw native memory works today, but backed by Postgres. 

### 3. Explicit Retrieval Tool
*   **`db_memory_search`:** Allows the agent to explicitly query the DB. It embeds the search query, runs a `<->` similarity search in Postgres, filters by metadata if requested, and returns the top `N` text chunks.

### 3. Proactive Injection (`before_prompt_build`)
We will implement an OpenClaw `before_prompt_build` hook to intercept task execution:
1.  When a user sends a message, the hook extracts the current topic/task.
2.  It silently calls the equivalent of `db_memory_search` against the Postgres database.
3.  It applies a strict confidence threshold (e.g., `similarity > 0.85`).
4.  If a match is found, it injects a `[SYSTEM: PROACTIVE MEMORY RECALL]` block containing the retrieved facts directly into the agent's system prompt.

## Result
By implementing this architecture, the multi-agent system achieves:
*   **Higher Precision & Recall:** The `before_prompt_build` hook guarantees the agent has relevant historical context without relying on the LLM to choose to use a search tool.
*   **Real-time Global Sync:** Eliminates the background indexer delay; memories are immediately shared across the global pool.
*   **Advanced Filtering:** Unlocks SQL-based hybrid search, allowing the Memory Controller to enforce privacy boundaries or filter noise based on relational metadata (e.g., hiding financial agent memories from public web agents).
