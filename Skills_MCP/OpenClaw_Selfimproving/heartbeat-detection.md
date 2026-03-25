# Heartbeat-Based Detection — OpenClaw Tutorial

How to use OpenClaw's heartbeat system for lightweight, periodic monitoring that catches problems between cron runs.

## Heartbeat vs Cron Detection

```
┌──────────────────────────────────────────────────────────────────────┐
│                  │ Heartbeat Detection    │ Cron Detection           │
├──────────────────────────────────────────────────────────────────────┤
│ Runs in          │ Main session           │ Isolated session         │
│ Frequency        │ Every 30min (default)  │ Custom schedule          │
│ Context          │ Full conversation      │ Clean slate each run     │
│ Cost             │ Cheap (batched)        │ Full agent turn per job  │
│ Best for         │ Quick scans, alerts    │ Deep analysis, reports   │
│ Output           │ HEARTBEAT_OK or alert  │ Announce to channel      │
└──────────────────────────────────────────────────────────────────────┘
```

**Use heartbeat detection for:** Quick periodic scans that benefit from main session context.
**Use cron detection for:** Heavy scans that need isolation or precise timing.

They work best together — heartbeat catches urgent things fast, cron does thorough sweeps on a schedule.

## How Heartbeat Works

Every N minutes, OpenClaw sends your agent a heartbeat prompt. The agent reads `HEARTBEAT.md`, runs its checks, and either:

- Replies `HEARTBEAT_OK` (nothing to report — message is suppressed)
- Replies with an alert (delivered to your configured target)

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────┐
│  OpenClaw   │ ──→ │   Agent      │ ──→ │  HEARTBEAT_OK      │
│  (30min)    │     │  reads       │     │  (suppressed)      │
│             │     │  HEARTBEAT.md│     │       OR            │
│             │     │              │     │  Alert text         │
│             │     │              │     │  (delivered)        │
└─────────────┘     └──────────────┘     └────────────────────┘
```

## Step 1: Configure Heartbeat

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "30m",
        target: "last",                    // Deliver alerts to last active channel
        activeHours: { start: "07:00", end: "23:00" },  // No 3am alerts
        // lightContext: true,             // Optional: skip workspace files
        // isolatedSession: true,         // Optional: fresh session each beat
      }
    }
  }
}
```

```
┌──────────────────────────────────────────────────────────────────────┐
│ Setting          │ What it does                                     │
├──────────────────────────────────────────────────────────────────────┤
│ every            │ How often to check (default: 30m)                │
│ target           │ Where to send alerts (none/last/channel id)      │
│ activeHours      │ Only run during these hours (agent's timezone)   │
│ lightContext      │ Skip heavy workspace files for faster runs      │
│ isolatedSession   │ Fresh session each beat (no history buildup)    │
└──────────────────────────────────────────────────────────────────────┘
```

## Step 2: Write HEARTBEAT.md

This is the agent's checklist. Keep it small — every token costs money on every heartbeat.

```markdown
# HEARTBEAT.md

On heartbeat: run system checks. If nothing needs attention, reply HEARTBEAT_OK.

## Checks

### 1. Cron Health
- Query recent cron runs for failures
- Alert if any job failed in the last 2 hours

### 2. Open Issues
- Count open issues in the database
- Alert if >10 open issues (backlog growing)

### 3. Stale Claims
- Check for issues stuck in 'in_progress' >48h
- Alert with the stuck issue details

### 4. Infrastructure
- Verify database is accessible
- Verify memory search is working
```

**Key principle:** HEARTBEAT.md should be tiny. The agent reads it every 30 minutes. A 500-line checklist means 500 lines of tokens every 30 minutes.

## Step 3: Detection Skill for Heartbeat

Create a skill that the heartbeat can trigger. This is the "detect" logic:

```
~/.openclaw/skills/heartbeat-detect/SKILL.md
```

```markdown
---
name: heartbeat-detect
description: Fast scan for system issues. Run on every heartbeat.
---

# Heartbeat Detection

Fast scan. INSERT new issues to the issues table. Never fix anything.

## Scan Steps

### 1. Cron Health
- Check recent cron run history for failures
- If any job failed → INSERT issue (if not already tracked)

### 2. Open Issue Count
- Count open issues
- If >10 open → alert (backlog growing)

### 3. Stale Claims (48h rule)
- Find issues stuck in 'in_progress' for >48h
- INSERT escalation issue for each

### 4. Quick Infrastructure Check
- Test database connection
- Test memory search availability

## Insert Pattern

Always deduplicate:
```sql
-- Check if already tracked
SELECT COUNT(*) FROM issues
WHERE type = 'TYPE' AND title = 'TITLE' AND status IN ('open', 'in_progress')
```

Only insert if count = 0:
```sql
INSERT INTO issues (id, date, reported_by, type, title, description, status)
VALUES ('HB-' || strftime('%s','now'), date('now'), 'heartbeat_detect', ...)
```

## Rules
- INSERT only. Never UPDATE or fix.
- Be FAST. Heartbeat runs every 30min — don't do heavy analysis.
- Deduplicate before inserting.
- If nothing found → reply HEARTBEAT_OK
```

## Step 4: The Response Contract

