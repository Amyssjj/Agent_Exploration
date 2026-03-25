# Daily Digest — Discord Components v2 Format Reference

## PIMR Framework
Every digest follows PIMR: **Problem → Insights → Method → Result**
Report on what was identified, learned, and fixed — not just what happened.

## Container
- Accent color: `#FFCF50` (warm yellow)
- Always use components v2 (not plain text)
- **NO modal buttons. NO interactive components.** They expire and look broken.

## Structure
```json
{
  "components": {
    "text": "📊 Daily Digest — [DATE]",
    "container": {"accentColor": "#FFCF50"},
    "blocks": [
      {"type": "text", "text": "### 🔴 Problems\n• [What's broken, blocked, or at risk — with context]"},
      {"type": "separator"},
      {"type": "text", "text": "### 💡 Insights\n• [What did we learn? Patterns? What's improving/degrading?]"},
      {"type": "separator"},
      {"type": "text", "text": "### 🔧 Method\n• [What was done to fix problems? Systemic improvements?]"},
      {"type": "separator"},
      {"type": "text", "text": "### ✅ Result\n• [Outcomes. What's better? What needs Jing's input?]"},
      {"type": "separator"},
      {"type": "text", "text": "### 📋 Team Pulse\n*Phase: [current phase]*\n[emoji] [status] **[Agent]** — [1-line summary]\n..."},
      {"type": "separator"},
      {"type": "text", "text": "### 📧 Email Summary\n• [Count] emails needing attention\n• [1-line per important email: sender — subject — why it needs attention]\n• If nothing needs attention: 'Inbox clear — nothing requiring action'"},
      {"type": "separator"},
      {"type": "text", "text": "-# Reviewed by MotusCOO • /feedback to rate"}
    ]
  }
}
```

## Agent Emoji
- CTO 🔧, YouTube 🎥, Writer ✍️, CPO 📦, Podcast 🎙️, COO 🏗️

## Status Emoji
- 🟢 active today, 🟡 yesterday only, ⏸️ standby (intentional)

## Anti-Patterns
- ❌ No modal buttons on digests — they expire and look broken
- ❌ Don't report "agent idle" as urgent when it's intentional
- ❌ Don't list raw events without insights
- ❌ Don't show counts without meaning

## Context Rules
- Team phase awareness matters — report accordingly
- Agent idle may be intentional — use ⏸️ not 🔴 when expected
- The digest's job: show what was LEARNED and FIXED, not just what HAPPENED

## Feedback
- Footer says: `/feedback to rate`
- Jing uses `/feedback` slash command whenever ready — no expiry
- Feedback stored in DB, COO processes in #coo
- **#daily-digest is for digests only. Never post conversations there.**
