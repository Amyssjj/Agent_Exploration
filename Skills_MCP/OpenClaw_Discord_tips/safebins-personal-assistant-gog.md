# Setting Up safeBins & Personal Assistant with gog CLI — OpenClaw Tutorial

How to give your OpenClaw agent access to CLI tools (like `gog` for Google Workspace) without requiring manual approval for every command.

## What Are safeBins?

By default, OpenClaw requires approval for every shell command an agent runs. `safeBins` is the list of "safe" executables that can run without approval — think of it as a pre-approved allowlist for low-risk, read-only tools.

```
Agent runs `gog gmail search "is:unread"`
  → OpenClaw checks: is `gog` in safeBins?
  → Yes → runs immediately, no approval needed
  → No → prompts user for /approve
```

### What belongs in safeBins

```
┌──────────────────────────────────────────────────────────────┐
│ ✅ Good for safeBins          │ ❌ Never put in safeBins     │
├──────────────────────────────────────────────────────────────┤
│ gog (Google Workspace CLI)    │ python3 (can run anything)   │
│ sqlite3 (query databases)    │ node (can run anything)      │
│ jq (JSON processing)         │ bash (shell interpreter)     │
│ grep (search files)          │ rm (delete files)            │
│ ls (list files)              │ curl (network requests)      │
│ find (search directories)    │ git push (modifies remote)   │
│ ffprobe (media info)         │ ssh (remote access)          │
└──────────────────────────────────────────────────────────────┘
```

**The rule:** safeBins is for stdin-only stream filters and read-only tools, not interpreters or destructive commands. Interpreters (python3, node, bash) can execute arbitrary code — use `exec-approvals.json` allowlists for those instead.

## Step 1: Install gog CLI

```bash
brew install gogcli/tap/gog
gog version
# gogcli v0.12.0
```

## Step 2: Configure Keyring (macOS)

gog stores OAuth tokens in a keyring. On macOS, use the native Keychain for non-interactive agent access:

```bash
gog auth keyring keychain
```

This eliminates the need for `GOG_KEYRING_PASSWORD` environment variable — macOS Keychain uses your login credentials automatically.

## Step 3: Authenticate with Google

```bash
gog auth add you@example.com --services gmail,calendar --force-consent
```

This opens a browser for Google OAuth. After authorizing, the token is stored in your macOS Keychain.

For full Google Workspace (Gmail + Calendar + Drive + Docs + Sheets + Slides):

```bash
gog auth add your-email@domain.com \
  --services gmail,calendar,drive,docs,sheets,slides \
  --force-consent
```

### Google Cloud APIs Required

Each service needs its API enabled in your GCP project:

```
┌──────────────────────────────────────────┐
│ Service    │ API to Enable               │
├──────────────────────────────────────────┤
│ Gmail      │ Gmail API                   │
│ Calendar   │ Google Calendar API         │
│ Drive      │ Google Drive API            │
│ Docs       │ Google Docs API             │
│ Sheets     │ Google Sheets API           │
│ Slides     │ Google Slides API           │
└──────────────────────────────────────────┘
```

Enable at: https://console.cloud.google.com/apis/library

## Step 4: Verify Auth Works

```bash
gog auth list
# Should show your email with configured services

gog gmail search "is:unread" --max 3
# Should return recent unread emails

gog calendar list --days 7
# Should return upcoming events
```

## Step 5: Add gog to Agent safeBins

Find your agent's index in the agents list:

```bash
openclaw config get agents.list
```

Then add `gog` to that agent's safeBins. For example, if your agent is at index 0:

```bash
openclaw config set agents.list.0.tools.exec.safeBins '["sqlite3","jq","gog"]'
```

Or to see the current safeBins first:

```bash
openclaw config get agents.list.0.tools.exec.safeBins
```

Then add `gog` to the existing array.

**Important:** This sets the entire array — include all existing entries plus the new one.

## Step 6: Restart Gateway

```bash
openclaw gateway restart
```

