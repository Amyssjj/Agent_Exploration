# Implementation Plan - Generalize Exec Approvals

*Created at: 2026-02-12*


The user is experiencing "approval fatigue" because the current security model requires explicit approval for every new virtual environment or script path.
The goal is to implement "general control" where commands within trusted project directories are allowed automatically.

## User Review Required

The user explicitly requested to **avoid dangerous commands like `rm`**.
My previous plan to allow `/bin/**` and `/usr/bin/**` was flawed because it would allow `rm`.

## User Review Required

> [!IMPORTANT]
The user rejected `security: "full"` because even trusted agents could do dangerous things (accidentally or otherwise).
We must return to the **Safe Allowlist** strategy.

## User Review Required

> [!IMPORTANT]
> **Final Strategy: Safe Allowlist & Python scripts**
>
> 1.  **Strict Allowlist**: We will **NOT** use `security: "full"`.
> 2.  **Allowed Tools**: only safe tools (`ls`, `grep`, `ffmpeg`, `python3`...) and your project folders.
>     - **Virtual Environments**: ✅ Covered! Any venv inside `~/clawd-*` or `~/Documents` is automatically allowed.
> 3.  **Blocked**: `rm`, `sudo`, and broad system wildcards (`/bin/*`) remain **BLOCKED**.
>
> ⚠️ **Security Disclosure (Known Risk)**:
> You are correct: **Allowing `python3` (or `node`) allows scripts to delete files** (e.g. `os.remove()`).
> *   **We cannot block this** without making the agent useless for coding.
> *   **The Benefit**: This config prevents *accidental* shell damage (like a bad `rm -rf` copy-paste).
> *   **The Trade-off**: We trust the agent's *intent* when writing code, but verify its *shell commands*.
>
> **Solving the Remote Issue**:
> Since we cannot allow complex shell syntax (`$(...)`) in this mode, the agents must be guided to **use Python scripts** (which are allowed via `python3`) instead of complex shell loops.
> *   `bash -c "complex loop..."` -> **Prompts** (Blocked)
> *   `python3 script.py` -> **Allowed** (Safe)
>
> This gives you the safety you want. If an agent gets stuck on a shell prompt, you will need to ask it to "use a python script instead".

## Proposed Changes

### Configuration

#### [MODIFY] [exec-approvals.json](file:///Users/jingshi/.openclaw/exec-approvals.json)

I will implement the **Safe Allowlist** on the `*` agent.

```json
  "agents": {
    "*": {
      "security": "allowlist",
      "allowlist": [
        // Safe System Tools
        { "pattern": "/bin/ls" }, { "pattern": "/bin/cat" }, { "pattern": "/bin/cp" }, { "pattern": "/bin/mv" },
        { "pattern": "/bin/mkdir" }, { "pattern": "/bin/rmdir" }, { "pattern": "/bin/echo" }, { "pattern": "/bin/ps" },
        { "pattern": "/bin/pwd" }, { "pattern": "/bin/date" }, { "pattern": "/bin/sleep" },
        { "pattern": "/usr/bin/grep" }, { "pattern": "/usr/bin/find" }, { "pattern": "/usr/bin/wc" },
        { "pattern": "/usr/bin/head" }, { "pattern": "/usr/bin/tail" }, { "pattern": "/usr/bin/sort" },
        { "pattern": "/usr/bin/uniq" }, { "pattern": "/usr/bin/cut" }, { "pattern": "/usr/bin/sed" },
        { "pattern": "/usr/bin/awk" }, { "pattern": "/usr/bin/tr" }, { "pattern": "/usr/bin/diff" },
        { "pattern": "/usr/bin/curl" }, { "pattern": "/usr/bin/git" }, { "pattern": "/usr/bin/make" },
        { "pattern": "/usr/bin/tar" }, { "pattern": "/usr/bin/zip" }, { "pattern": "/usr/bin/unzip" },
        // Coding Environments
        { "pattern": "/opt/homebrew/bin/python3" }, { "pattern": "/opt/homebrew/bin/node" },
        { "pattern": "/opt/homebrew/bin/npm" }, { "pattern": "/opt/homebrew/bin/npx" },
        { "pattern": "/opt/homebrew/bin/yarn" }, { "pattern": "/opt/homebrew/bin/pnpm" },
        { "pattern": "/opt/homebrew/bin/go" }, { "pattern": "/opt/homebrew/bin/cargo" },
        { "pattern": "/opt/homebrew/bin/rustc" },
        // CLI Utilities
        { "pattern": "/opt/homebrew/bin/rg" }, { "pattern": "/opt/homebrew/bin/fd" },
        { "pattern": "/opt/homebrew/bin/jq" }, { "pattern": "/opt/homebrew/bin/yq" },
        { "pattern": "/opt/homebrew/bin/gh" }, { "pattern": "/opt/homebrew/bin/ffmpeg" },
        { "pattern": "/opt/homebrew/bin/ffprobe" }, { "pattern": "/opt/homebrew/bin/yt-dlp" },
        { "pattern": "/usr/bin/cd" }, // Allow changing directories in chains
        // User Projects (TRUSTED)
        { "pattern": "/Users/jingshi/clawd-*/**" },
        { "pattern": "/Users/jingshi/Documents/**" },
        { "pattern": "/Users/jingshi/.openclaw/**" },
        { "pattern": "/Users/jingshi/.gemini/**" }
      ]
    },
    // ... existing agents remain ...
  }
```

