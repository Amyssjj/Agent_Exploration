# Story Arc: Best Practices of AI Agent Setup

*Created at: 2026-02-16*


## Overall Takeaway

> **Every file has a job. When content lands in the wrong file, you pay for it on every single API call — or worse, critical rules go unseen.**

Five files form a cohesive system. Each answers one question:

| File | Question | Loaded |
|:---|:---|:---|
| **SOUL.md** | *Who are you?* | Every turn |
| **AGENTS.md** | *How do you operate?* | Every turn (+ subagents) |
| **TOOLS.md** | *What's your local setup?* | Every turn |
| **MEMORY.md** | *What have you learned?* | Main session only |
| **SKILL.md** | *How do you use tool X?* | On demand |

The cost structure is the key insight: files loaded every turn multiply their token cost by every message in the conversation. A 500-token overlap across files costs 5,000 wasted tokens in a 10-turn chat.

---

## Previous Problems

### 1. Everything dumped into AGENTS.md
Discord formatting rules, tool-specific workflows, personality traits, environment paths — all crammed into one file. Result: bloated system prompt on every turn, even when 80% of it was irrelevant.

### 2. Safety rules hidden in skills
Critical execution rules (dangerous command lists, "ask before deleting") lived in `SKILL.md` files marked "Apply always" — but skills only load on demand. The agent could run `rm -rf` without ever seeing the safety checklist.

### 3. Hardcoded paths inside skills
Local machine paths (`/Users/jingshi/Documents/...`) baked into shareable skill files. Move to a new machine or share the skill → everything breaks.

### 4. SOUL.md stuffed with procedures
Model identifier formatting rules, platform-specific message formatting, team coordination protocols — none of this is *identity*. It's procedure wearing a personality mask.

### 5. No subagent awareness
Main agents delegated work to subagents without knowing that subagents only see `AGENTS.md` + `TOOLS.md`. Critical context (personality, user preferences, project history) never reached the worker, producing generic output.

### 6. Inter-agent communication via shared channels
Agents posting to Discord channels hoping other agents would "see" the message. No guaranteed delivery, routing conflicts, agents responding to each other's posts unpredictably.

---

## Insights

### The Pointer Pattern
Keep frequently-loaded files (AGENTS.md, SOUL.md, TOOLS.md) lean by using **one-line pointers** to full documentation in on-demand files (SKILL.md):

> AGENTS.md: *"Safe Execution — danger list → ask first; full rules: `~/.openclaw/skills/safe-scripting/SKILL.md`"*

4 tokens every turn. Full rules loaded only when executing commands.

### The Swap Test
To verify content placement, ask:
- *"Would this still make sense if I swapped personalities?"* → If yes, it doesn't belong in SOUL.md
- *"Would this still make sense on a different machine?"* → If yes, it doesn't belong in TOOLS.md
- *"Is this a standing order or a learned fact?"* → Standing order → AGENTS.md; learned fact → MEMORY.md

### Subagents Are Blind Workers
They see `AGENTS.md` + `TOOLS.md` only. No personality, no memory, no user context. The main agent must pass everything relevant in the `task` parameter of `sessions_spawn`.

### Use `sessions_send` Over Shared Channels
For reliable agent-to-agent communication, use direct `sessions_send`. Discord channels are for **human visibility**, not inter-agent coordination.

---

## Solution: Before ↔ After

### SOUL.md — Identity Only

| Before ❌ | After ✅ |
|:---|:---|
| Core personality + model ID formatting rules + Discord formatting + team coordination + continuity reminders | Pure identity: who you are, your values, your tone |
| ~300 tokens | ~60 tokens |

```diff
 # SOUL.md
 You're MarketingVideo — Jing's YouTube content machine.
-## Message Format Rule (MANDATORY)
-Every message MUST start with your model identifier...
-(100 tokens of formatting procedure)
-## Platform Formatting (MANDATORY)
-Discord: No raw markdown tables...
-## Boundaries
-Coordinate with Motus and MarketingWriter...
-## Continuity
-Each session, you wake up fresh...
+## Values
+- Quality over speed — never upload half-baked
+- Private things stay private
+- When in doubt, ask Jing before publishing
```

