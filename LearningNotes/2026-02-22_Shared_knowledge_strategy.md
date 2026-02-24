# Shared Knowledge Strategy (Built-in Memory)

*Created at: 2026-02-22*


This guide outlines exactly how to set up the "Surprise Driven Learning" database so that all agents in the OpenClaw architecture can natively read, search, and contribute to a global pool of knowledge.

## The Problem & Key Insights

### The Problems
*   **Repetitive Mistakes:** Agents operating independently often run into the same undocumented API limitations (e.g., Discord Error 1008, Gateway lock timeouts) and burn tokens/time re-learning them.
*   **Context Bloat:** Maintaining a single, massive `SHARED_LEARNINGS.md` file that agents read on every turn destroys token efficiency and slows down generation times.
*   **Non-Deterministic Enforcement:** "Just telling" an agent to read shared learnings before starting work fails during long, multi-step tasks where the context window drifts. Agents simply get distracted and forget to log "surprises".
*   **Workspace Sandboxing:** OpenClaw's architecture correctly blocks symlink path traversals. You cannot simply symlink a global `~/.openclaw/shared_learnings` directory into an agent's local `./workspace/` to trick the memory system.

### The Insights
*   **`extraPaths` Configuration:** The Built-in memory backend (SQLite vector search) supports secure external directory mounting via the `memorySearch.extraPaths` array in `openclaw.json`. This bypasses symlink restrictions completely and safely natively indexes a global folder for all agents.
*   **Semantic Deduplication via Agent Logic:** OpenClaw doesn't magically deduplicate files. However, by forcing the agent to use `memory_search` *before* writing, the LLM itself acts as the semantic deduplicator—updating existing entries with a "Citations" counter instead of creating duplicates.
*   **The Power of the Heartbeat:** The most deterministic way to enforce learning is via `HEARTBEAT.md`, which wakes the agent up every 30 minutes on a cron schedule to explicitly review its local logs and write down new lessons it may have forgotten.

## The Semantic Lifecycle (How it Works)

### Flow 1: Reading an Existing Learning
1. **Trigger:** User asks an agent to perform a complex task (e.g., posting to Discord).
2. **Query:** The agent uses its `memory_search("discord limitations")` tool.
3. **Vector Search:** OpenClaw calculates the vector embedding for the query and finds the most mathematically similar snippet from the `extraPaths` folder.
4. **Action:** The agent reads the returned snippet and adjusts its plan. Token usage is minimized to just the search query and the 2-line snippet.

### Flow 2: Discovering & Deduplicating a New Learning
1. **Trigger:** The agent encounters an unexpected error or heuristic during a task.
2. **Deduplication Check:** The agent calls `memory_search("specific error details")` first.
3. **Logical Decision (The Agent's Brain):** 
   - *If found:* The agent opens the existing file and increments the **Citations** counter.
   - *If NOT found:* The agent appends a new entry using the mandated template.
4. **Background Embedding:** Once the markdown file is saved, OpenClaw's built-in file watcher detects the change and automatically calculates the new vector embeddings silently in the background. It is instantly ready for the next agent's semantic search.

---

## Step 1: Create the External Shared Directory
First, you need a single, centralized directory where all the shared learnings will live. It should be outside any individual agent's private directory. 

A good logical place is inside the global `.openclaw` directory, next to `agents`:

```bash
mkdir -p ~/.openclaw/shared_learnings
```

*Inside this folder, you will eventually have categorized Markdown files like `discord_learnings.md`, `python_learnings.md`, etc.*

## Step 2: Update `openclaw.json` (The Key!)
Because OpenClaw explicitly blocks workspace symlinks for security, we must tell the Built-in memory backend to natively scan our new global folder.

Open your `openclaw.json` config file and add the absolute path to your shared folder inside the `memorySearch.extraPaths` array:

```json5
"memorySearch": {
  "enabled": true,
  "provider": "local",  // or openai/gemini
  "fallback": "local",
  "extraPaths": [
    "/Users/jingshi/.openclaw/shared_learnings"
  ]
},
```
*Note: Make sure to use the absolute path (e.g., `/Users/jingshi/`), rather than the `~` shortcut.*

## Step 3: Update `SOUL.md` Guidelines
The agents need strict instructions on *how* and *when* to use this database. Because we want to avoid reading the full text of multiple active files and blowing up the context window, we force the use of `memory_search` and specify the absolute path for writes.

Add this exact section to the **`SOUL.md`** file of every agent (or your global shared SOUL template):

```markdown
## Shared "Surprise" Learning Protocol
You are connected to a hive-mind database of shared agent learnings located at `~/.openclaw/shared_learnings/`.

**1. Pre-Flight Check (Read):**
Before you write scripts, use complex tools, or interact with external APIs (like YouTube or Discord), you MUST use your `memory_search` tool to query for known limitations or "surprises" related to that task. 
- *Example Query:* "discord rate limits" or "sessions_send timeout".
- NEVER read the full text of the learnings files directly. Always use `memory_search`.

**2. Post-Action Reflection (Write):**
If you encounter an unexpected error, a tool failure, or discover a heuristic that differs from standard documentation (a "surprise"):
- You MUST append it to the appropriate file in the global directory: `~/.openclaw/shared_learnings/` (e.g., `discord_learnings.md`).
- **Required Format:** Use this exact template when appending to the file:
  ```markdown
  ### [YYYY-MM-DD]: [Brief Title of the Surprise]
  - **Context:** What you were attempting to do.
  - **The Surprise:** The unexpected error, timeout, or undocumented behavior.
  - **The Rule/Workaround:** How this should be handled by agents in the future.
  - **Citations:** 1 (Increment this number if you encounter this exact issue again)
  ```
- If the surprise is already documented, update the existing entry with new context or increase the tally.
- If it doesn't fit in an existing category file, safely create a new markdown file for it.
```

## Step 4: The Enforcement Loop (HEARTBEAT.md)
Even with strict `SOUL.md` guidance, agents get distracted during long tasks. To guarantee that lessons are actually logged, you must use the heartbeat system to trigger a mandatory reflection cycle.

Add this checklist item to the **`HEARTBEAT.md`** file of each agent:

```markdown
- [ ] Review the last 30 minutes of logs. Did any tool fail? Did you discover any unexpected behavior or "surprises"? If yes, append it to the relevant file in `~/.openclaw/shared_learnings/` immediately.
```