### Instructions

#### [NEW] [safe-scripting.md](file:///Users/jingshi/.clawdbot/skills/safe-scripting/safe-scripting.md)

I will create a "Skill" that teaches the agents to prefer Python scripts.

```markdown
---
description: Procedures for writing and executing safe scripts (Python) to avoid shell permission prompts.
---

# Safe Scripting Guidelines

When you need to perform complex operations (loops, file processing, data manipulation), **DO NOT use complex shell one-liners** (e.g., `for`, `while`, `$(...)`, `|`, `&&`, output redirection `>`).
These will trigger "Permission Denied" or "Approval Required" prompts which the user cannot approve remotely.

## ❌ The Blocked Way: Shell Complexity

Avoid these patterns:
*   **Command substitution**: `echo $(cat file.txt)` -> **PROMPTS** (Blocked by strict allowlist)
*   **Redirections**: `find . > output.txt` or `2>/dev/null` -> **PROMPTS** (Blocked by strict allowlist)
*   **Complex loops**: `for i in *; do ...; done` -> **PROMPTS**
*   **Pipes**: `cat file.txt | grep "foo"` -> **PROMPTS** (Use `grep` directly or Python)

## ✅ The Safe Way: Python

### Option A: Python Scripts (Cleanest)
Write a script file for complex logic.
1.  **Write**: `script.py`
    ```python
    import glob, subprocess
    files = glob.glob("*.mp4")
    # ... logic ...
    ```
2.  **Run**: `python3 script.py`

### Option B: Python One-Liners (Fastest)
Use `python3 -c` to run logic without writing a file (Zero Token Cost).
*   **Task**: List files to `output.txt` (Shell `>` is blocked).
*   **Python**: `python3 -c "import glob; print('\n'.join(glob.glob('*.txt')))"`

## When to use Shell vs Python

*   **Simple**: `ls -la`, `grep "foo" file`, `cp a b` -> **Use Shell**
*   **Complex**: Logic, loops, variables, piping, redirections -> **Use Python**
```

## Verification Plan

### Manual Verification
1.  **Check Config**: Verify `~/.openclaw/exec-approvals.json` contains the new `*` section.
2.  **Test Execution**:
    *   Create a temporary script in a new folder in Documents.
    *   Run it via an agent (e.g. using `run_command` with `SafeToAutoRun: false` to simulate user approval flow, but since I am the agent, I will check if it prompts).
    *   *Note*: As an agent, I cannot "see" the UI prompt, but I can check if the command executes successfully without a "permission denied" or timeout error (if auto-deny is on).
    *   Actually, the best verification is to ask the user to confirm if the prompts have stopped for their workflow.
