# OpenClaw Session Architecture

*Created at: 2026-02-12*


## 1. What is `session_status`?

The `session_status` is a specific **tool** available to agents in OpenClaw.

### Purpose
*   **Self-Awareness**: Allows the agent to check its own operational state (current time/date, token usage, active model).
*   **User Information**: Helps answer user questions like "what model are you using?" or "how many tokens have I used?".
*   **Controls**: Can be used to set model overrides for the current session (e.g., switching from `claude-3-5-sonnet` to `gpt-4o` for a specific chat).

---

## 2. Core Concept: "Session"

In OpenClaw, a **Session** represents a persistent conversational context. It is the stateful "memory" of a specific interaction thread.

### Session Identity
Every session is uniquely identified by a **Session Key**.
*   **Format**: `agent:<agentId>:<scope>:<type>:<id>`
*   **Examples**:
    *   `agent:main:direct:user123` (DM with user123)
    *   `agent:coder:channel:general` (Group chat in #general)
    *   `agent:main:thread:t123` (Threaded conversation)

---

## 3. Real-World Scenarios

Here is how sessions work in practice through common user interactions.

### Scenario A: Chatting Across Days (Continuity)
**User**: Validates continuity over time.
1.  **Day 1 (10:00 AM)**: You DM the Main Agent: "Hi, I'm working on Project X."
    *   **System Action**: Creates/Loads session `agent:main:direct:user123`.
    *   **State**: `updatedAt` is set to now. Context includes "Project X".
2.  **Day 2 (2:00 PM)**: You DM again: "What was I working on?"
    *   **System Action**: Loads the *same* session `agent:main:direct:user123`.
    *   **Agent**: Sees history from Day 1.
    *   **Tool Usage**: Agent might call `session_status` to check the current time (it's now Day 2) if relevant to the answer.
    *   **Result**: "You mentioned you were working on Project X yesterday."

### Scenario B: Switching Agents (Separation of Concerns)
**User**: Chats with different specialized agents.
1.  **User**: DMs the **Main Agent**: "Plan my week."
    *   **Session**: `agent:main:direct:user123` is active.
    *   **Context**: Personal planning.
2.  **User**: DMs the **Coder Agent**: "Fix this Python script."
    *   **Session**: `agent:coder:direct:user123` is created/loaded.
    *   **Key Difference**: This is a *completely separate* session file and memory context.
    *   **Isolation**: The Coder Agent does *not* know about your weekly plan from the Main Agent (unless explicitly shared).
    *   **Result**: You have two parallel, independent conversation threads with different "personalities."

### Scenario C: Switching Models (Session Override)
**User**: Needs a smarter model for a specific tough problem.
1.  **User**: "Write a quick email." (Default model: `claude-3-5-sonnet`)
    *   **Session**: using default config.
2.  **User**: "This next output needs to be perfect. Use Opus."
    *   **Agent**: Calls `session_status(model="claude-3-opus")`.
    *   **System Action**: Updates `modelOverride` in `session:main:direct:user123`.
    *   **Result**: All subsequent messages *in this specific DM* will use Opus.
    *   **Context**: The conversation history is **preserved**. The agent remembers everything said previously (while using Sonnet). The session is *not* reset; only the "brain" processing the new messages changes.
3.  **User**: Switches to a different channel or thread.
    *   **New Session**: This new session does *not* have the override; it uses the default `sonnet`.
    *   **Result**: The "Opus mode" is sticky only to the specific conversation where you requested it.

### Scenario D: Threaded Conversations (Granularity)
**User**: Starts a thread in Discord/Slack.
1.  **User**: Posts in `#general`: "Anyone know React?"
    *   **Session**: `agent:main:channel:general` (Group context).
2.  **User**: Replies in a **Thread** to that message: "Specifically hooks."
    *   **System Action**: Creates a *new* session `agent:main:thread:thread-id-123`.
    *   **Inheritance**: It might pull initial context from the parent, but it becomes its own history.
    *   **Result**: You can have a detailed technical discussion in a thread without polluting the main channel's memory.
    *   **Mechanism**: The Gateway appends `:thread:<threadId>` to the original Session Key.
        *   Main Channel Key: `agent:main:channel:general` -> Loads Session File A
        *   Thread Key: `agent:main:channel:general:thread:123` -> Loads Session File B
        *   Since they point to different files (or `SessionEntry` objects), messages sent in the thread are saved *only* to Session B. The main channel's context limit and history remain untouched.