Your agent must follow these rules:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Situation                    │ Agent Should Reply                   │
├──────────────────────────────────────────────────────────────────────┤
│ Nothing needs attention      │ HEARTBEAT_OK                         │
│ Found issues (inserted to DB)│ HEARTBEAT_OK (issues are tracked)    │
│ Something needs human action │ Alert text (NO HEARTBEAT_OK)         │
│ Infrastructure broken        │ Alert text (NO HEARTBEAT_OK)         │
└──────────────────────────────────────────────────────────────────────┘
```

**Important:** `HEARTBEAT_OK` must appear at the start or end of the reply. If the agent includes it in the middle of text, it won't be recognized.

- `HEARTBEAT_OK` → message suppressed, no notification
- Alert without `HEARTBEAT_OK` → delivered to your target channel

## Step 5: Combining Heartbeat + Cron Detection

The best setup uses both:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Check                        │ Where        │ Why                   │
├──────────────────────────────────────────────────────────────────────┤
│ Cron health (quick)          │ Heartbeat    │ Catch failures fast   │
│ Open issue count             │ Heartbeat    │ Cheap, frequent       │
│ Stale claims                 │ Heartbeat    │ 48h rule needs freq.  │
│ Infrastructure health        │ Heartbeat    │ Catch outages fast    │
│ Deep agent activity scan     │ Cron (4h)    │ Too heavy for beat    │
│ Metric completeness          │ Cron (4h)    │ Needs DB queries      │
│ Dropped ball detection       │ Cron (4h)    │ Needs session history │
│ Trend analysis               │ Cron (daily) │ Needs multi-day data  │
└──────────────────────────────────────────────────────────────────────┘
```

**Rule of thumb:** If the check takes <5 seconds and needs no heavy queries → heartbeat. If it needs deep analysis, session history, or multi-table queries → cron.

## Example: Full Detection Architecture

```
Every 30 minutes (heartbeat):
  ├── Quick cron failure check
  ├── Open issue count
  ├── Stale claim check
  └── Infrastructure ping
       ↓
  HEARTBEAT_OK (or alert)

Every 4 hours (detection cron):
  ├── Deep cron analysis (all jobs, all runs)
  ├── Agent activity scan (memory files, sessions)
  ├── Metric completeness check (all 6 goals)
  ├── Dropped ball detection (session history scan)
  └── Auto-optimizing opportunity detection
       ↓
  INSERT new issues to DB
  Announce summary to ops channel

Every 4 hours, offset 2h (fixer cron):
  ├── SELECT open issues
  ├── Claim → Fix → Close
  └── Escalate Red-tier issues
       ↓
  Report to ops channel
```

## Token Cost Management

Heartbeat runs are cheap but add up. Here's how to keep costs down:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Optimization             │ How                                      │
├──────────────────────────────────────────────────────────────────────┤
│ Small HEARTBEAT.md       │ Keep under 500 bytes                     │
│ lightContext: true        │ Skip workspace files on heartbeat       │
│ activeHours               │ No heartbeats while you're sleeping    │
│ Cheap model               │ Use a faster model for heartbeats      │
│ HEARTBEAT_OK suppression  │ No delivery cost for clean beats       │
│ Isolated session          │ No growing history consuming tokens    │
└──────────────────────────────────────────────────────────────────────┘
```

### Cost example

```
30-min heartbeat, 16 hours/day active:
= 32 heartbeats/day
= ~2,000 tokens per beat (small HEARTBEAT.md + light context)
= ~64,000 tokens/day for monitoring
≈ $0.20/day on Claude Sonnet (or near-zero on cheaper models)
```

Compare to 4 isolated cron detection runs:
```
= 4 runs × ~10,000 tokens each
= ~40,000 tokens/day
≈ $0.12/day
```

Together: ~$0.32/day for comprehensive automated monitoring.

## Troubleshooting

```
┌──────────────────────────────────────────────────────────────────────┐
│ Problem                     │ Fix                                   │
├──────────────────────────────────────────────────────────────────────┤
│ Heartbeat never fires       │ Check heartbeat.every > 0, gateway   │
│                             │ is running, activeHours is correct    │
│ Always gets HEARTBEAT_OK    │ Agent may not be finding issues —     │
│                             │ check DB access and query results     │
│ Too many false alerts       │ Tighten thresholds, add dedup logic  │
│ Alerts at 3am               │ Set activeHours to daytime only      │
│ Growing context/cost        │ Enable isolatedSession: true and/or  │
│                             │ lightContext: true                     │
│ Duplicate issues in DB      │ Check dedup query — must match on    │
│                             │ type + title + open status            │
└──────────────────────────────────────────────────────────────────────┘
```

## Quick Setup Checklist

- [ ] Heartbeat enabled (`agents.defaults.heartbeat.every: "30m"`)
- [ ] `HEARTBEAT.md` written (small — under 500 bytes)
- [ ] Detection skill created with scan steps
- [ ] Issues table created in your database
- [ ] Alert target configured (`target: "last"` or specific channel)
- [ ] Active hours set to avoid nighttime noise
- [ ] Tested: agent returns `HEARTBEAT_OK` when nothing found
- [ ] Tested: agent returns alert when you insert a test issue
