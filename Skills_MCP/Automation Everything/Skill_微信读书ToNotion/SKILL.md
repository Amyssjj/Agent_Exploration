---
name: weread-to-notion
description: >-
  Pull the user's WeRead notebooks (highlights and their own reviews) through
  the Agent Gateway and prepare Notion pages under a parent they configure.
  Requires WEREAD_API_KEY. Never commit the key or private highlights.
---

# 微信读书 → Notion

Turn **your** WeRead notebooks into Notion pages. Highlights (划线) and your own ideas and reviews (想法 / 书评) are the export. Bookmark positions are counts only. Other people's public reviews and popular highlights are not your notes; leave them out of the sync.

## Credentials

```bash
export WEREAD_API_KEY=…
```

That is the only credential. The gateway expects `Authorization: Bearer $WEREAD_API_KEY`. If the variable is unset, stop and tell the user to export it. Do not ask them to paste the key into chat, and do not read a secrets file from a home directory as a fallback.

Never print the key. Mask `Bearer` values and any `wrk-…` token if an error body echoes them.

## Gateway

```
POST https://i.weread.qq.com/api/agent/gateway
Content-Type: application/json
Authorization: Bearer $WEREAD_API_KEY
```

Business fields sit on the top-level JSON object, next to `api_name` and `skill_version`. Do not wrap them in `params`.

```json
{"api_name":"/user/notebooks","count":20,"skill_version":"1.0.4"}
```

Next page, `lastSort` is the last book's `sort` from the previous page:

```json
{"api_name":"/user/notebooks","count":20,"lastSort":0,"skill_version":"1.0.4"}
```

`skill_version` is `1.0.4` unless `config.json` overrides it. If a response contains `upgrade_info`, stop and follow `upgrade_info.message` before continuing.

A non-zero `errcode` is a failure. Say so in plain language. Do not dump the raw body if it might contain a token.

## Flow

1. **Notebooks.** `POST` `api_name` `/user/notebooks`. Page with top-level `count` and `lastSort` until `hasMore` is 0. Do not send `offset` or `limit`.
2. **Score.** Per book, statistical note count is `reviewCount + noteCount + bookmarkCount`. `noteCount` is highlight count, not the total. Content you can export is highlights plus your reviews. `bookmarkCount` stays a number.
3. **Highlights.** `/book/bookmarklist` with `bookId`. Response `updated[]` is highlight text (`markText`). `chapters[]` maps `chapterUid` to a title. This call already drops positional bookmarks.
4. **Your reviews.** `/review/list/mine` with `bookid`, `synckey`, and `count`. Page while `hasMore` is 1. Keep items that have `content` or `abstract`.
5. **Markdown.** Group highlights by chapter. Quote highlight text with `>`. Under 想法 / 书评, quote `abstract` when the idea points at a passage, then the idea text.
6. **Notion.** Create a page under the user's parent with Notion MCP. This skill does not call the Notion HTTP API.

Copy [config.example.json](config.example.json) to `config.json`. Set `NOTION_PARENT_DATA_SOURCE_ID` to the user's data source. `YOUR_PARENT_DATA_SOURCE_ID` is a placeholder. Refuse to create a page with that string. Property names in the example (`Title`, `Author`, `Category`) are defaults; rename them to match the database. The env var `NOTION_PARENT_DATA_SOURCE_ID` overrides the file.

`notion-create-pages`:

- `parent`: `{ "type": "data_source_id", "data_source_id": "<from config or env>" }`
- `properties`: title, author, and category using the configured property names
- `content`: the prepared Notion enhanced markdown
- `cover`: only a plain public cover URL. If the URL is signed (token, `Expires`, `Signature`, or similar query), do not put it in chat or git. Download and attach, or omit the cover.

Fetch `notion://docs/enhanced-markdown-spec` with `notion-fetch` before writing content.

After a page exists, record it so the next run can skip:

```bash
python3 prepare.py --mark-synced BOOK_ID "Book Title" "https://www.notion.so/…"
```

## Prepare helper

[prepare.py](prepare.py) writes `prepared/<bookId>.json` plus `last_report.json`. Both are gitignored, as are `config.json` and `state.json`. Those files hold your highlights. Do not commit them.

```bash
python3 prepare.py --limit 5
python3 prepare.py --book-id BOOK_ID
python3 prepare.py --self-check
```

`--self-check` builds a synthetic page in memory. It does not call WeRead or Notion.

## Output shape

Notebook overview: title, author, total notes, review count, highlight count, bookmark count, reading progress.

One book: highlights by chapter, then ideas and reviews. Bookmarks appear as a count from `/user/notebooks` only.

Show Unix timestamps as `YYYY-MM-DD`.

## Privacy

- Sync the signed-in user's notebooks only.
- Do not commit `prepared/`, reports, or sample highlights.
- Do not paste highlight text into a public channel. Chat gets the book title and the Notion URL.
- Cover URLs that look signed are credentials.

## Do not

- Commit `WEREAD_API_KEY` or a Bearer header
- Ship a real database UUID as the default parent
- Treat popular highlights (`/book/bestbookmarks`) or public reviews as the user's notes
- Export bookmark bodies (the API does not return them)
- Nest business fields under `params`
