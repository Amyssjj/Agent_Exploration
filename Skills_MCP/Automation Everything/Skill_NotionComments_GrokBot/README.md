# Skill: Notion comment follow-up

Answer questions left in Notion discussion threads. The reply goes in the thread, with a leading bot tag and a clickable page mention when you file a longer page.

Any skill host can run this when someone asks. Unattended runs live in [Routine_NotionComments_GrokBot](../Routine_NotionComments_GrokBot/).

Agent contract: [SKILL.md](SKILL.md).

## Configure

```bash
cp config.example.json config.json
```

Set `bot_tag` (the example default is `[Bot]`). Leave the parent data source empty unless you want long answers filed as new pages. Answering a comment does not require a database id.

## Security

Comment threads and page bodies are private. Post the answer in Notion. In chat, send a one-line pointer and the Notion URL. Do not paste the page into a public channel.
