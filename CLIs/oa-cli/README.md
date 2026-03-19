# 📊 OA — Operational Analytics CLI

**Operational analytics for your AI agent team — from the command line.**

OA gives you a live dashboard to track how your [OpenClaw](https://github.com/openclaw/openclaw) multi-agent system is actually performing. Cron reliability, agent activity, custom goals — all from data your system already generates. Zero new infrastructure required.

## Why OA?

You've got agents running cron jobs, writing to memory, processing tasks. But how do you know if things are actually working?

- "Job ran" ≠ "job succeeded"
- Agent sessions exist, but are agents actually active?
- Problems get logged to memory files, but nobody's tracking the trends

OA reads the data OpenClaw already writes and turns it into real metrics — no new agents, no new integrations, no cloud services.

## Features

- 📊 **Built-in goals** — Cron Reliability and Team Health work instantly with zero config
- 🎯 **Custom goals** — define your own metrics via simple Python pipelines
- 🔭 **OTel-compatible tracing** — see exactly how data flows through your system
- 🖥️ **Live dashboard** — React UI served locally, auto-refreshes
- 🐍 **Zero dependencies** — pure Python core, reads from SQLite
- 🤖 **Agent-friendly** — works as an OpenClaw skill for autonomous monitoring

## Quick Start

```bash
pip install oa-cli

# Initialize — auto-detects your OpenClaw setup
oa init

# Collect metrics
oa collect

# Open dashboard
oa serve
```

## How It Works (Step by Step)

### Step 0: What You Already Have

If you're running OpenClaw, your machine already has all the data we need:

```
~/.openclaw/
├── cron/
│   ├── jobs.json                ← cron job definitions
│   └── runs/
│       ├── my-daily-job.jsonl   ← run history per job
│       └── data-collector.jsonl
├── sessions/                     ← agent session data
└── agents/                       ← agent configs
```

OA doesn't create new data — it reads what's already there.

### Step 1: Install

```bash
pip install oa-cli
```

Pure Python, zero runtime dependencies. No Node, no npm, no venv required. Takes ~5 seconds.

### Step 2: Initialize

```bash
cd ~/my-workspace
oa init
```

The CLI auto-detects your OpenClaw installation:

```
🔍 Scanning OpenClaw installation...

  OpenClaw:  ✓ Found at ~/.openclaw
  Agents:    ✓ 4 agents detected
             • researcher (last active: 2h ago)
             • writer (last active: 1d ago)
             • reviewer (last active: 3h ago)
             • publisher (last active: 5h ago)
  Cron:      ✓ 6 jobs (5 enabled, 1 disabled)

📊 Setting up built-in goals:
  ✓ G1 · Cron Reliability — success rate across all cron jobs
  ✓ G2 · Team Health — daily agent activity

📋 Optional goal templates:
  [1] Knowledge Sharing — shared learnings growth
  [2] Custom goal
  [0] Skip — just use built-ins

  Your choice (0-2): 0

✓ Created oa-project/
  ├── config.yaml         ← your goals + agent list
  ├── data/
  │   └── monitor.db      ← SQLite database (schema ready)
  └── pipelines/          ← data collection scripts

Next steps:
  oa collect    ← gather data now
  oa serve      ← open dashboard
```

**What happens under the hood:**
1. Reads `~/.openclaw/cron/jobs.json` → discovers your agents and cron jobs
2. Scans `~/.openclaw/sessions/` → detects which agents exist and their activity
3. Creates `config.yaml` with detected agents + built-in goals (thresholds auto-calculated)
4. Creates SQLite database with schema ready to receive metrics
5. Generates pipeline scripts with paths configured to your OpenClaw install

### Step 3: Collect Data

```bash
oa collect
```

```
📊 Collecting data for 2026-03-15...

  G1 · Cron Reliability
    ✓ Read 6 cron jobs from ~/.openclaw/cron/jobs.json
    ✓ Scanned 234 run entries from JSONL logs
    ✓ Matched 18 slots today → 15 success, 2 failed, 1 missed
    ✓ Success rate: 83.3%
    🔭 Trace: a4f2c... (6 spans)

  G2 · Team Health
    ✓ Scanned 4 agents
    ✓ 3 active today (researcher, reviewer, publisher)
    ✓ Memory logged: 2/4 agents
    🔭 Trace: b7e1d... (4 spans)

✓ Results written to data/monitor.db
```

The built-in pipelines read directly from OpenClaw's files — the same `cron/runs/*.jsonl` and session directories that already exist. No new data collection agents needed.

### Step 4: View Dashboard

```bash
oa serve
```

```
🖥️  Dashboard running at http://localhost:3460

  Goals:     2 tracked (Cron Reliability, Team Health)
  Agents:    4 configured
  Data:      1 day collected

  Press Ctrl+C to stop
```

Opens your browser → live React dashboard with:
- **Goal cards** with sparkline charts and health indicators
- **Goal-specific charts** — stacked bar + line for Cron Reliability, DAA dual chart for Team Health
- **Metrics definition panel** — click 📐 to see datasource, calculation, and purpose for each metric
- **Mechanism view** — SVG flow charts showing how data moves through pipelines
- **Click-to-expand trace details** — full execution trace with span tree and attributes

All from real data, auto-refreshes every 30 seconds.

### Step 5: Automate (Optional)

```bash
oa cron show
```

```
📋 Suggested cron schedule for OpenClaw:

  # Collect metrics 3x daily (paste into your OpenClaw config):
  {
    "name": "oa-collect",
    "schedule": {"kind": "cron", "expr": "0 7,12,19 * * *"},
    "payload": {"kind": "systemEvent", "text": "Run: oa collect"}
  }
```

Set it and forget it — metrics collected automatically.

## Built-in Goals

These work out of the box for any OpenClaw user. Zero configuration needed.

### G1 · Cron Reliability

Tracks whether your cron jobs are actually succeeding, not just running.

| Metric | Description | Source |
|--------|-------------|--------|
| `success_rate` | % of scheduled slots that succeeded | `~/.openclaw/cron/runs/*.jsonl` |
| `missed_triggers` | Jobs that never ran | `~/.openclaw/cron/jobs.json` + runs |

**Data flow:**
```
OpenClaw Scheduler → JSONL run logs → oa pipeline → SQLite → Dashboard
```

### G2 · Team Health

Tracks daily agent activity — are your agents actually working?

| Metric | Description | Source |
|--------|-------------|--------|
| `active_agent_count` | Agents with sessions today | `~/.openclaw/sessions/` |
| `memory_discipline` | % of agents that logged to memory | Agent memory files |

**Data flow:**
```
Agent sessions + memory files → oa pipeline → SQLite → Dashboard
```

## Custom Goals

Define your own metrics by writing a simple Python pipeline:

```python
# pipelines/content_quality.py
from oa import Pipeline, Metric

class ContentQuality(Pipeline):
    goal_id = "content_quality"

    def collect(self, date: str) -> list[Metric]:
        # Your logic — read files, APIs, whatever
        approved = count_approved_posts(date)
        total = count_total_posts(date)
        rate = approved / total * 100 if total else 0

        return [Metric("approval_rate", rate, unit="%")]
```

Register it in `config.yaml`:

```yaml
goals:
  # ... built-in goals auto-configured ...

  - id: content_quality
    name: "Content Quality"
    pipeline: pipelines/content_quality.py
    metrics:
      - name: approval_rate
        unit: "%"
        healthy: 90
        warning: 70
```

Run `oa collect` and your custom goal appears on the dashboard.

## Using with AI Agents

### As an OpenClaw Skill

Install the `oa` skill and your agents can:
- Run `oa collect` autonomously via cron
- Check system health before taking actions
- Detect issues and self-remediate

### Agent Instructions Example

```markdown
## Operational Monitoring
- Run `oa collect` at 7:30 AM, 12:30 PM, 7:00 PM
- If cron reliability drops below 80%, investigate and fix
- Log all fixes to memory for trend analysis
```

## Configuration

The `config.yaml` is auto-generated by `init` and fully editable:

```yaml
# Auto-generated by oa init
openclaw_home: ~/.openclaw

agents:
  - id: researcher
    name: Researcher
  - id: writer
    name: Writer
  - id: reviewer
    name: Reviewer
  - id: publisher
    name: Publisher

goals:
  - id: cron_reliability
    builtin: true
    metrics:
      - name: success_rate
        unit: "%"
        healthy: 95
        warning: 80

  - id: team_health
    builtin: true
    metrics:
      - name: active_agent_count
        unit: count
        healthy: 3
        warning: 2
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `oa init` | Auto-detect OpenClaw setup, create project |
| `oa collect` | Run all data pipelines |
| `oa collect --goal G1` | Run a specific pipeline |
| `oa serve` | Start dashboard on localhost:3460 |
| `oa serve --port 8080` | Start dashboard on custom port |
| `oa status` | Show current goal health (terminal) |
| `oa cron show` | Show suggested cron schedule |
| `oa doctor` | Check system dependencies |

## Architecture

```
OpenClaw writes:                    OA reads:
─────────────────                   ──────────────────────
cron/jobs.json          ──────►     What jobs exist, their schedules
cron/runs/*.jsonl       ──────►     Did each run succeed or fail?
sessions/ directory     ──────►     Which agents were active today?
agent memory files      ──────►     Did agents log their work?
                                           │
                                           ▼
                                    Python Pipelines (zero-dep)
                                           │
                                           ▼
                                    SQLite Database
                                           │
                                           ▼
                                    Dashboard (localhost:3460)
```

No servers to maintain. No cloud services. Everything runs on your machine.

## Requirements

- **Python 3.10+** (that's it for the core)
- **OpenClaw** installed and running
- **A web browser** to view the dashboard

## Tracing

Every data collection run produces OTel-compatible traces stored in SQLite. View them in the dashboard's **Mechanism** tab — SVG flow charts with shaped nodes (cylinder for DB, pill for cron, rectangle for scripts) and click-to-expand trace details.

```python
# Built-in tracing — automatically wraps every pipeline
from oa.tracing import Tracer

tracer = Tracer(service="my_pipeline")
with tracer.span("Data Collection") as span:
    span.set_attribute("rows_processed", 42)
    with tracer.span("DB Write") as child:
        # nested spans for detailed flow tracking
        ...
```

## Roadmap

- [x] Pre-built React dashboard (static files bundled in pip package — no Node required)
- [x] SVG flow chart trace visualization
- [x] Goal-specific charts (stacked bar + line, dual axis, per-agent bars)
- [x] Metrics definition panel
- [x] GitHub Actions auto-publish via PyPI trusted publishing
- [ ] `oa export` — export metrics to CSV/JSON
- [ ] More built-in goal templates (knowledge sharing, issue tracking)
- [ ] Code-splitting for dashboard bundle optimization
- [ ] OTel SDK export (optional, for users with existing observability)
- [ ] OpenClaw skill package for autonomous monitoring

## Contributing

```bash
git clone https://github.com/Amyssjj/Agent_Exploration.git
cd Agent_Exploration/CLIs/oa-cli
pip install -e ".[dev]"
pytest  # 57 tests
```

### Dashboard Development

The dashboard is a React app pre-built via Vite. End users never need Node — but if you're modifying the UI:

```bash
cd dashboard-src
npm install
npm run dev      # Vite dev server with hot reload
npm run build    # Build to ../src/oa/dashboard/
```

## License

MIT — built by [MotusAI](https://github.com/Amyssjj/Agent_Exploration)
