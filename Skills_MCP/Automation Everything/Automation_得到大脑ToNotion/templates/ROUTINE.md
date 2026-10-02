<!--
TEMPLATE. Install as Routine_得到大脑ToNotion/README.md only when SETUP.md
recorded a cron. If they said on demand, do not install this file.
-->

# Routine: 得到大脑 → Notion

When to run `Skill_得到大脑ToNotion`. Install this only because the user asked for a schedule.

| | |
| --- | --- |
| Cron | `{{CRON}}` |
| Timezone | `{{TIMEZONE}}` |
| Pull rule | {{PULL_RULE}} |
| Parent | `{{PARENT_ID}}` |
| Quiet | No chat ping when no new note matched |

**Grok Bot** can fire this cron. **Dots** and **Muse** often will not.

## Prompt to install

```
You are this user's Getnote to Notion routine.

Cron: {{CRON}}
Timezone: {{TIMEZONE}}
Pull rule: {{PULL_RULE}}

Each run:
1. Read and follow Skill_得到大脑ToNotion.
2. Pass -o json. Treat success=false as failure.
3. Land new matches under the configured Notion parent when that id is real.
4. Skip note ids already in notion-map.json unless the note updated.

Stay quiet when nothing new matched.
Do not announce that this routine fired.
Do not share or delete getnote notes on this run.
Do not paste note bodies or signed URLs into chat.
```
