# Skill: 微信读书 → Notion

Pull your WeRead notebooks (划线 and your own 想法 / 书评) and prepare a Notion page payload for a database you configure.

Agent contract: [SKILL.md](SKILL.md). Prepare helper: [prepare.py](prepare.py).

## Setup

```bash
export WEREAD_API_KEY=…    # never commit this
cp config.example.json config.json
# edit NOTION_PARENT_DATA_SOURCE_ID and the property names to match your database
```

Requires Python 3.10+ (stdlib only) and Notion MCP on the create step.

## Prepare

Top N books by highlight count plus your review count:

```bash
python3 prepare.py --limit 5
```

One book you name (your own book id):

```bash
python3 prepare.py --book-id BOOK_ID
```

Check the markdown builder without calling WeRead or Notion:

```bash
python3 prepare.py --self-check
```

Payloads land in `prepared/<bookId>.json` (gitignored). Create the page with Notion MCP `notion-create-pages`, then record it:

```bash
python3 prepare.py --mark-synced BOOK_ID "Book Title" "https://www.notion.so/…"
```

`state.json` and `last_report.json` stay local.
