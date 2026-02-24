

*Created at: 2026-02-13*

# OpenClaw Agent Structure & Workflow Implementation

This document consolidates findings on the internal structure of OpenClaw agents, their essential files, and how to implement custom workflows like "Project Approval".

## 1. Agent Essentials (The "Soul" of the Agent)

An agent's identity and behavior are defined by a specific set of files in its workspace (`~/.openclaw/workspace` or `~/.openclaw/workspace-<profile>`). The system **automatically loads** these files if they exist.

| File | Purpose |
| :--- | :--- |
| **`AGENTS.md`** | Core documentation, rules, and repository guidelines. |
| **`SOUL.md`** | The persona, tone, and high-level behavioral instructions. |
| **`TOOLS.md`** | User-defined notes on how to use specific tools/skills. |
| **`IDENTITY.md`** | Key-value pairs for identity (Name, Emoji, Theme, Vibe). |
| **`USER.md`** | Context about *you* (the user) to help the agent serve you better. |
| **`MEMORY.md`** | Long-term memory storage (updated dynamically by the agent). |
| **`BOOTSTRAP.md`**| Initial context loaded at the start of a session. |

### Dynamic vs. Static Behavior
*   **Static**: The system *always* looks for the files above. It does not "discover" new system files arbitrarily.
*   **Dynamic Content**: The *content* of `MEMORY.md` changes.
*   **No "Magic" Folders**: The system **does NOT** automatically create folders like `projects/`, `approved/`, or `workflows/` based on conversation context. These are purely user-convention.

---

## 2. Implementing Workflows (e.g., Project Approval)

To enforce a specific workflow (like "Create Project -> Review -> Approve -> Move Folder"), you must explicitly instruct the agent.

### The "Instruction" Strategy (Recommended)
Add a rule to **`AGENTS.md`**. This is the flexible capabilities of the LLM to follow standard operating procedures.

**Example Rule (Added to `AGENTS.md`):**
```markdown
## Project Workflow
1.  **Initialization**: For every new task, create a new folder `projects/<task-name>/`.
2.  **Drafting**: Do all work inside `projects/<task-name>/`.
3.  **Review**: Ask the user to review the files.
4.  **Approval**: ONLY upon explicit user approval, move the folder to `approved/<task-name>/`.
```

### The "Skill" Strategy (Advanced)
For strict enforcement, create a custom Skill (`skills/workflow/SKILL.md`) that defines rigid tools.
*   `tool: project.start(name)` -> Creates folder
*   `tool: project.approve(name)` -> Moves folder
*   *Pros*: Guaranteed behavior. *Cons*: Requires writing TypeScript/Python code for the skill.

## 3. Key Code References
*   `src/agents/workspace.ts`: Logic for `ensureAgentWorkspace` and loading bootstrap files.
*   `src/agents/pi-embedded-helpers/bootstrap.ts`: Logic for trimming and injecting these files into the context window.
