---
name: Notion comment follow-up
description: >-
  Reply in a Notion discussion thread when someone leaves a question on a page.
  Leading bot tag is configurable (example default [Bot]). Page mentions use a
  dashed UUID in rich_text. No workspace database id is required.
---

# Notion comment follow-up

People ask in **Notion comments**. An answer that exists only in chat makes them copy-paste. Reply in the discussion thread.

This skill is host-agnostic. The example bot tag is `[Bot]`. Change it in `config.json` so readers can tell your replies from theirs. One tag per workspace, used by every agent on every thread you answer.

## When this applies

- A page the user cares about has an unresolved comment or question.
- Someone asks in chat to follow up their Notion comments.
- [Routine_NotionComments_GrokBot](../Routine_NotionComments_GrokBot/) woke you on `comment.created` or the weekday backup poll.

No database id is required to find or answer a comment. You need the page id that holds the thread.

## Standing rules

1. Start every bot Notion reply with the configured tag. Default example: `[Bot]`. It is the first characters of the comment text. Example: `[Bot] Filed the notes on the page linked above.`
2. Reply in the Notion discussion thread. Chat may add a one-line pointer and the Notion URL. Chat alone is not the answer.
3. When the answer is long enough to sit and read, create or update a Notion page under the user's configured parent, then mention that page in the comment so the chip is clickable.
4. Use real sources already on the page or that you fetched. If it is too early to know, say it is too early.
5. Keep private page content inside Notion. Do not paste it into a public channel.

## How to find comments

1. `notion-fetch` the page. Pass `include_discussions: true` when you need the thread list on the page payload.
2. `notion-get-comments` with `page_id` and `include_all_blocks: true`. Pass `include_resolved` only when you need closed threads.
3. Unresolved questions are work. A short acknowledgment gets a short in-thread note. A research question gets a real follow-up.

## How to reply in-thread

`notion-create-comment` with:

- `page_id` of the page that has the comment
- `discussion_id` of the existing thread (`discussion://…`)
- `rich_text` whose first text run is the bot tag, then the answer, then a page mention when you are linking a page

### Page mentions

Put the page id in `rich_text` as a mention. Use the **dashed UUID**.

A full `https://app.notion.com/p/...` URL inside markdown `<mention-page url="…">` makes the connector prefix the URL twice. The chip then points at `/p/https://app.notion.com/p/...`.

```json
{
  "page_id": "<page-with-the-comment>",
  "discussion_id": "discussion://<thread-id>",
  "rich_text": [
    { "type": "text", "text": { "content": "[Bot] Filed: " } },
    {
      "type": "mention",
      "mention": {
        "type": "page",
        "page": { "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" }
      }
    },
    { "type": "text", "text": { "content": " — one line on what the page covers." } }
  ]
}
```

Replace the tag if `config.json` sets another `bot_tag`. Replace both ids with the real page and a real answer page. The UUID in the sample is a shape example, not a workspace.

Compact ids from Notion URLs need dashes before you mention them:

`aaaaaaaabbbbccccddddeeeeeeeeeeee` → `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee`

(8-4-4-4-12). After posting, fetch the discussion again and confirm the mention URL is a single `https://app.notion.com/p/<id>`.

## Optional long-form page

Skip this unless the answer is too long for the thread. Parent and property names come from the user.

```json
{
  "bot_tag": "[Bot]",
  "NOTION_PARENT_DATA_SOURCE_ID": "YOUR_PARENT_DATA_SOURCE_ID"
}
```

`YOUR_PARENT_DATA_SOURCE_ID` means "not configured". Do not send that placeholder to Notion.

When a parent is set, `notion-create-pages` (or `notion-update-page` when you already filed one) with:

- `parent`: `{ "type": "data_source_id", "data_source_id": "<the user's id>" }`
- Properties that exist on **their** database. A typical title property is enough. Add date or status only when those properties exist.
- Body in native Notion blocks: thesis, mechanism, evidence, sources, holes.

Fetch `notion://docs/enhanced-markdown-spec` with `notion-fetch` before you write enhanced markdown.

## Quiet

If the routine invoked you and there is no unanswered question, stop. Do not post "no comments", and do not announce that a routine fired.

## Do not

- Leave the only answer in chat
- Reply in Notion without the leading bot tag
- Paste a bare URL when a page mention works
- Put a full Notion URL inside `<mention-page url="…">`
- Invent claims, or dump HTML or PDF as the reading surface
- Paste private page content into a public channel
- Require a database id to answer a comment