---

### AGENTS.md — Lean Operational Playbook

| Before ❌ | After ✅ |
|:---|:---|
| Generic template with redundant "Read SOUL.md" instructions, no production workflow, no subagent rules | Purpose-built playbook: production phases, approval flow, subagent delegation, safety pointers |
| Missing YouTube-specific guidance | Every section earns its place |

```diff
 # AGENTS.md
 ## Every Session
-1. Read SOUL.md — this is who you are
-2. Read USER.md — this is who you're helping
-3. Read memory/YYYY-MM-DD.md
+1. Read memory/YYYY-MM-DD.md (today + yesterday)
+2. Read STATUS.md for current project state
+3. Main session only: Also read MEMORY.md

+## Production Workflow
+1. Brainstorm → get topic approval
+2. Story arc → draft outline, get approval
+3. Production → spawn subagents (parallel)
+4. Assembly → concat + audio, quality check
+5. Delivery → never deliver silent renders

+## Subagent Delegation
+- Include full context in task param
+- Use descriptive labels
+- Set runTimeoutSeconds: 300 for renders
```

---

### SKILL.md — Tool Docs Only

| Before ❌ | After ✅ |
|:---|:---|
| Hardcoded local paths in Environment section | Paths moved to TOOLS.md, skill references `See TOOLS.md § Manim Setup` |
| Governance rules ("Jing will reject...") mixed with tool docs | Governance in AGENTS.md, technical how-to stays in SKILL.md |
| Discord media workflow in safe-scripting skill | Moved to TOOLS.md or discord skill where it belongs |

```diff
 # safe-scripting/SKILL.md
-## Part 4: Sending Media via Discord
-Stage files to ~/.openclaw/media/outbound/...
+(removed — belongs in TOOLS.md or discord skill)

 # manim-animation/SKILL.md
 ## Environment
-source /Users/jingshi/Documents/.venv/bin/activate
-cd /Users/jingshi/Documents/projects/<project>/
+See TOOLS.md § Manim Setup for paths and venv activation.
```

---

### TOOLS.md — Local Environment Map

| Before ❌ | After ✅ |
|:---|:---|
| Paths scattered across SKILL.md files | Single source of truth for all local paths |
| No project structure documentation | Clear folder structure with purpose annotations |

```diff
+### YouTube Projects
+- Root: ~/Documents/MotusAI_Teams/clawd-youtube/projects/
+
+### Project Structure
+<project_name>/
+├── topics/        # research, brainstorm notes
+├── story_arc/     # outlines, structure drafts
+├── scripts/       # voiceover scripts
+├── scenes/        # Manim scene .py files
+├── media/         # generated assets
+├── evidence/      # reference material
+└── approved/      # user-approved deliverables only
+
+### Manim
+- venv: ~/Documents/MotusAI_Teams/clawd-youtube/.venv/
+
+### Discord Media
+- Outbound staging: ~/.openclaw/media/outbound/
```

---

### Inter-Agent Communication

| Before ❌ | After ✅ |
|:---|:---|
| Post to shared Discord channel, hope other agents see it | `sessions_send` for guaranteed delivery + Discord for human visibility |
| No approval distribution workflow | Explicit post-approval notification with file paths |

```diff
+## Post-Approval Distribution
+After content is approved:
+1. Move deliverable to approved/
+2. sessions_send → MarketingWriter (with script path)
+3. sessions_send → Motus (with script path)
+4. Post to #content-updates for human visibility
```

---

### Shared vs. Per-Agent Skills

| Before ❌ | After ✅ |
|:---|:---|
| Discord formatting rules duplicated in every agent's SOUL.md | Global skill at `~/.openclaw/skills/discord-formatting/` — auto-discovered by all agents |
| Each agent maintains its own copy | Single source of truth, update once |

```
~/.openclaw/skills/          ← shared across all agents
├── discord-formatting/
│   └── SKILL.md             ← one set of rules
├── safe-scripting/
│   └── SKILL.md
└── ...

~/.openclaw/agents/youtube/skills/  ← YouTube-specific
└── manim-animation/
    └── SKILL.md
```
