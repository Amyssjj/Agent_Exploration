---
title: "ACP Thread-Bound Agents — How It Works"
date: 2026-02-27
topics: [acp-integration]
status: active
---

# ACP Thread-Bound Agents — How It Works

## What Is It?

ACP = **Agent Communication Protocol**. "Thread-bound agents" means you can spawn **external AI coding agents** (Claude Code, Codex, OpenCode, Gemini CLI, Pi) directly from a Discord thread, and they become **bound** to that thread — all messages in the thread route to that agent session, and all agent output streams back to the same thread.

Think of it as: **spawning a coding assistant inside a Discord thread, and it stays there as a persistent conversation partner**.

---

## How It Works (Architecture)

```
┌─────────────────────────────────────────────────────┐
│                   Discord Thread                     │
│  User types message → thread binding lookup          │
└─────────────┬───────────────────────────┬───────────┘
              │ inbound routing           │ output streaming
              ▼                           ▲
┌─────────────────────────────────────────────────────┐
│            OpenClaw Core (Control Plane)              │
│                                                       │
│  • AcpSessionManager — single writer/orchestrator     │
│  • Session identity, metadata, lifecycle states       │
│  • Thread binding ↔ ACP session mapping               │
│  • Dispatch pipeline (dispatch-acp.ts)                │
│  • Policy enforcement (allowed agents, concurrency)   │
└─────────────┬───────────────────────────┬───────────┘
              │ ACP transport             │ events
              ▼                           ▲
┌─────────────────────────────────────────────────────┐
│          ACP Runtime Backend (Pluggable)              │
│                                                       │
│  Currently: acpx plugin                               │
│  Handles: spawn, queueing, cancel, reconnect          │
│  Adapters: pi, claude, codex, opencode, gemini        │
└─────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **Core owns routing, plugin owns runtime** | Routing must be in core (thread bindings resolve before dispatch). Runtime transport is pluggable |
| **Session lifecycle states** | `creating` → `idle` → `running` → `cancelling` → `closed` / `error` |
| **Spawn + bind + enqueue are atomic** | Prevents orphaned sessions or unbound threads |
| **Streamed output is a projection** | Agent output goes through a projector/coalescer, not raw side-effects |
| **Fail-closed dispatch** | If binding exists but session is invalid → error, not silent fallback |

---

## User Flow (Discord)

1. **Spawn** an ACP agent into a thread:
   ```
   /acp spawn codex --mode session --thread auto --cwd /my/repo
   ```
   - Creates a new Discord thread
   - Starts an `acpx` session with the `codex` adapter
   - Binds the thread to that session

2. **Chat** in the thread — messages route to the ACP session automatically

3. **Control** the session with `/acp` commands:
   - `/acp status` — see session state, model, options
   - `/acp model anthropic/claude-opus-4-5` — change model
   - `/acp cwd /other/repo` — change working directory
   - `/acp cancel` — cancel in-flight turn
   - `/acp close` — close session and unbind thread

4. **Modes:**
   - `run` — one-shot: agent runs a task and session closes
   - `session` — persistent: thread stays bound, agent keeps context

---

## Config Required

```json5
// openclaw.json
{
  "acp": {
    "enabled": true,
    "dispatch": { "enabled": true },
    "backend": "acpx",
    "defaultAgent": "codex",
    "allowedAgents": ["pi", "claude", "codex", "opencode", "gemini"],
    "maxConcurrentSessions": 8,
    "stream": {
      "coalesceIdleMs": 300,
      "maxChunkChars": 1200
    },
    "runtime": {
      "ttlMinutes": 120
    }
  },
  // Discord-specific thread binding
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

Setup:
```bash
openclaw plugins install @openclaw/acpx
openclaw config set plugins.entries.acpx.enabled true
/acp doctor   # verify backend health
```

---

## Available `/acp` Commands

| Command | Purpose |
|---|---|
| `/acp spawn <agent>` | Create session, optionally bind to thread |
| `/acp cancel` | Cancel in-flight turn |
| `/acp steer` | Send steer instruction mid-run |
| `/acp close` | Close session + unbind thread |
| `/acp status` | Show state, model, options, session IDs |
| `/acp set-mode` | Change mode (e.g. `plan`) |
| `/acp model <id>` | Set model override |
| `/acp cwd <path>` | Set working directory |
| `/acp permissions` | Set approval policy |
| `/acp timeout <s>` | Set runtime timeout |
| `/acp sessions` | List recent ACP sessions |
| `/acp doctor` | Health check + actionable fixes |
| `/acp install` | Show install steps |

---

## Supported Harness Agents

| Agent ID | What it runs |
|---|---|
| `pi` | OpenClaw's own Pi agent |
| `claude` | Claude Code CLI |
| `codex` | OpenAI Codex CLI |
| `opencode` | OpenCode CLI |
| `gemini` | Gemini CLI |

---

## Relevance to Your Setup

This is a **big deal for multi-agent workflows**. Previously you were working with `sessions_send` and subagent communication (which had pairing issues). ACP thread-bound agents offer a **much cleaner path**:

- **Each agent gets its own Discord thread** — no message routing confusion
- **Proper lifecycle management** — spawn, cancel, close with explicit states
- **Streaming output** — agent responses stream live into the thread
- **Multiple concurrent sessions** — up to `maxConcurrentSessions` (default 8)
- **Model/cwd overrides per session** — each thread can target different repos/models

> [!TIP]
> This could replace the `sessions_send` approach you were debugging before. Instead of agents sending messages to each other through the gateway, you spawn dedicated ACP sessions bound to Discord threads, each running their own coding agent.



## Feb 27, ACP doesn't work investation:
Root Cause Analysis                                                                                                         
                                                                                                                              
  The Flow: /acp spawn claude                                                                                                 
                                                                                                                              
  1. spawnAcpDirect() (src/agents/acp-spawn.ts:220) creates a session key and calls acpManager.initializeSession()            
  2. That calls AcpxRuntime.ensureSession() (extensions/acpx/src/runtime.ts:146) which runs:                                  
  acpx --format json --json-strict --cwd <cwd> claude sessions ensure --name <key>                                            
  3. Inside acpx, sessions ensure spawns the Claude agent, runs ACP initialize, then newSession                               
  4. After session creation, prompts run through AcpxRuntime.runTurn() (extensions/acpx/src/runtime.ts:197):                  
  acpx ... --ttl 0.1 claude prompt --session <name> --file -                                                                  
                                                                                                                              
  What's breaking                                                                                                             
                                                                                                                              
  Claude adapter (@zed-industries/claude-agent-acp@0.19.2):                                                                   
  - ACP initialize works fine (I verified this — returns protocol version, capabilities, etc.)                                
  - newSession is flaky — sometimes succeeds, sometimes the agent crashes with "Query closed before response received" (ACP   
  error code -32603)
  - Even when sessions ARE created, every single session record in ~/.acpx/sessions/ shows lastAgentDisconnectReason:
  "connection_close" — the agent dies on prompt or load
  - zod IS installed (v4.3.6) — so that's not the issue. The underlying @anthropic-ai/claude-agent-sdk@0.2.62 has a
  reliability problem with ACP session lifecycle

  Gemini adapter (gemini CLI native):
  - Hangs on sessions ensure — the Gemini CLI likely doesn't fully implement ACP persistent session commands

  Codex adapter (npx @zed-industries/codex-acp):
  - Also hangs on sessions ensure

  Why exec (one-shot) works

  Looking at acpx's code (cli.js:5893), createSession() does: start() → createSession() → close() — all in one shot. The exec
  path creates a temporary session, sends one prompt, and exits without needing session persistence/reloading. The persistent
  session path (prompt --session <name>) requires loading a previously created session via a new agent process — and that's
  where claude-agent-acp crashes.

  OpenClaw's code is correct

  The OpenClaw ACP implementation (src/acp/, extensions/acpx/) is well-structured and correct — the bug is upstream in the
  adapter packages. The pinned acpx@0.1.13 properly calls sessions ensure and parses the JSON event stream, but the adapters
  it delegates to are failing.

  Recommendations

  1. File upstream issues:
    - @zed-industries/claude-agent-acp: persistent session crashes (connection_close on every load/prompt). Issue #357 you
  mentioned is already tracking this.
    - acpx: gemini native adapter hangs on sessions ensure
  2. Potential workaround: Could we use the exec (one-shot) code path instead of persistent sessions? In OpenClaw's
  AcpxRuntime, the ensureSession + runTurn pattern requires persistent sessions, but if you added a one-shot mode that wraps
  acpx <agent> exec, it would bypass the broken session lifecycle.
  3. Downgrade test: acpx@0.1.12 is available on npm — worth testing if it handles sessions ensure differently.
  4. Use coding-agent skill in the meantime as your investigation already suggested — it uses PTY-based execution which is
  reliable.
