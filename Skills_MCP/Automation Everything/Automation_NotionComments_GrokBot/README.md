# Automation: Notion comment follow-up

Handoff for an agent that answers Notion discussion comments. This folder is the interview. It is not the installed skill.

## Security & privacy

- Credentials stay in environment variables or a local secret store. Never commit API keys, tokens, cookies, or Bearer headers.
- Do not print secrets.
- Signed media URLs are credentials. Download if needed. Do not reprint them.
- Reads are the default. Post a Notion reply only for a question the user wants answered.
- Do not paste private page bodies into a public channel. Chat gets a one-line pointer and the Notion URL.
- Page and database ids come from the interview. This repo does not ship a workspace id. `YOUR_PARENT_DATA_SOURCE_ID` means "not set".
- The filled skill and `config.json` stay on the user's host. Do not commit them here.

## What you do with this folder

1. **Interview.** Read [SETUP.md](SETUP.md). Ask webhook vs poll, the bot prefix (example tag `[Bot]`), and which pages or databases to watch. Wait for answers.
2. **Install.** Fill [templates/SKILL.md](templates/SKILL.md) and [templates/ROUTINE.md](templates/ROUTINE.md). Write `Skill_NotionComments_GrokBot` and `Routine_NotionComments_GrokBot`, or the host's native skill and routine. Copy [templates/config.example.json](templates/config.example.json) to a local `config.json` and [templates/.gitignore](templates/.gitignore) beside it.
3. **Run.** The next unanswered comment on a page they named gets a reply in that thread, starting with their tag. If nothing is waiting, stay quiet.

**Grok Bot** can take the webhook and the poll. **Dots** and **Muse** may load the skill and often will not subscribe or cron. Tell them which half you could actually arm.

Leave `{{TOKEN}}` in this repo. Real ids live only in the generated files.
