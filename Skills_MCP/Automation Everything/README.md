# Automation Everything

Setup handoffs. An `Automation_*` folder is not a skill to run as-is.

## Security & privacy

These packs are for anyone who clones the repo.

- Credentials stay in environment variables or a local secret store. The pattern is `export WEREAD_API_KEY=…`. Never commit API keys, tokens, cookies, Bearer headers, or files from a secrets directory.
- Status output masks secrets. Do not print them.
- Signed media and object-storage URLs are credentials. Download the file if you need it. Do not paste the URL into chat, a commit, or a public channel.
- Reads are the default. Write, share, delete, redeem, or upgrade only when the user asks.
- Do not paste private Notion page or note bodies into public channels. A chat reply is a title, an id, and a link.
- Database and page ids belong to the user who answers the interview. Example configs use `YOUR_PARENT_DATA_SOURCE_ID` or `SET_AFTER_INTERVIEW`. Nothing here requires a pre-filled workspace id.
- The generated skill, `config.json`, `prepared/`, `baseline.json`, and sync maps stay on that user's machine. Do not commit them back to this repo.

## Contract

When someone hands you an `Automation_*` folder:

1. Ask the questions in that folder's `SETUP.md`. Offer the documented defaults, and wait for an answer before you write anything.
2. Fill `templates/` and install `Skill_*` plus `Routine_*` (or the host's native skill and routine) for that user.
3. Then do the named work.

| Prefix | Role |
| --- | --- |
| `Automation_*` | This repo. Interview, then install. |
| `Skill_*` | How. Written after the interview, on the user's host. |
| `Routine_*` | When it fires, and when to stay quiet. Written only if they named a cadence, a webhook, or both. |

**Grok Bot** can store the generated skill and run the routine. **Dots** and **Muse** may load the skill. They often will not auto-schedule a routine. On those hosts, still write the routine when they asked for one, and tell them the host will not fire it alone.

A skill and a routine ship together when the work should run unattended. 微信读书 and 得到大脑 get a routine only if the user asks for a schedule.

## Packs

| Handoff | What the interview decides | What gets installed |
| --- | --- | --- |
| [Automation_TokenPerf](Automation_TokenPerf/) | Cron, vendors, quiet-when-nothing-new, never claim without approval | `Skill_TokenPerf` and, when they named a cron, `Routine_TokenPerf` |
| [Automation_NotionComments_GrokBot](Automation_NotionComments_GrokBot/) | Webhook vs poll, bot prefix (`[Bot]` unless they change it), which pages or databases | `Skill_NotionComments_GrokBot` and `Routine_NotionComments_GrokBot` |
| [Automation_微信读书ToNotion](Automation_微信读书ToNotion/) | `WEREAD_API_KEY`, Notion parent placeholder, optional schedule | `Skill_微信读书ToNotion`, plus a routine only if they want one |
| [Automation_得到大脑ToNotion](Automation_得到大脑ToNotion/) | getnote auth, Notion parent placeholder, optional schedule | `Skill_得到大脑ToNotion`, plus a routine only if they want one |

## Prerequisites

| Need | Used by |
| --- | --- |
| Notion MCP on the user's workspace (`notion-fetch`, `notion-get-comments`, `notion-create-comment`, `notion-create-pages`, `notion-update-page`) | Notion comments, 微信读书, 得到大脑 |
| `export WEREAD_API_KEY=…` | 微信读书 |
| `getnote` CLI, logged in (`getnote auth status` masks the key) | 得到大脑 |
| Web search, and X search when the host has it | TokenPerf |
| A scheduler or a Notion webhook | Any routine they asked for |
