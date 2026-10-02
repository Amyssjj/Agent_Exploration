# Automation Everything

Public skills (how) and routines (when) for unattended agent work.

## Security & privacy

These packs are for anyone who clones the repo.

- Credentials stay in environment variables or a local secret store. The pattern is `export WEREAD_API_KEY=…`. Never commit API keys, tokens, cookies, Bearer headers, or files from a secrets directory.
- Status output masks secrets. Do not print them.
- Signed media and object-storage URLs are credentials. Download the file if you need it. Do not paste the URL into chat, a commit, or a public channel.
- Reads are the default. Write, share, delete, redeem, or upgrade only when the user asks.
- Do not paste private Notion page or note bodies into public channels. A chat reply is a title, an id, and a link.
- Database and page ids are the user's. Example configs use `YOUR_PARENT_DATA_SOURCE_ID`. Nothing in this folder requires a pre-filled workspace id.
- Local state (`config.json`, `prepared/`, `baseline.json`, sync maps) stays untracked. It can contain your notes.

## Naming

| Prefix | Contract |
| --- | --- |
| `Skill_*` | How to do the work. Pull and run when asked. Any skill-capable host. |
| `Routine_*` | When it fires (cron or event) and when to stay quiet. Only hosts that schedule work or receive webhooks. |

A skill and a routine ship together when the job should run with nobody watching. On-demand jobs are skills only.

**Grok Bot** can load these skills and run the routines. **Dots** and **Muse** may load the skills. They often will not auto-schedule a routine; run the skill when someone asks.

## Packs

| Area | Skill | Routine | What it does |
| --- | --- | --- | --- |
| Notion comments | [Skill_NotionComments_GrokBot](Skill_NotionComments_GrokBot/) | [Routine_NotionComments_GrokBot](Routine_NotionComments_GrokBot/) | Answer in the Notion discussion thread. Wake on `comment.created`, with a weekday backup poll. |
| 微信读书 → Notion | [Skill_微信读书ToNotion](Skill_微信读书ToNotion/) | — | Notebooks, highlights, and your own reviews into a Notion page you configure. |
| 得到大脑 → Notion | [Skill_得到大脑ToNotion](Skill_得到大脑ToNotion/) | — | Pull a Getnote note with the CLI, then create or update a Notion page you configure. |
| Token performance | [Skill_TokenPerf](Skill_TokenPerf/) | [Routine_TokenPerf](Routine_TokenPerf/) | Weekday scan for free or promo LLM credits. Stay quiet when nothing changed. Never claim without approval. |

微信读书 and 得到大脑 stay on demand until you name a schedule. Add a `Routine_*` beside the skill when you do.

## Prerequisites

| Need | Used by |
| --- | --- |
| Notion MCP connected to **your** workspace (`notion-fetch`, `notion-get-comments`, `notion-create-comment`, `notion-create-pages`, `notion-update-page`) | Notion comments, 微信读书, 得到大脑 |
| `export WEREAD_API_KEY=…` | 微信读书 |
| `getnote` CLI, logged in (`getnote auth status` masks the key) | 得到大脑 |
| Web search, and X search when the host has it | TokenPerf |
| A scheduler or Notion webhook | The two routines |

Copy `config.example.json` to `config.json` inside a skill before you point it at a database. `config.json` is gitignored.
