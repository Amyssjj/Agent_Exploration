# Routine: Notion comment follow-up

When to run [Skill_NotionComments_GrokBot](../Skill_NotionComments_GrokBot/). This folder is a schedule and a quiet rule. The skill is how the reply is written.

Grok Bot can install this. Dots and Muse may load the skill and still skip the schedule; on those hosts, run the skill when someone asks.

| | |
| --- | --- |
| Event | Notion webhook `comment.created` |
| Backup | Weekday poll, in case a webhook is missed |
| Example cron | `0 17 * * 1-5` in `America/Los_Angeles` |
| Skill | `Skill_NotionComments_GrokBot` |
| Quiet | No Notion post and no chat ping when there is nothing to answer |

Change the cron to the hour you want. Do not point the webhook at a database id from someone else's workspace. Subscribe to the pages or integration the user actually uses.

## Prompt to install

```
You are the Notion comment routine.

Wake on Notion webhook event comment.created.
On weekdays, also run once as a backup poll (example cron: 0 17 * * 1-5 America/Los_Angeles) so a missed webhook still gets a pass.

Each run:
1. Read and follow Skill_NotionComments_GrokBot.
2. For each new or still-unanswered question, reply in that Notion discussion thread.
3. Use the configured leading bot tag (example default [Bot]).
4. Mention any long-form answer page with a dashed UUID in rich_text.

Stay quiet when there is nothing to answer.
Do not post a "no comments" note.
Do not announce that this routine fired.
Do not invent a database id. Answering does not need one.
Do not paste private page content into chat or any public channel.
```

## Quiet rules

- Nothing unresolved → end the run with no user-visible message.
- A resolved thread, or a comment that is not a question, is not a reason to reply.
- One reply per unanswered question. Do not re-answer a thread you already closed.
- Webhook and backup poll share that rule, so a comment handled from the webhook stays quiet on the afternoon poll.
