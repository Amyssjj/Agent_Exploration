# Building a Cron-Based Detection Pipeline — OpenClaw Tutorial

How to set up automated detection crons that scan your system for problems and log them to a database for later fixing.

## The Pattern: Detect → Store → Fix

Instead of fixing problems inline (which is fragile and hard to track), split the work into two phases:

```
┌────────────┐     ┌──────────┐     ┌────────────┐
│  Detection  │ ──→ │   DB     │ ←── │   Fixer    │
│  (cron)     │     │ (issues) │     │  (cron)    │
└────────────┘     └──────────┘     └────────────┘
   Runs often        Source of        Runs less often
   INSERT only       truth            UPDATE only
```

**Detection** scans for problems and INSERTs them as open issues.
**Fixing** claims open issues, fixes them, and closes them with resolution notes.
Never mix detection and fixing in the same job.

## Step 1: Create the Issues Table

The issues table is the backbone. Every detection writes here, every fixer reads from here.

```sql
CREATE TABLE issues (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    reported_by TEXT NOT NULL,
    type TEXT NOT NULL,
    rating TEXT,
    title TEXT NOT NULL,
    description TEXT,
    goal TEXT,
    category TEXT,
    status TEXT DEFAULT 'open',
    resolution_note TEXT,
    fix_agent TEXT,
    fix_session_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_issues_date ON issues(date);
CREATE INDEX idx_issues_type ON issues(type);
```

```
┌──────────────────────────────────────────────────────────────────┐
│ Field           │ Purpose                                        │
├──────────────────────────────────────────────────────────────────┤
│ id              │ Unique ID (e.g. HB-1234567890)                 │
│ reported_by     │ Who found it (heartbeat_detect, trend_review)  │
│ type            │ Category (improvement, cron_failure, etc.)     │
│ status          │ Lifecycle: open → in_progress → closed         │
│ fix_agent       │ Which agent claimed the fix                    │
│ resolution_note │ What was done to fix it                        │
└──────────────────────────────────────────────────────────────────┘
```

## Step 2: Write the Detection Skill

Create a skill that teaches your agent what to scan and how to report findings.

```
~/.openclaw/skills/detect/SKILL.md
```

```markdown
---
name: detect
description: Scan system health and insert new issues to the database.
---

# System Detection

Fast scan. INSERT new issues. Never fix anything.

## What to Scan

### 1. Cron Job Health
- Check cron run history for failures
- If any job failed since last check → INSERT issue

### 2. Agent Activity
- Check each agent's recent memory files
- If an agent hasn't logged anything in >48h → INSERT issue

### 3. Metric Drift
- Query goal metrics for today
- If any expected metric is missing → INSERT issue
- If any metric dropped significantly from yesterday → INSERT issue

### 4. Stale Issues
- Check for issues stuck in 'in_progress' for >48h → INSERT escalation

## How to Insert

Always deduplicate before inserting:

```sql
SELECT COUNT(*) FROM issues
WHERE type = 'cron_failure'
  AND title = 'Job morning-brief failed'
  AND status IN ('open', 'in_progress')
```

Only insert if count = 0:

```sql
INSERT INTO issues (id, date, reported_by, type, title, description, status)
VALUES (
  'HB-' || strftime('%s','now'),
  date('now'),
  'heartbeat_detect',
  'cron_failure',
  'Job morning-brief failed',
  'Exit code 1, error: rate limit exceeded',
  'open'
)
```

## Rules
- INSERT only. Never UPDATE, never fix.
- Deduplicate before inserting (check for existing open issue with same type+title).
- One issue per problem. Don't merge unrelated issues.
```

## Step 3: Create the Detection Cron Job

Set up a cron that runs the detection skill periodically:

```bash
openclaw cron add \
  --name "system-detect" \
  --cron "0 */4 * * *" \
  --tz "America/Los_Angeles" \
  --session isolated \
  --light-context \
  --message "Run the detect skill. Scan cron health, agent activity, metric drift, and stale issues. INSERT any new issues found. Report a summary of what you found." \
  --announce \
  --channel discord \
  --to "channel:YOUR_OPS_CHANNEL_ID"
```

```
┌──────────────────────────────────────────────────────────────────────┐
│ Flag              │ Why                                              │
├──────────────────────────────────────────────────────────────────────┤
│ --session isolated│ Clean slate each run, no context pollution       │
│ --light-context   │ Only loads essential files, faster startup       │
│ --announce        │ Posts summary to your ops channel                │
│ --cron "0 */4 * *"│ Every 4 hours                                   │
└──────────────────────────────────────────────────────────────────────┘
```

## Step 4: Add Data Collection Crons

Detection works best when there's fresh data to scan. Set up collection crons that write metrics to your database:

```bash
# Collect cron run records (3x/day)
openclaw cron add \
  --name "data-collection" \
  --cron "30 7,12,19 * * *" \
  --tz "America/Los_Angeles" \
  --session isolated \
  --light-context \
  --message "Run data collection: record cron runs, compute goal metrics, write to goal_metrics table." \
  --announce \
  --channel discord \
  --to "channel:YOUR_OPS_CHANNEL_ID"
```

### Goal Metrics Table

```sql
CREATE TABLE goal_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  goal TEXT NOT NULL,
  metric TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT,
  breakdown TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(date, goal, metric)
);
```

Collection scripts compute metrics and UPSERT them:

```sql
INSERT OR REPLACE INTO goal_metrics (date, goal, metric, value, unit)
VALUES (date('now'), 'cron_reliability', 'success_rate', 95.0, '%')
```

## Example: What Detection Finds

After a few days of running, your issues table might look like:

```
┌──────────────┬─────────────────────────────────────┬────────┐
│ Type         │ Title                               │ Status │
├──────────────┼─────────────────────────────────────┼────────┤
│ cron_failure │ Job data-collection failed (429)     │ open   │
│ metric_drift │ G6 satisfaction missing today        │ open   │
│ agent_idle   │ YouTube agent inactive 3 days        │ closed │
│ stale_issue  │ Issue HB-123 stuck in_progress 72h  │ open   │
│ cron_failure │ Job morning-brief timeout            │ closed │
└──────────────┴─────────────────────────────────────┴────────┘
```

The detection cron doesn't fix anything — it just makes problems visible. The fixer cron (see separate tutorial) handles resolution.

## Tips

1. **Keep detection fast** — Use `--light-context` so the agent doesn't waste tokens loading full workspace context
2. **Deduplicate always** — Check for existing open issues before inserting. Duplicate issues are noise.
3. **Be specific in titles** — "Job X failed" is better than "cron error". Titles are how you deduplicate.
4. **Use `reported_by`** — Different detectors (heartbeat, trend_review, user_feedback) should identify themselves so you can track detection sources.
5. **Don't fix in detection** — The moment you start fixing in detection, you lose the audit trail. Detection = INSERT only.
