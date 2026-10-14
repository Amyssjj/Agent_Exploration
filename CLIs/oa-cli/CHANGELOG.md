# Changelog

## Unreleased

### Added
- directional metric semantics via `MetricConfig.direction` (`higher` / `lower`)
- `failed_runs` and `unknown_runs` for `cron_reliability`
- `inactive_agent_count` for `team_health`
- richer `cron_runs` schema fields for real OpenClaw runtime data
- release smoke notes for `init → collect → status → serve/api`

### Changed
- scanner now detects agents from current OpenClaw runtime data sources, including cron run logs
- config template now includes `workspace_root` and `memory_paths`
- CLI / server health evaluation now respects lower-is-better metrics
- README synced to current behavior and current local test count
- dashboard now visualizes directional metrics and unknown cron runs
- bundled frontend assets refreshed

### Validated locally
- `python3 -m pytest -q` → `61 passed`
- smoke flow executed against a fresh temp project on `2026-03-23`:
  - `init`
  - `collect`
  - `status`
  - `serve --no-open` + `/api/health` + `/api/goals`
