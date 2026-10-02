---
name: token-perf
description: >-
  Scan for free or promotional LLM credits across a user-configured vendor
  list (Claude, Codex/ChatGPT, Grok, Gemini by default). Report only new or
  changed offers from real sources. Never claim, redeem, or upgrade without
  explicit approval. Stay quiet when nothing changed.
---

# Token and promo scan

Look for **free or promotional LLM usage**: credits, token gifts, usage resets, temporary rate-limit boosts. The user configures which vendors and which plan tier they are on. Do not assume an account, a seat count, or a leftover balance.

Default vendors (edit [config.example.json](config.example.json)):

| Id | Label |
| --- | --- |
| `anthropic` | Anthropic / Claude, including Claude Code credits |
| `openai` | OpenAI / ChatGPT / Codex |
| `xai` | xAI / Grok |
| `google` | Google / Gemini |

Run on demand, or when [Routine_TokenPerf](../Routine_TokenPerf/) fires the weekday cron.

## Checklist

For each configured vendor:

1. Search the web for official help, status, pricing, and credit-announcement pages. Search X when the host has X search. Query seeds are starting points, not facts:
   - `Claude` free credits OR promotional usage
   - `ChatGPT` OR `Codex` promo credits
   - `Grok` free tokens OR rate limit
   - `Gemini` API free tier credits
   Replace the seed with the vendors in config. Prefer the vendor's own domain over a recap post.
2. Open the page you would cite. An offer counts only when the page states what it is, who qualifies, how to claim it, and any deadline.
3. Compare with `baseline.json` (copy from [baseline.example.json](baseline.example.json)). Report an item only when it is new or a field changed (eligibility, steps, deadline, or the offer disappeared).
4. Write the user-visible note as: what, who qualifies, claim steps, deadline, source URL.
5. Update `baseline.json` after the run so the next pass does not repeat the same offer. Record `open`, `expired`, or `user-declined`. Record `claimed` only after the user says they claimed it.

Soft rumors and posts that do not name a real claim path stay in the run log. They are not a user ping.

## Quiet

If nothing is new or changed versus the baseline, send no message. Do not send "no change". Do not announce that a routine fired.

## Approval

Listing an offer is the end of the run. Do not apply, redeem, buy, upgrade, switch plans, or click a claim flow unless the user approves that specific offer in a later message. Approval for one vendor is not approval for the next.

## Baseline file

`baseline.json` is local and gitignored. Shape:

```json
{
  "updated_at": null,
  "items": []
}
```

An item, once you have a real source:

| Field | Meaning |
| --- | --- |
| `id` | Stable slug, `vendor:short-name` |
| `vendor` | Id from config |
| `summary` | One line, quoted from the source |
| `who_qualifies` | Who the source says can claim |
| `claim_steps` | Steps the source publishes |
| `deadline` | Date, or null |
| `source_url` | Page you opened |
| `status` | `open`, `expired`, `user-declined`, or `claimed` |

Do not seed this file with offers you have not opened. An empty `items` array is the correct starting point.

## Do not

- Invent a credit, a code, a deadline, or a qualification
- Treat a search snippet or a repost as confirmation
- Claim or pay without an explicit yes
- Hard-code someone else's plan, balance, or account
- Ping the user when the baseline already covers the scan
