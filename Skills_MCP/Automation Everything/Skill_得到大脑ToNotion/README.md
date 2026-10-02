# Skill: 得到大脑 → Notion

Pull a note from 得到大脑 (Get笔记) with the `getnote` CLI, then create or update a Notion page under a parent you configure.

Agent contract: [SKILL.md](SKILL.md).

## Setup

```bash
npm install -g @getnote/cli@latest
getnote auth login          # you authorize in the browser; do not paste the key into chat
cp config.example.json config.json
```

Set `NOTION_PARENT_DATA_SOURCE_ID` or `NOTION_PARENT_PAGE_ID` to your page parent. Notion MCP does the write. The CLI never sees that id.

## Landing a note

```bash
getnote notes --limit 5 -o json
getnote note NOTE_ID -o json
```

The agent writes a local markdown file under `pulled/` (gitignored), then `notion-create-pages` or `notion-update-page`. Chat gets the title, the note id, and the Notion URL.
