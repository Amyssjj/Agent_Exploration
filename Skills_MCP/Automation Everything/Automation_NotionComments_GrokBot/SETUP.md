# Setup questions

Ask these before you write `Skill_NotionComments_GrokBot` or `Routine_NotionComments_GrokBot`. Wait for the answers. Do not invent a page id or a database id.

## Required

1. **Webhook, poll, or both?**
   - `webhook` — Notion event `comment.created` only.
   - `poll` — a cron you both agree, no webhook.
   - `webhook+poll` — webhook, plus a weekday backup poll in case the webhook is missed. Default poll you may offer: `0 17 * * 1-5` in `America/Los_Angeles`.
2. **Bot prefix.** Every Notion reply starts with this tag. Example default: `[Bot]`. Use `[Bot]` only after they accept it. One tag for every agent on the threads you answer.
3. **Which pages or databases?** They name the pages, databases, or "comments on pages shared with this integration". Record their words and any ids they paste. If they have no database yet, store `YOUR_PARENT_DATA_SOURCE_ID` and do not call Notion with that string.
4. **Long answers.** When a reply is too long for the thread, where should the page go? Optional parent data source. Same placeholder until they have one. Answering a comment does not require a parent.

Also confirm the quiet rule: nothing to answer means no Notion post and no chat ping.

## Wake snippets

Paste one block into `{{WAKE_BLOCK}}`.

Webhook:

```
Wake on Notion webhook event comment.created for the pages or databases this user named.
Do not run a backup poll.
```

Poll:

```
There is no webhook. Run on cron {{CRON}} in {{TIMEZONE}}.
Each run, check only the pages or databases this user named.
```

Webhook and poll:

```
Wake on Notion webhook event comment.created for the pages or databases this user named.
Also run a backup poll on cron {{CRON}} in {{TIMEZONE}} so a missed webhook still gets a pass.
```

## Record before you write

| Token | From |
| --- | --- |
| `{{WAKE_MODE}}` | `webhook`, `poll`, or `webhook+poll` |
| `{{WAKE_BLOCK}}` | The snippet above |
| `{{CRON}}` | Poll cron, or `none` |
| `{{TIMEZONE}}` | Timezone, or `n/a` |
| `{{BOT_TAG}}` | Their prefix. `[Bot]` only if they accepted the example |
| `{{WATCH_SCOPE}}` | Pages, databases, or the sentence they used |
| `{{PARENT_ID}}` | Their data source id, or `YOUR_PARENT_DATA_SOURCE_ID` |

## Install

- `Skill_NotionComments_GrokBot/SKILL.md` from [templates/SKILL.md](templates/SKILL.md).
- `Routine_NotionComments_GrokBot/README.md` from [templates/ROUTINE.md](templates/ROUTINE.md). The routine matches `{{WAKE_MODE}}`. A poll-only user still gets a routine. A webhook-only user gets a routine with no cron.
- Local `config.json` from [templates/config.example.json](templates/config.example.json).
- Host with no webhooks and no cron: install the skill, and tell them comments will be answered only when they ask.

## Then do the work

If they asked to catch up now, read comments on `{{WATCH_SCOPE}}` and reply in-thread where a question is still open. Use a dashed UUID in `rich_text` when you mention a page. If nothing is open, stop without a "no comments" message.
