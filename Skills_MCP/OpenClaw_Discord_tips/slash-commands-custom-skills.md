# Enabling /Slash Commands for Custom Skills — OpenClaw Tutorial

How to make your custom skills appear as native Discord (or Telegram) slash commands.

## How It Works

OpenClaw automatically registers slash commands for skills that declare themselves as `user-invocable`. When a user types `/skillname` in Discord, OpenClaw routes it to the agent and triggers the skill.

```
User types /feedback → Discord sends to OpenClaw Gateway
  → Gateway identifies it as a skill command
  → Routes to agent session with skill context
  → Agent executes the skill logic
  → Reply sent back to Discord
```

## Step 1: Write the Skill with the Right Frontmatter

The skill's `SKILL.md` needs two frontmatter fields:

```yaml
---
name: feedback
description: Submit feedback on any agent or system component.
user-invocable: true
command-dispatch: agent
---
```

```
┌──────────────────────────────────────────────────────────────┐
│ Field            │ Value    │ What it does                   │
├──────────────────────────────────────────────────────────────┤
│ user-invocable   │ true     │ Registers as a slash command   │
│ command-dispatch │ agent    │ Routes to LLM for processing   │
│ command-dispatch │ tool     │ Routes directly to a tool      │
│                  │          │ (deterministic, no LLM)        │
└──────────────────────────────────────────────────────────────┘
```

### `command-dispatch: agent` (recommended for most skills)

The command text is forwarded to the agent as a normal message. The agent reads the skill, processes the input, and responds. This is what `/feedback` uses — the agent parses the arguments, validates, stores in DB, and confirms.

### `command-dispatch: tool`

The command routes directly to a specific tool without going through the LLM. Use for deterministic operations like `/prose` (OpenProse plugin).

## Step 2: Place the Skill

Skills can live in three locations:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Location                          │ Scope                           │
├──────────────────────────────────────────────────────────────────────┤
│ ~/.openclaw/skills/<name>/        │ Global — all agents see it      │
│ <workspace>/skills/<name>/        │ Agent-specific — one agent only │
│ ~/.agents/skills/<name>/          │ User-level skills               │
└──────────────────────────────────────────────────────────────────────┘
```

Example directory structure:

```
~/.openclaw/skills/feedback/
  SKILL.md          # Frontmatter + instructions
```

## Step 3: Enable Native Commands in Config

Native slash command registration is controlled by `commands.nativeSkills`:

```json5
{
  commands: {
    native: "auto",        // Register built-in commands (default: auto)
    nativeSkills: "auto"   // Register skill commands (default: auto)
  }
}
```

- `"auto"` — On for Discord/Telegram, off for Slack
- `true` — Always register
- `false` — Never register (text `/skillname` still works)

Per-channel override:

```json5
{
  channels: {
    discord: {
      commands: {
        native: true,
        nativeSkills: true
      }
    }
  }
}
```

## Step 4: Restart Gateway

After adding or modifying a skill, restart the gateway so it discovers and registers the new command:

```bash
openclaw gateway restart
```

Discord may take a few seconds to show the new command in its autocomplete. Guild-scoped commands appear instantly; global commands can take up to an hour.

## Real Example: /feedback Skill

Here's a complete `SKILL.md` for a `/feedback` command:

```yaml
---
name: feedback
description: Submit feedback on any agent, digest, or system component. Use /feedback [agent] [rating] [text] for inline feedback.
user-invocable: true
command-dispatch: agent
---
```

```markdown
# Feedback Skill

## Usage
/feedback <agent> <rating> <text>

**Agents:** digest / coo / cto / youtube / writer / cpo / podcast / reading / system
**Ratings:** good / needs_work / useless

## Behavior
When called with ALL arguments: parse inline, store in DB, confirm.
When called with PARTIAL arguments: reply with usage help.

## Processing
1. Parse agent, rating, text
2. Validate (known agent, known rating)
3. Store in `issues` table with appropriate status
4. Confirm: "✅ Feedback logged: [agent] — [rating]."
5. STOP. No diagnosis, no long responses.
```

When a user types `/feedback coo good Great work today`, Discord sends it to OpenClaw, which routes it to the agent. The agent reads the skill, parses the arguments, inserts into the DB, and responds with a confirmation.

## Real Example: /acp Skill

ACP (Agent Communication Protocol) commands work similarly but are built-in rather than skill-based. The `/acp` command is registered natively when `commands.native` is enabled:

```
/acp spawn claude-code     — Start a Claude Code session
/acp status                — Check running ACP sessions  
/acp steer <id> <message>  — Redirect a running session
/acp cancel <id>           — Stop a session
```

These are handled by OpenClaw's core, not by a skill file. But they follow the same native command registration path.

## How Commands Are Named

Skill names are sanitized for Discord's requirements:

```
┌──────────────────────────────────────────────────────────┐
│ Rule                           │ Example                 │
├──────────────────────────────────────────────────────────┤
│ Lowercase only                 │ MySkill → myskill       │
│ a-z, 0-9, underscore only     │ my-skill → my_skill     │
│ Max 32 characters              │ Truncated if longer     │
│ Collision? Numeric suffix      │ test, test_2            │
└──────────────────────────────────────────────────────────┘
```

You can also invoke any skill via the generic command:

```
/skill feedback coo good Great work
```

This works even if the skill-specific command wasn't registered natively.

## Session Routing

Native slash commands use isolated sessions:

```
Discord: agent:<agentId>:discord:slash:<userId>
Telegram: telegram:slash:<userId>
```

This means slash command sessions are separate from your main chat session. The skill still executes with full agent context (AGENTS.md, SOUL.md, etc.), but conversation history is isolated.

## Troubleshooting

```
┌──────────────────────────────────────────────────────────────────────┐
│ Problem                        │ Fix                                │
├──────────────────────────────────────────────────────────────────────┤
│ Command not showing in Discord │ Restart gateway, wait ~30s         │
│ "Not authorized" on command    │ Check commands.allowFrom config    │
│ Command visible but no reply   │ Check user-invocable: true         │
│ Want text-only (no native)     │ Set nativeSkills: false            │
│ Slash command in wrong session │ Expected — slash uses isolated     │
│                                │ sessions, not main chat            │
└──────────────────────────────────────────────────────────────────────┘
```

## Quick Checklist

- [ ] `SKILL.md` has `user-invocable: true` in frontmatter
- [ ] `SKILL.md` has `command-dispatch: agent` (or `tool`)
- [ ] Skill is in `~/.openclaw/skills/<name>/` or `<workspace>/skills/<name>/`
- [ ] `commands.nativeSkills` is `"auto"` or `true`
- [ ] Gateway restarted after adding the skill
- [ ] User is in `commands.allowFrom` (if configured)
