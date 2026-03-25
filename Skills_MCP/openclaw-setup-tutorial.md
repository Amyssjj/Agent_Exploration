# Setting Up OpenClaw with Claude Code + Gemini CLI Subscriptions

> **Goal:** Get OpenClaw running with both Anthropic (Claude) and Google (Gemini) as your AI models — using subscriptions you already have.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   YOUR DEVICE                        │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │           OpenClaw Gateway                    │   │
│  │           (localhost:18789)                    │   │
│  │                                               │   │
│  │  ┌─────────────┐    ┌──────────────────┐     │   │
│  │  │  Anthropic   │    │  Google Gemini    │     │   │
│  │  │  Claude 4.6  │    │  CLI (OAuth)     │     │   │
│  │  │  (primary)   │    │  (fallback)      │     │   │
│  │  └──────┬───────┘    └───────┬──────────┘     │   │
│  │         │    Model Router    │                │   │
│  │         └────────┬───────────┘                │   │
│  │                  │                            │   │
│  │         ┌────────┴────────┐                   │   │
│  │         │  Agent Runtime  │                   │   │
│  │         │  (your AI)      │                   │   │
│  │         └────────┬────────┘                   │   │
│  └──────────────────┼───────────────────────────┘   │
│                     │                                │
│    ┌────────────────┼────────────────────┐           │
│    │                │                    │           │
│  ┌─┴──┐    ┌───────┴───┐    ┌──────────┴──┐        │
│  │ 💬 │    │    🌐     │    │     📱      │        │
│  │Web  │    │ Discord   │    │ Telegram    │        │
│  │ UI  │    │ WhatsApp  │    │ iMessage    │        │
│  └─────┘    └───────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────┘
```

---

## What You Need

| Item | What | Cost |
|------|------|------|
| **Claude Code subscription** | Gives you Anthropic API access via setup-token | $20/mo (Max plan) |
| **Gemini CLI** | Free OAuth access to Gemini models | Free (Google account) |
| **Node.js 24+** | Runtime for OpenClaw | Free |

---

## Step 1: Install OpenClaw

```bash
# macOS / Linux
curl -fsSL https://openclaw.ai/install.sh | bash

# Windows (PowerShell)
iwr -useb https://openclaw.ai/install.ps1 | iex
```

Verify:
```bash
openclaw --version
```

---

## Step 2: Run Onboarding

```bash
openclaw onboard --install-daemon
```

The wizard walks you through everything. Here's what happens:

```
openclaw onboard
    │
    ├─ 1. Choose model provider
    │     → Select "Anthropic (setup-token)"
    │     → Paste your Claude Code setup token
    │
    ├─ 2. Pick default model
    │     → anthropic/claude-opus-4-6 (recommended)
    │     → or anthropic/claude-sonnet-4-6 (faster, cheaper)
    │
    ├─ 3. Set workspace
    │     → Default: ~/.openclaw/workspace
    │     → Or choose your own directory
    │
    ├─ 4. Configure gateway
    │     → Port: 18789 (default)
    │     → Auth: Token (auto-generated)
    │
    ├─ 5. Connect channels (optional)
    │     → Discord, Telegram, WhatsApp, etc.
    │
    └─ 6. Install daemon
          → Starts gateway automatically on boot
```

---

## Step 3: Add Gemini CLI as Fallback

After onboarding with Anthropic, add Gemini CLI as a fallback provider:

```bash
openclaw configure
# Select: Add another model provider
# Choose: Google Gemini CLI (OAuth)
# Browser opens → sign in with Google → authorize
```

Or set it up non-interactively:
```bash
openclaw models auth login google-gemini-cli
```

### Configure Fallback Chain

Edit your config (`~/.openclaw/openclaw.json`):

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-opus-4-6",
        "fallbacks": [
          "google-gemini-cli/gemini-3-pro-preview"
        ]
      }
    }
  }
}
```

```
Request Flow:
                                    
  User message                      
       │                            
       ▼                            
  ┌─────────────┐   ✅ success     
  │  Claude 4.6  ├──────────────► Response
  │  (primary)   │                  
  └──────┬──────┘                   
         │ ❌ fail/unavailable      
         ▼                          
  ┌──────────────┐  ✅ success     
  │  Gemini 3    ├──────────────► Response
  │  (fallback)  │                  
  └──────────────┘                  
```

**Why this order?**
- Claude 4.6 = strongest reasoning, best for complex tasks
- Gemini 3 Pro = free (OAuth), good backup when Anthropic is down

---

## Step 4: Verify Everything Works

```bash
# Check gateway is running
openclaw gateway status

# Open the web UI
openclaw dashboard

# Check available models
openclaw models list
```

You should see both providers listed:
```
anthropic/claude-opus-4-6          ← primary
anthropic/claude-sonnet-4-6
google-gemini-cli/gemini-3-pro-preview  ← fallback
google-gemini-cli/gemini-3.1-pro-preview
```

---

## Step 5: Connect a Chat Channel (Optional)

### Discord (recommended for teams)

```bash
openclaw configure --section discord
# Paste your Discord bot token
# Set allowed channels/users
```

### Telegram (fastest to set up)

```bash
openclaw configure --section telegram
# Paste your bot token from @BotFather
```

```
After channel setup:

  ┌──────────┐     ┌───────────┐     ┌──────────┐
  │  Phone   │     │  Desktop  │     │  Browser │
  │ Telegram │────►│  Discord  │────►│  Web UI  │
  └──────────┘     └───────────┘     └──────────┘
       │                │                  │
       └────────────────┼──────────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   OpenClaw   │
                 │   Gateway    │
                 │              │
                 │ Claude + Gemini
                 └──────────────┘

  Message from ANY channel → same AI agent → same context
```

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `openclaw onboard` | Initial setup wizard |
| `openclaw configure` | Reconfigure settings |
| `openclaw gateway status` | Check if gateway is running |
| `openclaw gateway restart` | Restart the gateway |
| `openclaw dashboard` | Open web UI |
| `openclaw models list` | Show available models |
| `openclaw models set <model>` | Change default model |
| `openclaw doctor` | Diagnose issues |

---

## Cost Breakdown

| Provider | Auth Method | Models | Cost |
|----------|-----------|--------|------|
| **Anthropic** | Setup token (Claude Code sub) | Claude 4.6 Opus/Sonnet | Included in $20/mo Max plan |
| **Gemini CLI** | OAuth (Google account) | Gemini 3 Pro, 3.1 Pro | Free |

**Total: $20/month** for Claude 4.6 primary + Gemini fallback. Compare to API-only pricing where Claude Opus can cost $15/1M input tokens.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Gateway not running` | `openclaw gateway start` |
| `No API key found` | `openclaw models auth login <provider>` |
| `Gemini OAuth expired` | `openclaw models auth login google-gemini-cli` |
| `Model not found` | `openclaw models list` to check available models |
| `Config issues` | `openclaw doctor --fix` |

---

*Built with OpenClaw — docs: [docs.openclaw.ai](https://docs.openclaw.ai)*
