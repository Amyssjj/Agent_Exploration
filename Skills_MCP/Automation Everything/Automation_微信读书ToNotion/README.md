# Automation: 微信读书 → Notion

Handoff that pulls your WeRead notebooks into Notion pages you configure. This folder is the interview. It is not the installed skill.

## Security & privacy

- The only WeRead credential is `export WEREAD_API_KEY=…`. Never commit the key, a Bearer header, or a file from a secrets directory. Do not ask the user to paste the key into chat.
- Status output masks secrets. Strip `Bearer` values and `wrk-…` tokens from error text.
- Signed cover and media URLs are credentials. Download if you need the file. Do not paste them into chat or git.
- Sync the signed-in user's highlights and their own reviews. Leave other people's public reviews and popular highlights out.
- The Notion parent is theirs. `YOUR_PARENT_DATA_SOURCE_ID` is not a database. Do not send it to Notion, and do not commit a real id into this repo.
- `prepared/`, `state.json`, and `config.json` hold their notes. They stay untracked.

## What you do with this folder

1. **Interview.** Read [SETUP.md](SETUP.md). Confirm the env key, the Notion parent placeholder, property names, and whether they want a schedule.
2. **Install.** Fill [templates/SKILL.md](templates/SKILL.md) into `Skill_微信读书ToNotion/SKILL.md`. Copy [templates/prepare.py](templates/prepare.py), [templates/config.example.json](templates/config.example.json), and [templates/.gitignore](templates/.gitignore) into that skill. Write `config.json` locally from their answers. Install [templates/ROUTINE.md](templates/ROUTINE.md) as `Routine_微信读书ToNotion` only if they asked for a schedule.
3. **Run.** If they asked to sync now, run `prepare.py` for the limit they chose, then create pages with Notion MCP. Chat gets book titles and Notion URLs, not highlight text.

**Grok Bot** can cron the optional routine. **Dots** and **Muse** may load the skill and often will not. A user who wants on-demand sync gets the skill only.

`prepare.py --self-check` builds a synthetic page in memory. It does not call WeRead or Notion.
