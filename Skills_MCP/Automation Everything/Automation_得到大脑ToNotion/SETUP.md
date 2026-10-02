# Setup questions

**Say this first:** This automation pulls your 得到大脑 notes with the getnote CLI and lands them as Notion pages under a parent you configure.

Ask these before you write `Skill_得到大脑ToNotion`. A routine exists only if they want a schedule.

## Required

1. **CLI auth.** Is `getnote` on the path, and does `getnote auth status` show a masked key? If not, they run `getnote auth login` and authorize in the browser. Do not type their password and do not take a key in chat. Membership errors (`10201 not_member`) are billing: give them the checkout URL from the error payload.
2. **Notion parent.** One of:
   - `NOTION_PARENT_DATA_SOURCE_ID` (database), or
   - `NOTION_PARENT_PAGE_ID` (page).
   Until they have an id, store `YOUR_PARENT_DATA_SOURCE_ID` or leave the page id empty. Ask the title property name. Default you may offer: `Title`.
3. **What to pull by default?** A specific note id, "latest", or "when I name one". Note ids are strings. Do not coerce them to numbers.
4. **Schedule?** On demand is the default. If they want a routine, record cron, timezone, and the pull rule (for example "notes created since the last run"). If they say no, do not write `Routine_得到大脑ToNotion`.

Also confirm: share and delete on the getnote side need a yes every time. Landing a note in Notion is allowed when they asked for this automation.

## Record before you write

| Token | From |
| --- | --- |
| `{{PARENT_KIND}}` | `data_source_id` or `page_id` |
| `{{PARENT_ID}}` | Their id, or `YOUR_PARENT_DATA_SOURCE_ID` |
| `{{TITLE_PROPERTY}}` | Question 2 |
| `{{PULL_RULE}}` | Question 3 |
| `{{CRON}}` | Question 4, or `none` |
| `{{TIMEZONE}}` | Question 4, or `n/a` |

## Install

- `Skill_得到大脑ToNotion/SKILL.md` from [templates/SKILL.md](templates/SKILL.md).
- Local `config.json` from [templates/config.example.json](templates/config.example.json), gitignored.
- Routine only when `{{CRON}}` is a cron expression.
- Refuse `notion-create-pages` while the parent placeholder is still in place.

## Then do the work

If they named a note and the parent is real: `getnote note <id> -o json` (plus `original` or `transcript` when that is the body), write `pulled/<note_id>.md`, then create or update the Notion page and record `notion-map.json`. Chat gets the pointer, not the body.
