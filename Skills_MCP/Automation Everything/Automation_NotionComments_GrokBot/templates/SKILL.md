---
name: Notion comment follow-up
description: >-
  Reply in a Notion discussion thread on the pages this user named. Leading
  tag is the prefix they chose. Page mentions use a dashed UUID in rich_text.
---

<!--
TEMPLATE. Replace every {{TOKEN}} from Automation_NotionComments_GrokBot/SETUP.md.
Write the filled file to the user's Skill_NotionComments_GrokBot.
Do not commit their page ids back to the public repo.
-->

# Notion comment follow-up

People ask in **Notion comments**. Reply in the discussion thread.

| | |
| --- | --- |
| Bot prefix | `{{BOT_TAG}}` |
| Watch | {{WATCH_SCOPE}} |
| Wake | `{{WAKE_MODE}}` |
| Long-form parent | `{{PARENT_ID}}` |

`YOUR_PARENT_DATA_SOURCE_ID` means the parent is unset. Do not send that string to Notion. A comment reply does not need it.

## When this applies

- An unresolved question on a page in the watch scope.
- The user asks to follow up their Notion comments.
- `Routine_NotionComments_GrokBot` woke you (`{{WAKE_MODE}}`).

## Standing rules

1. Start every bot Notion reply with `{{BOT_TAG}}`. It is the first characters of the comment text.
2. Reply in the Notion discussion thread. Chat may add one line and the Notion URL.
3. When the answer is long enough to sit and read, create or update a page under `{{PARENT_ID}}` when that id is real, then mention that page in the comment.
4. Use sources you actually fetched. If it is too early to know, say so.
5. Keep private page content inside Notion.

## How to find comments

1. `notion-fetch` the page. Pass `include_discussions: true` when you need the thread list.
2. `notion-get-comments` with `page_id` and `include_all_blocks: true`. Pass `include_resolved` only for closed threads.
3. Unresolved questions are work. A short acknowledgment gets a short in-thread note.

## How to reply in-thread

`notion-create-comment` with `page_id`, `discussion_id` (`discussion://…`), and `rich_text`. The first text run is the bot prefix.

### Page mentions

Put the page id in `rich_text` as a mention. Use the **dashed UUID** (8-4-4-4-12).

A full `https://app.notion.com/p/...` URL inside `<mention-page url="…">` makes the connector prefix the URL twice.

```json
{
  "page_id": "<page-with-the-comment>",
  "discussion_id": "discussion://<thread-id>",
  "rich_text": [
    { "type": "text", "text": { "content": "{{BOT_TAG}} Filed: " } },
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

The UUID in the sample is a shape, not a workspace. Compact ids need dashes: `aaaaaaaabbbbccccddddeeeeeeeeeeee` → `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee`. After posting, fetch the discussion and confirm the mention URL is a single `https://app.notion.com/p/<id>`.

## Optional long-form page

Skip this unless the answer is too long for the thread and `{{PARENT_ID}}` is a real id.

`notion-create-pages` or `notion-update-page`:

- `parent`: `{ "type": "data_source_id", "data_source_id": "{{PARENT_ID}}" }`
- Properties that exist on their database.
- Body in native Notion blocks.

Fetch `notion://docs/enhanced-markdown-spec` with `notion-fetch` before enhanced markdown.

## Quiet

If the routine invoked you and there is no unanswered question in scope, stop. Do not post "no comments", and do not announce that a routine fired.

## Do not

- Leave the only answer in chat
- Reply in Notion without `{{BOT_TAG}}`
- Paste a bare URL when a page mention works
- Put a full Notion URL inside `<mention-page url="…">`
- Invent claims
- Paste private page content into a public channel
- Watch a database they did not name
