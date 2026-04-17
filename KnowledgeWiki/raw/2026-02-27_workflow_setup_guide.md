---
title: "OpenClaw Multi-Agent Setup Guide"
date: 2026-02-27
topics: [agent-collaboration]
status: active
---

# OpenClaw Multi-Agent Setup Guide

Here is your step-by-step guide to migrating your multi-agent architecture from ❌ `sessions_send` mapping to the robust ✅ `sessions_spawn` + ACP setup.

---

## Part 1: Setting up `sessions_spawn` for Async Delegation

To get your OpenClaw agents (COO, YouTube, Writer) collaborating asynchronously via `sessions_spawn`, you need to configure their parent-child permissions in `openclaw.json`.

### Step 1: Update `openclaw.json` Agent Permissions

An agent can only spawn another agent if it is explicitly allowed in `subagents.allowAgents`.

Edit your `openclaw.json`:

```json5
{
  "agents": {
    "list": [
      {
        "id": "coo",
        "name": "COO Agent",
        "subagents": {
          // The COO agent orchestrates, so it can spawn anyone
          "allowAgents": ["youtube", "writer", "agent-4", "agent-5"]
        }
      },
      {
        "id": "youtube",
        "name": "YouTube Agent",
        "subagents": {
          // YouTube can handoff to Writer
          "allowAgents": ["writer"]
        }
      },
      {
        "id": "writer",
        "name": "Writer Agent"
        // No allowAgents list = cannot spawn other agents
      }
    ]
  }
}
```

### Step 2: Instruct Your Agents (System Prompt / SOUL)

Update your agents' `SOUL.md` or `SYSTEM.md` files so they know *how* and *when* to use `sessions_spawn` instead of formatting messages for Discord.

**Example for the YouTube Agent:**
```markdown
When you have finished generating the raw video script, do NOT output it to the user.
Instead, save the script to the workspace (e.g. `workspace/handoff/script.md`), and use your `sessions_spawn` tool to delegate the blog post creation to the `writer` agent.

Use exactly this format when calling the tool:
- task: "I have saved the new script to workspace/handoff/script.md. Please read it and write a blog post."
- agentId: "writer"
```

### Step 3: Check How the Handoff Works

1. You tell **YouTube agent** to make a video.
2. It does its work and calls `sessions_spawn(agentId="writer")`.
3. OpenClaw spins up the **Writer agent** in the background (no manual chat trigger needed).
4. Writer does the work.
5. The result is automatically announced back directly to the channel where you made the original request.

---

## Part 2: Setting up ACP Thread-Bound Agents

> [!WARNING]
> Because you are currently 1,060 commits behind `origin/main` (HEAD: `b81bce703`), you **must** pull the latest code first, as the ACP features were merged in PR #23580 over the last few days.

### Step 1: Update your Local OpenClaw Repository

```bash
cd /Volumes/Motus_SSD/mac_mini/ClawdBot_Github/openclaw
git pull origin main
```

### Step 2: Enable ACP in `openclaw.json`

Add the core ACP configuration and enable thread bindings on your Discord channel config:

```json5
{
  // 1. Core ACP configuration
  "acp": {
    "enabled": true,
    "dispatch": { "enabled": true },
    "backend": "acpx",
    // Allowed external harness agents:
    "allowedAgents": ["pi", "claude", "codex", "opencode", "gemini"],
    "maxConcurrentSessions": 8
  },
  
  // 2. Discord Thread Binding config
  "channels": {
    "discord": {
      "threadBindings": {
        "enabled": true,
        "spawnAcpSessions": true
      }
    }
  }
}
```

### Step 3: Install the ACP Runtime Plugin (`acpx`)

ACP agents run in an external backend process managed by the `acpx` plugin.

1. Navigate to your `openclaw` directory
2. Run the plugin installation:
   ```bash
   openclaw plugins install @openclaw/acpx
   ```
3. Enable the plugin in your config:
   ```bash
   openclaw config set plugins.entries.acpx.enabled true
   ```

### Step 4: Verify the Setup

1. Restart your OpenClaw gateway connection.
2. Go into your Discord server and type this check command:
   ```text
   /acp doctor
   ```
   *This will tell you if the `acpx` backend is healthy and ready to receive spawn requests.*

### Step 5: Start using ACP Agents!

Go to any Discord channel your Motus bot has access to, and type:
```text
/acp spawn claude --thread auto
```
OpenClaw will immediately create a new Thread, start a persistent Claude Code session, and link them together. Talk in that thread to code with Claude!
