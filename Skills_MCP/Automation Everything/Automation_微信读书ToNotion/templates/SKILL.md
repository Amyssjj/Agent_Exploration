---
name: weread-to-notion
description: >-
  Pull this user's WeRead notebooks through the Agent Gateway and prepare
  Notion pages under the parent they configured. Requires WEREAD_API_KEY.
---

<!--
TEMPLATE. Replace every {{TOKEN}} from Automation_微信读书ToNotion/SETUP.md.
Copy prepare.py next to the filled skill. Do not commit config.json,
prepared/, or highlight text.
-->

# 微信读书 → Notion

Turn this user's WeRead notebooks into Notion pages. Highlights (划线) and their own ideas and reviews (想法 / 书评) are the export. Bookmark positions are counts only. Other people's public reviews and popular highlights stay out.

| | |
| --- | --- |
| Parent data source | `{{PARENT_ID}}` |
| Title property | `{{TITLE_PROPERTY}}` |
| Author property | `{{AUTHOR_PROPERTY}}` |
| Category property | `{{CATEGORY_PROPERTY}}` |
| Category value | `{{CATEGORY_VALUE}}` |
| First-run limit | `{{LIMIT}}` |
| Routine | `{{CRON}}` |

`YOUR_PARENT_DATA_SOURCE_ID` means unset. Do not send it to Notion.

## Credentials

```bash
export WEREAD_API_KEY=…
```

That is the only credential. Header: `Authorization: Bearer $WEREAD_API_KEY`. If the variable is unset, stop and tell them to export it. Never print the key.

## Gateway

```
POST https://i.weread.qq.com/api/agent/gateway
Content-Type: application/json
Authorization: Bearer $WEREAD_API_KEY
```

Business fields sit on the top-level JSON object, next to `api_name` and `skill_version` (`1.0.4` unless config overrides it). Do not wrap them in `params`.

```json
{"api_name":"/user/notebooks","count":20,"skill_version":"1.0.4"}
```

Next page: `lastSort` is the last book's `sort`. If a response contains `upgrade_info`, stop and follow `upgrade_info.message`. A non-zero `errcode` is a failure. Do not dump a body that might contain a token.

## Flow

1. **Notebooks.** `/user/notebooks` with top-level `count` and `lastSort` until `hasMore` is 0.
2. **Score.** Statistical note count is `reviewCount + noteCount + bookmarkCount`. `noteCount` is the highlight count. Export highlights plus their reviews. `bookmarkCount` stays a number.
3. **Highlights.** `/book/bookmarklist` with `bookId`. `updated[]` is `markText`. `chapters[]` maps `chapterUid` to a title.
4. **Their reviews.** `/review/list/mine` with `bookid`, `synckey`, and `count`, while `hasMore` is 1. Keep items with `content` or `abstract`.
5. **Markdown.** Group highlights by chapter. Quote with `>`. Under 想法 / 书评, quote `abstract` when the idea points at a passage, then the idea text.
6. **Notion.** `notion-create-pages` under `{{PARENT_ID}}` using the property names above. This skill does not call the Notion HTTP API. Fetch `notion://docs/enhanced-markdown-spec` first. A signed cover URL is not pasted into chat; omit it or upload the file.

## Prepare helper

`prepare.py` in this skill folder writes `prepared/<bookId>.json`. Those files are gitignored.

```bash
python3 prepare.py --limit {{LIMIT}}
python3 prepare.py --book-id BOOK_ID
python3 prepare.py --self-check
python3 prepare.py --mark-synced BOOK_ID "Book Title" "https://www.notion.so/…"
```

## Privacy

Chat gets the book title and the Notion URL. Highlight text stays in Notion and in the gitignored `prepared/` files.

## Do not

- Commit `WEREAD_API_KEY` or a Bearer header
- Create a page while the parent placeholder is still in place
- Treat `/book/bestbookmarks` or public reviews as this user's notes
- Export bookmark bodies
- Nest gateway fields under `params`