## Step 7: Create a Personal Assistant Skill

Create a skill that teaches your agent how to use gog:

```bash
mkdir -p ~/.openclaw/skills/personal-assistant
```

Write the skill file:

```markdown
# ~/.openclaw/skills/personal-assistant/SKILL.md

---
name: personal-assistant
description: Personal assistant for email, calendar, and Google Workspace via gog CLI.
---

# Personal Assistant

## Email (Gmail)

### Search inbox
gog gmail search "is:unread" --max 10

### Read a specific email
gog gmail read <message-id>

### Send email
gog gmail send --to "recipient@email.com" --subject "Subject" --body-file /tmp/email.txt

### Reply to email
gog gmail reply <message-id> --body-file /tmp/reply.txt

## Calendar

### View upcoming events
gog calendar list --days 7

### Create event
gog calendar create --title "Meeting" --start "2026-03-25T10:00:00" --duration 60

### Quick add (natural language)
gog calendar quick "Lunch with team tomorrow at noon"

## Drive

### List files
gog drive ls
gog drive ls <folder-id>

### Create folder
gog drive mkdir "Project Files"

### Upload file
gog drive upload /path/to/file.pdf --parent <folder-id>

## Docs

### Create document
gog docs create --title "Meeting Notes"

### Write to document
gog docs write <doc-id> --file /tmp/content.txt

## Sheets

### Create spreadsheet
gog sheets create --title "Budget Tracker"

### Append row
gog sheets append <sheet-id> --range "Sheet1" --values '["Item","Cost","Date"]'

## Best Practices
- Use --body-file or --file for long content (avoid inline --body with multiline text)
- Write content with the write tool first, then reference the temp file
- This avoids shell escaping issues and exec approval triggers
```

## Step 8: Test It

Chat with your agent:

```
"Check my email — anything urgent?"
"What's on my calendar this week?"
"Send an email to team@company.com with subject 'Weekly Update' — draft it based on today's work"
```

The agent will use `gog` commands without needing approval for each one.

## Full Config Example

Here's what the relevant config looks like when everything is set up:

```json5
{
  agents: {
    list: [
      {
        id: "main",
        // ... other config ...
        tools: {
          exec: {
            safeBins: ["sqlite3", "jq", "gog", "grep", "ls", "find"]
          }
        }
      }
    ]
  }
}
```

## For Interpreter Commands (Python Scripts)

If your assistant skill needs to run Python scripts (not just CLI tools), don't add `python3` to safeBins. Instead, use the allowlist:

Create or edit `~/.openclaw/exec-approvals.json`:

```json
{
  "agents": {
    "main": {
      "allowlist": [
        "python3 /path/to/specific_script.py",
        "python3 /path/to/another_script.py"
      ]
    }
  }
}
```

This allows specific scripts without opening up arbitrary Python execution.

## Troubleshooting

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Problem                            │ Fix                                │
├──────────────────────────────────────────────────────────────────────────┤
│ gog still needs approval           │ Check safeBins includes "gog",    │
│                                    │ restart gateway                    │
│ "token expired" errors             │ Run: gog auth add <email>         │
│                                    │ --services gmail,calendar         │
│                                    │ --force-consent                   │
│ "API not enabled" error            │ Enable the API in GCP console     │
│ Keyring password prompt            │ Switch to keychain backend:       │
│                                    │ gog auth keyring keychain         │
│ Agent can't find gog binary        │ Check gog is in PATH. For        │
│                                    │ Homebrew: /opt/homebrew/bin/gog   │
│ Multiline email body fails         │ Use --body-file /tmp/email.txt   │
│                                    │ instead of inline --body          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Security Notes

- OAuth tokens are stored in macOS Keychain (encrypted at rest)
- Tokens auto-refresh — no manual re-auth needed under normal use
- Agent can read email and manage calendar but can't extract the OAuth credentials
- If you revoke access in Google Account settings, the agent loses access immediately
- safeBins only bypasses the exec approval prompt — the agent still can't run arbitrary code
