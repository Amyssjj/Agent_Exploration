# Building a Cron-Based Issue Fixer — OpenClaw Tutorial

How to set up an automated fixer cron that claims open issues from your database, fixes them, and closes them with resolution notes.

## The Claim-Then-Fix Pattern

The fixer never just "closes" issues. It follows a strict lifecycle:

```
open → in_progress → closed
       (claimed)     (resolved)
```

This prevents two fixer runs from working on the same issue simultaneously.

```
┌────────────┐     ┌──────────────┐     ┌────────────────┐
│ SELECT     │ ──→ │ UPDATE       │ ──→ │ Do the work    │
│ open issues│     │ in_progress  │     │ then close     │
└────────────┘     └──────────────┘     └────────────────┘
   Find work        Claim it            Fix + resolve
```

## Step 1: Write the Fixer Skill

Create a skill that teaches your agent the fix workflow:

```
~/.openclaw/skills/fix/SKILL.md
```

```markdown
---
name: fix
description: Claim open issues, fix them, close with resolution notes.
---

# Issue Fixer

Uses claim-then-fix pattern.

## Database Access Rules
- You may READ (SELECT) from any table
- You may WRITE (INSERT/UPDATE) ONLY to: issues
- You must NEVER write to: goal_metrics, cron_runs, or other data tables

## Procedure

### 1. Find open issues
```sql
SELECT id, date, type, title, description, category
FROM issues
WHERE status = 'open'
ORDER BY created_at ASC
```

### 2. Claim before fixing
```sql
UPDATE issues
SET status = 'in_progress',
    fix_agent = 'my-agent',
    fix_session_id = 'SESSION_ID',
    updated_at = datetime('now')
WHERE id = 'ISSUE_ID'
```

### 3. Do the work
Investigate and fix based on issue type:
- Transient errors (rate limits, timeouts) → close as transient
- Real bugs → investigate root cause and fix
- Stale issues → escalate if >48h

### 4. Close with resolution note
```sql
UPDATE issues
SET status = 'closed',
    resolution_note = 'Description of what was done',
    updated_at = datetime('now')
WHERE id = 'ISSUE_ID'
```

## Rules
- CLAIM before fixing (prevents double-fix across concurrent runs)
- If fix reveals a NEW problem → INSERT as 'open', don't fix in same pass
- Detection INSERTs. Fixer UPDATEs. Never mix them.
- Report only what needs human attention
```

## Step 2: Issue Classification

Not all issues need the same treatment. Classify by severity and type:

```
┌────────────────────────────────────────────────────────────────┐
│ Tier    │ Action         │ Examples                            │
├────────────────────────────────────────────────────────────────┤
│ Green   │ Auto-close     │ Transient errors (429, timeout),   │
│         │                │ hook telemetry, ENOENT on fresh    │
│         │                │ memory files                        │
├────────────────────────────────────────────────────────────────┤
│ Yellow  │ Fix + close    │ Config issues, missing metrics,    │
│         │                │ stale claims, agent idle >48h      │
├────────────────────────────────────────────────────────────────┤
│ Red     │ Fix + escalate │ Repeated failures (same issue 3x), │
│         │                │ data pipeline broken, security     │
│         │                │ concerns                            │
└────────────────────────────────────────────────────────────────┘
```

### Green Tier (Auto-Close)

Most issues are transient noise. The fixer should bulk-close them:

```sql
-- Example: close all HOOK transient errors at once
UPDATE issues
SET status = 'closed',
    resolution_note = 'Transient error, system working as designed',
    fix_agent = 'my-agent',
    updated_at = datetime('now')
WHERE status = 'open'
  AND type LIKE 'HOOK%'
  AND title LIKE '%timeout%'
```

### Yellow Tier (Fix + Close)

These need actual investigation:

```markdown
Issue: "G6 satisfaction metric missing today"
→ Check: did the data collection cron run?
→ If not: run it manually or check why it failed
→ Close with: "Data collection cron had failed due to 429. Ran manually, metric now present."
```

### Red Tier (Escalate)

Don't silently close these. Post to your ops channel:

```markdown
Issue: "Same cron job failed 3 times in 24h"
→ Investigate root cause
→ Post to ops channel: "⚠️ Job X failing repeatedly — root cause: API quota exhausted. Needs human decision."
→ Close with: "Escalated to ops channel. Root cause: quota."
```

## Step 3: Create the Fixer Cron Job

