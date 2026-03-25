# Discord Components v2 — OpenClaw Tutorial

How to send rich, interactive messages in Discord using OpenClaw's `message` tool with Components v2.

## What Are Components v2?

Components v2 replace plain text messages with structured, styled containers. They support:

- **Text blocks** — Markdown-formatted text sections
- **Separators** — Visual dividers between sections
- **Action rows** — Buttons (up to 5) or a single select menu
- **Media galleries** — Inline images
- **File blocks** — Attachments
- **Sections** — Text with a side accessory (button or thumbnail)
- **Modals** — Multi-field forms triggered by a button

Everything is wrapped in a **container** with an optional accent color stripe.

## Basic Structure

```json
{
  "action": "send",
  "channel": "discord",
  "target": "channel:1234567890",
  "message": "Fallback text (shown in notifications)",
  "components": {
    "text": "Header text (shown above the container)",
    "container": { "accentColor": "#FFCF50" },
    "blocks": [
      { "type": "text", "text": "### Section Title\nBody text with **markdown**" },
      { "type": "separator" },
      { "type": "text", "text": "Another section" }
    ]
  }
}
```

### Key fields

```
┌──────────────────────────────────────────────────────┐
│ Field              │ Purpose                          │
├──────────────────────────────────────────────────────┤
│ text               │ Header above the container       │
│ container          │ Accent color, spoiler toggle     │
│ blocks[]           │ Array of content blocks          │
│ reusable           │ Keep buttons/selects alive       │
│ modal              │ Attach a form to the message     │
└──────────────────────────────────────────────────────┘
```

## Block Types Reference

```
┌──────────────────────────────────────────────────────────────┐
│ Type           │ What it does                                │
├──────────────────────────────────────────────────────────────┤
│ text           │ Markdown text block                         │
│ separator      │ Horizontal divider line                     │
│ actions        │ Row of buttons OR a select menu             │
│ section        │ Text + side accessory (button/thumbnail)    │
│ media-gallery  │ Inline image(s) via attachment://           │
│ file           │ File attachment via attachment://            │
└──────────────────────────────────────────────────────────────┘
```

## Real Example: Daily Digest

This is a real daily digest template:

```json
{
  "action": "send",
  "channel": "discord",
  "target": "channel:YOUR_CHANNEL_ID",
  "message": "Daily Digest",
  "components": {
    "text": "📊 Daily Digest — March 24, 2026",
    "container": { "accentColor": "#FFCF50" },
    "blocks": [
      {
        "type": "text",
        "text": "### 🔴 Problems\n• Dashboard launchd crash-looping — macOS Sandbox blocking ~/Documents access\n• G6 satisfaction stuck at 54% — feedback UX needs overhaul"
      },
      { "type": "separator" },
      {
        "type": "text",
        "text": "### 💡 Insights\n• Context optimization pipeline live — 4/8 agents over prompt budget\n• Auto-optimizing metrics now collecting 3x/day"
      },
      { "type": "separator" },
      {
        "type": "text",
        "text": "### 🔧 Method\n• Moved launchd logs to ~/Library/Logs/ (sandbox-safe)\n• New G2 Automation Opportunities chart shipped"
      },
      { "type": "separator" },
      {
        "type": "text",
        "text": "### ✅ Result\n• Dashboard restored, all endpoints HTTP 200\n• 0 open issues after fixer run"
      },
      { "type": "separator" },
      {
        "type": "text",
        "text": "### 📋 Team Pulse\n🟢 **CTO** — Context optimization pipeline + auto-optimizing metrics\n🟢 **COO** — G2 chart, dashboard fix, issue fixer\n⏸️ **YouTube** — Standby\n⏸️ **Writer** — Standby"
      },
      { "type": "separator" },
      {
        "type": "text",
        "text": "-# Reviewed by COO Agent • /feedback to rate"
      }
    ]
  }
}
```

**Design rules:**
- Accent color `#FFCF50` (warm yellow) for digests
- Follow PIMR framework: Problem → Insights → Method → Result
- Footer uses Discord's small text syntax (`-#`)
- **No interactive buttons on digests** — they expire when the session ends

## Real Example: Content Approval with Buttons

Use buttons when you need a user to approve/reject content:

```json
{
  "action": "send",
  "channel": "discord",
  "target": "channel:YOUR_CHANNEL_ID",
  "message": "Review request",
  "components": {
    "text": "**📋 Content Review Request**\nProject: 2026-03-24_youtube-script\nDeliverable: story_arc_v2.md\n\n> AI agent coordination explainer — 12min target",
    "container": { "accentColor": "#A4B465" },
    "blocks": [
      {
        "type": "actions",
        "buttons": [
          {
            "label": "✅ Approve",
            "style": "success",
            "allowedUsers": ["YOUR_USER_ID"]
          },
          {
            "label": "❌ Reject",
            "style": "danger",
            "allowedUsers": ["YOUR_USER_ID"]
          },
          {
            "label": "💬 Feedback",
            "style": "secondary",
            "allowedUsers": ["YOUR_USER_ID"]
          }
        ]
      }
    ],
    "reusable": false
  }
}
```

**Key points:**
- `allowedUsers` locks buttons to specific Discord user IDs — others get an ephemeral denial
- `reusable: false` (default) = one click, then buttons expire
- `reusable: true` = buttons stay active until the message is deleted
- Accent color `#A4B465` (sage green) for review requests

## Real Example: Modal Form

Modals let users fill out structured forms. OpenClaw adds a trigger button automatically:

```json
{
  "action": "send",
  "channel": "discord",
  "target": "channel:YOUR_CHANNEL_ID",
  "message": "Submit feedback",
  "components": {
    "text": "**📝 Quick Feedback**",
    "container": { "accentColor": "#60A5FA" },
    "modal": {
      "title": "Submit Feedback",
      "triggerLabel": "📝 Open Form",
      "triggerStyle": "primary",
      "fields": [
        {
          "type": "text",
          "label": "Agent",
          "placeholder": "e.g. coo, cto, youtube",
          "required": true,
          "style": "short"
        },
        {
          "type": "text",
          "label": "Rating",
          "placeholder": "good / needs_work / useless",
          "required": true,
          "style": "short"
        },
        {
          "type": "text",
          "label": "Details",
          "placeholder": "What happened?",
          "required": false,
          "style": "paragraph"
        }
      ]
    }
  }
}
```

**Modal limitations:**
- Max 5 fields per modal
- Only text inputs (`short` or `paragraph`) — no select dropdowns
- Modal must be submitted within 15 minutes of opening
- Submissions arrive as a new inbound message to the agent

## Button Styles

```
┌──────────────────────────────────────────────────┐
│ Style       │ Color     │ Use for                │
├──────────────────────────────────────────────────┤
│ primary     │ Blue      │ Main action            │
│ secondary   │ Gray      │ Alternative action     │
│ success     │ Green     │ Approve / confirm      │
│ danger      │ Red       │ Reject / delete        │
│ link        │ Gray+icon │ External URL (no cb)   │
└──────────────────────────────────────────────────┘
```

## Select Menus

```json
{
  "type": "actions",
  "select": {
    "type": "string",
    "placeholder": "Choose an option",
    "options": [
      { "label": "Option A", "value": "a", "description": "First choice" },
      { "label": "Option B", "value": "b", "description": "Second choice" }
    ],
    "minValues": 1,
    "maxValues": 1
  }
}
```

Select types: `string`, `user`, `role`, `mentionable`, `channel`

## Media Gallery (Images)

```json
{
  "type": "media-gallery",
  "items": [
    { "url": "attachment://chart.png" }
  ]
}
```

Stage files to `~/.openclaw/media/outbound/` first, then reference via `media` parameter:

```json
{
  "action": "send",
  "channel": "discord",
  "target": "channel:123",
  "message": "Chart attached",
  "media": "file:///Users/you/.openclaw/media/outbound/chart.png",
  "components": {
    "blocks": [
      { "type": "media-gallery", "items": [{ "url": "attachment://chart.png" }] }
    ]
  }
}
```

## Common Mistakes

1. **Buttons expire** — Isolated cron sessions terminate → button handlers die → "interaction failed". Use `sessionTarget: "main"` for persistent buttons.
2. **No embeds + components** — Discord rejects messages that combine v2 components with legacy embeds.
3. **Modal text-only** — Discord modals only support text inputs (type 4). No select dropdowns in modals.
4. **Media staging** — Local file paths don't work. Stage to `~/.openclaw/media/outbound/` first.
5. **Forum parents** — Forum channels don't accept components. Send to the thread, not the parent.

## Config Requirements

Components v2 must be enabled in your OpenClaw Discord config:

```json5
{
  channels: {
    discord: {
      capabilities: {
        // "dm" | "group" | "all" | "allowlist"
        inlineButtons: "all"  // Enable interactive components
      }
    }
  }
}
```
