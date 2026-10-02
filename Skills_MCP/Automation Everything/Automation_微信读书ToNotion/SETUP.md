# Setup questions

**Say this first:** This automation pulls your WeRead highlights and your own reviews into Notion pages under a parent you configure.

Ask these before you write `Skill_微信读书ToNotion`. A routine exists only if they want a schedule.

## Required

1. **API key.** Is `WEREAD_API_KEY` exported in the shell that will run `prepare.py`? Tell them `export WEREAD_API_KEY=…`. If it is missing, stop. Do not take the key in chat, and do not read a secrets file from a home directory.
2. **Notion parent.** Data source id for the pages, or the placeholder `YOUR_PARENT_DATA_SOURCE_ID` until they have one. Env `NOTION_PARENT_DATA_SOURCE_ID` overrides `config.json`. Property names on that database (title, author, category). Defaults you may offer: `Title`, `Author`, `Category`, category value `Reading`. They must match the real database before you create pages.
3. **How many books on the first run?** Default you may offer: top 5 by highlight count plus their review count. Or they pass specific book ids at run time. Do not bake someone else's book ids into the skill.
4. **Schedule?** On demand is the default. Ask once: do they want a routine? If yes, cron and timezone. If no, do not write `Routine_微信读书ToNotion`.

## Record before you write

| Token | From |
| --- | --- |
| `{{PARENT_ID}}` | Question 2, or `YOUR_PARENT_DATA_SOURCE_ID` |
| `{{TITLE_PROPERTY}}` | Question 2 |
| `{{AUTHOR_PROPERTY}}` | Question 2 |
| `{{CATEGORY_PROPERTY}}` | Question 2 |
| `{{CATEGORY_VALUE}}` | Question 2 |
| `{{LIMIT}}` | Question 3 |
| `{{CRON}}` | Question 4, or `none` |
| `{{TIMEZONE}}` | Question 4, or `n/a` |

## Install

- Copy `templates/prepare.py` unchanged into `Skill_微信读书ToNotion/prepare.py`.
- Fill `templates/SKILL.md` and `templates/config.example.json` into that folder. The installed `config.json` holds their parent id and stays gitignored.
- Routine from `templates/ROUTINE.md` only when `{{CRON}}` is a cron expression.
- Refuse to create Notion pages while the parent is `YOUR_PARENT_DATA_SOURCE_ID`. Preparing markdown locally is fine.

## Gateway the skill will use

`POST https://i.weread.qq.com/api/agent/gateway` with `Authorization: Bearer $WEREAD_API_KEY`. Details are in the skill template. Business fields sit next to `api_name` and `skill_version`, not under `params`.

## Then do the work

If they asked to sync now and the key and parent are set, run `python3 prepare.py --limit {{LIMIT}}`, then `notion-create-pages` from `prepared/<bookId>.json`. Record each page with `python3 prepare.py --mark-synced BOOK_ID "Book Title" "https://www.notion.so/…"`.