```bash
openclaw cron add \
  --name "issue-fixer" \
  --cron "0 8,12,16,20 * * *" \
  --tz "America/Los_Angeles" \
  --session isolated \
  --light-context \
  --message "Run the fix skill. Claim and fix open issues from the issues table. For each issue: claim it (set in_progress), investigate, fix if possible, close with resolution note. Report summary to ops channel. Escalate Red-tier issues." \
  --announce \
  --channel discord \
  --to "channel:YOUR_OPS_CHANNEL_ID"
```

**Why 4x/day?** Detection runs every 4h, fixer runs every 4h offset by 2h. This gives issues time to accumulate before the fixer sweeps:

```
┌──────────────────────────────────────────────────┐
│ Time  │ What runs                                │
├──────────────────────────────────────────────────┤
│ 06:00 │ Detection scan                           │
│ 08:00 │ Fixer sweep (fixes issues from 06:00)    │
│ 10:00 │ Detection scan                           │
│ 12:00 │ Fixer sweep (fixes issues from 10:00)    │
│ 14:00 │ Detection scan                           │
│ 16:00 │ Fixer sweep (fixes issues from 14:00)    │
│ 18:00 │ Detection scan                           │
│ 20:00 │ Fixer sweep (fixes issues from 18:00)    │
└──────────────────────────────────────────────────┘
```

## Step 4: The 48-Hour Escalation Rule

Issues stuck in `in_progress` for >48h are a signal that something is wrong. The detection cron should flag these:

```sql
SELECT id, title, fix_agent, updated_at
FROM issues
WHERE status = 'in_progress'
  AND updated_at < datetime('now', '-48 hours')
```

If found → INSERT a new escalation issue and notify the ops channel.

## Step 5: Reporting

The fixer should post a concise summary after each run:

```
Issue Fixer Run — 12:00 PM
━━━━━━━━━━━━━━━━━━━━━━━━━
Found: 15 open issues
• 12 Green (transient) → auto-closed
• 2 Yellow (metric gaps) → fixed
• 1 Red (repeated cron failure) → escalated
Remaining: 0 open
```

Only post to the ops channel if there are Yellow/Red issues. Green-only runs can stay silent.

## Common Fixer Actions

```
┌──────────────────────────────────────────────────────────────────────┐
│ Issue Type                │ Typical Fix                              │
├──────────────────────────────────────────────────────────────────────┤
│ Transient API error       │ Close as transient (auto-resolves)       │
│ Missing metric today      │ Trigger data collection manually         │
│ Agent idle >48h           │ Check if intentional (standby vs stuck)  │
│ Config issue              │ Fix config, verify, close                │
│ Context/workspace bloat   │ Trim files, verify sizes, close          │
│ Repeated failure (3x)     │ Investigate root cause, escalate         │
│ User feedback (needs_work)│ Diagnose, create improvement plan        │
└──────────────────────────────────────────────────────────────────────┘
```

## Anti-Patterns

1. **Fixing in detection** — Detection INSERTs, fixer UPDATEs. Never mix. If the detector tries to fix, you lose the audit trail.
2. **Closing without claiming** — Always set `in_progress` first. This prevents two concurrent fixer runs from double-fixing.
3. **Silent Red issues** — Red-tier issues MUST be reported. Closing them quietly defeats the purpose.
4. **Fixing the same issue twice** — Deduplicate: check `fix_session_id` before claiming. If another session already claimed it, skip.
5. **Writing to data tables** — The fixer writes ONLY to `issues`. Never modify `goal_metrics`, `cron_runs`, or other source-of-truth tables.

## Monitoring the Pipeline

Track pipeline health with these queries:

```sql
-- Open issues by type (what's piling up?)
SELECT type, COUNT(*) FROM issues
WHERE status = 'open' GROUP BY type ORDER BY COUNT(*) DESC

-- Fix rate (overall health)
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed,
  ROUND(100.0 * SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) / COUNT(*), 1) as fix_rate
FROM issues

-- Average time to fix (efficiency)
SELECT type,
  ROUND(AVG(julianday(updated_at) - julianday(created_at)) * 24, 1) as avg_hours
FROM issues
WHERE status = 'closed'
GROUP BY type

-- Stuck issues (needs attention)
SELECT id, title, fix_agent, updated_at
FROM issues
WHERE status = 'in_progress'
  AND updated_at < datetime('now', '-48 hours')
```
