<!--
TEMPLATE. Install as Routine_微信读书ToNotion/README.md only when SETUP.md
recorded a cron. If they said on demand, do not install this file.
-->

# Routine: 微信读书 → Notion

When to run `Skill_微信读书ToNotion`. Install this only because the user asked for a schedule.

| | |
| --- | --- |
| Cron | `{{CRON}}` |
| Timezone | `{{TIMEZONE}}` |
| Limit | `{{LIMIT}}` |
| Parent | `{{PARENT_ID}}` |
| Quiet | No chat ping when no new book was prepared |

**Grok Bot** can fire this cron. **Dots** and **Muse** often will not. Say so if you could only install the skill.

## Prompt to install

```
You are this user's WeRead to Notion routine.

Cron: {{CRON}}
Timezone: {{TIMEZONE}}

Each run:
1. Read and follow Skill_微信读书ToNotion.
2. Run prepare.py with their limit. WEREAD_API_KEY comes from the environment. Do not print it.
3. Create Notion pages only when the parent id is real (not YOUR_PARENT_DATA_SOURCE_ID).
4. Skip books already in state.json.

Stay quiet when nothing new was prepared.
Do not announce that this routine fired.
Do not paste highlights or signed cover URLs into chat.
```
