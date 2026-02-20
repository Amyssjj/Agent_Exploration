# OpenClaw System Prompt Optimization Analysis

## The "Why": Anatomy of a Token Guzzler

You are correct: OpenClaw reconstructs the **entire system prompt** for every single turn. This is stateless by design but expensive.

### 1. What gets sent every time?
Based on `src/agents/system-prompt.ts` and `bootstrap-files.ts`, the following are injected **on every request**:

1.  **Identity & Safety**: Hardcoded instructions (~500 tokens).
2.  **Tool Definitions**: All available tools + their schemas.
    *   *Impact*: If you have 20+ tools, this is huge (2k-4k tokens).
3.  **Skills**: The entire content of `SKILL.md` for *every* loaded skill is often summarized or fully injected if "active".
    *   *Default*: It lists *all* available skills so the agent knows what it *can* do.
4.  **Project Context (The Big One)**:
    *   `AGENTS.md`: Defines the team roster.
    *   `SOUL.md`: Persona and style guide.
    *   `TOOLS.md`: User-facing tool guide.
    *   `MEMORY.md`: The "active" memory file.
    *   `BOOTSTRAP.md`: Initial project instructions.

### 2. The Multiplier Effect
In a 10-turn conversation:
*   Turn 1: System Prompt (10k) + User (100) = 10,100 tokens.
*   Turn 10: System Prompt (10k) + History (5k) + User (100) = 15,100 tokens.
*   **Total Burn**: You paid for that 10k system prompt 10 times (100k tokens total), even though it never changed.

---

## Optimization Strategy

To save tokens, we must move information from **"Hot Context"** (System Prompt) to **"Cold Storage"** (Retrieval/Files).

### Strategy A: Prune "Hot" Context Files
These files are read from disk and dumped into the prompt every time.

| File | Keep or Kill? | Action |
| :--- | :--- | :--- |
| `SOUL.md` | **Keep (Trim)** | Essential for personality, but keep it short (<200 tokens). Don't put huge backstories here. |
| `AGENTS.md` | **Kill** | If you don't use multi-agent routing often, move this list to `MEMORY.md`. The agent can "lookup" who to call. |
| `TOOLS.md` | **Kill** | The agent already sees tool schemas. `TOOLS.md` is often redundant user documentation. Delete it or move to `docs/`. |
| `BOOTSTRAP.md` | **Kill** | Once the project is running, delete this. It's for setup only. |
| `MEMORY.md` | **Keep (Curate)** | This is your "RAM". Keep it for *current* active tasks only. Move completed tasks to `archive/`. |

### Strategy B: "Cold" Memory (Retrieval)
Instead of putting *everything* in `MEMORY.md` (which is always loaded), create a `memory/` folder.

1.  **Create**: `workspace/memory/archive_2024.md`, `workspace/memory/architecture_decisions.md`.
2.  **Usage**: The agent has `find` and `grep` tools.
    *   *Bad*: "Here is the entire history of the project in the system prompt."
    *   *Good*: "I need to know about the database migration. I will `grep` 'migration' in `memory/`."
3.  **Result**: You pay 0 tokens for this info until the agent specifically asks for it.

### Strategy C: Skill Management
Every enabled skill adds to the prompt overhead (name + description at minimum).

1.  **Disable Unused Skills**: If you aren't doing "Graphviz" diagrams, delete/move that skill folder.
2.  **Granularity**: Don't make one giant "Utils" skill. Break it up so you can load only what's needed for a specific agent.

### Summary Checklist for Savings
1.  [ ] Delete `TOOLS.md`.
2.  [ ] Rename `AGENTS.md` to `AGENTS.inactive` (if you mostly solo).
3.  [ ] Trim `SOUL.md` to 3-5 bullet points.
4.  [ ] Move old `MEMORY.md` items to `memory/archive.md`.
