<!--
TEMPLATE. Install as Routine_NotionComments_GrokBot/README.md after SETUP.md.
{{WAKE_BLOCK}} is one of the three snippets in SETUP.md.
-->

# Routine: Notion comment follow-up

When to run `Skill_NotionComments_GrokBot`.

| | |
| --- | --- |
| Wake | `{{WAKE_MODE}}` |
| Cron | `{{CRON}}` |
| Timezone | `{{TIMEZONE}}` |
| Bot prefix | `{{BOT_TAG}}` |
| Scope | {{WATCH_SCOPE}} |
| Quiet | No Notion post and no chat ping when there is nothing to answer |

**Grok Bot** can arm a webhook and a cron. **Dots** and **Muse** often cannot. If this host cannot, the skill still runs when the user asks.

## Prompt to install

```
You are this user's Notion comment routine.

{{WAKE_BLOCK}}

Watch scope:
{{WATCH_SCOPE}}

Each run:
1. Read and follow Skill_NotionComments_GrokBot.
2. For each new or still-unanswered question in scope, reply in that Notion discussion thread.
3. Start the comment with {{BOT_TAG}}.
4. Mention any long-form answer page with a dashed UUID in rich_text.

Stay quiet when there is nothing to answer.
Do not post a "no comments" note.
Do not announce that this routine fired.
Do not invent a database id. If the parent is still YOUR_PARENT_DATA_SOURCE_ID, answer in the thread without filing a new page.
Do not paste private page content into chat or any public channel.
```

## Quiet rules

- Nothing unresolved in scope → end with no user-visible message.
- A resolved thread, or a comment that is not a question, is not a reason to reply.
- One reply per unanswered question. Do not re-answer a thread you already closed.
- Webhook and poll share that rule, so a comment handled from the webhook stays quiet on the later poll.
