# 2026-03-23 release smoke

## Scope
Ran a minimal end-to-end smoke flow against a fresh temp project using the current local source tree.

Repo under test:
- `/home/qz057/Agent_Exploration/CLIs/oa-cli`

Temp project root:
- `/home/qz057/.openclaw/workspace/tmp/oa-cli-smoke-20260323/smoke-project`

Command style used:
- `PYTHONPATH=src python3 -m oa.cli ...`

## Flow
1. `init -y`
2. `collect -c config.yaml`
3. `status -c config.yaml`
4. `serve --no-open -c config.yaml -p 3471`
5. `GET /api/health`
6. `GET /api/goals`

## Results
### init
- OpenClaw found at `/home/qz057/.openclaw`
- detected agents: `1`
- detected cron jobs: `0`
- project created successfully

### collect
Collected metrics successfully and wrote to:
- `data/monitor.db`

Observed terminal results:
- `success_rate: 0.0%`
- `failed_runs: 0.0 count`
- `unknown_runs: 0.0 count`
- `active_agent_count: 0 count`
- `inactive_agent_count: 1 count`
- `memory_discipline: 100.0%`

### status
Rendered terminal health table successfully.

Observed statuses:
- `Cron Reliability / success_rate` → `critical`
- `Cron Reliability / failed_runs` → `healthy`
- `Cron Reliability / unknown_runs` → `healthy`
- `Team Health / active_agent_count` → `critical`
- `Team Health / inactive_agent_count` → `warning`
- `Team Health / memory_discipline` → `healthy`

### serve/api
`serve --no-open` started successfully and API responded.

Observed `/api/health` payload:
```json
{"overall":"critical","goals":2,"healthy":0,"warning":0,"critical":2,"lastCollected":"2026-03-23"}
```

Observed `/api/goals` summary:
- goal count: `2`
- ids: `cron_reliability`, `team_health`

## Notes
- This smoke run used real local OpenClaw data availability, so the resulting health state was environment-dependent.
- The important result is that the full command chain completed and the API served valid responses.
- Separate unit regression remains green: `python3 -m pytest -q` → `61 passed`.
