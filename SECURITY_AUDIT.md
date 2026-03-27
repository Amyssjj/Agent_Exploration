# Security Audit Report

Date: 2026-03-27
Scope: repository-wide static review of source, notebooks, and configuration files.

## Summary

- **High risk fixed:** Sensitive Notion token-like value was present in a tracked notebook output and has been redacted.
- **Medium risk fixed:** Shell command execution used `subprocess.run(..., shell=True)` in markdown conversion paths; replaced with argument-list invocation (`shell=False` behavior).
- **Defense-in-depth fixed:** Added ignore rule to prevent accidental commits of agent cache artifacts under `Agent_Prototype/Agents/_cache/`.

## Findings

### 1) Sensitive token-like value in notebook outputs (**High**) — Fixed
- A token-like value matching `ntn_...` was present in `Agent_Prototype/Agents/MultiAgent_TripPlanner.ipynb` output cells.
- Risk: credential leakage, unauthorized API access, and secret persistence in Git history.
- Remediation applied:
  - Replaced token-like values with `ntn_REDACTED` in the notebook.

### 2) `shell=True` in markdown conversion bridge (**Medium**) — Fixed
- `Agent_Prototype/Tools/notion_markdown_utils/markdown_converter.py` used `subprocess.run` with `shell=True` for Node/Martian execution paths.
- Risk: command-injection surface expansion and shell parsing ambiguities.
- Remediation applied:
  - Replaced string command execution with list-based argument execution.
  - Removed dependence on shell parsing for these subprocess calls.

### 3) Cache artifact handling (**Low/Preventive**) — Fixed
- Agent cache directory can contain generated content and potentially sensitive data.
- Remediation applied:
  - Added `/Agents/_cache/` to `Agent_Prototype/.gitignore`.

## Checks executed

- Secret pattern scans via `rg`.
- Dangerous execution pattern scans (`shell=True`, subprocess usage).
- Syntax validation for modified Python module via `python -m py_compile`.

## Recommended next steps

1. **Rotate credentials** if the exposed token was ever valid.
2. **Purge Git history** if this repository is public/shared and the token appeared in prior commits.
3. Add automated secret scanning in CI (e.g., pre-commit + gitleaks/trufflehog).
4. Add static security checks in CI (Bandit or Semgrep rules for subprocess/shell usage).
