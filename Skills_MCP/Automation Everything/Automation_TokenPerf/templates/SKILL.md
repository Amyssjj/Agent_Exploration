---
name: token-perf
description: >-
  Scan for free or promotional LLM credits for the vendors this user confirmed.
  Report only new or changed offers from real sources. Never claim without
  approval. Stay quiet when nothing changed, unless they opted out.
---

<!--
TEMPLATE. Replace every {{TOKEN}} from Automation_TokenPerf/SETUP.md.
Write the filled file to the user's Skill_TokenPerf. Do not commit it here.
-->

# Token and promo scan

Look for **free or promotional LLM usage**: credits, token gifts, usage resets, temporary rate-limit boosts. Scan only the vendors below. Plan tier is what this user told you. Do not assume a balance.

## This user's settings

| | |
| --- | --- |
| Cron | `{{CRON}}` |
| Timezone | `{{TIMEZONE}}` |
| Quiet when nothing is new | `{{QUIET}}` |
| Claim only after explicit approval | `{{CLAIM_LOCK}}` |

### Vendors

{{VENDOR_TABLE}}

The paired routine is `Routine_TokenPerf` when `{{CRON}}` is a cron expression. When the cron cell says `on-demand`, run this skill only when asked.

## Checklist

For each enabled vendor:

1. Search the web for that vendor's help, status, pricing, and credit pages. Search X when the host has X search. Query seeds are starting points, not facts. Prefer the vendor's own domain over a recap post.
2. Open the page you would cite. An offer counts only when that page states what it is, who qualifies, how to claim it, and any deadline.
3. Compare with `baseline.json`. Report an item only when it is new or a field changed (eligibility, steps, deadline, or the offer disappeared).
4. Write the note as: what, who qualifies, claim steps, deadline, source URL.
5. Update `baseline.json` after the run. Status is `open`, `expired`, or `user-declined`. Use `claimed` only after the user says they claimed it.

Soft rumors with no claim path stay in the run log.

## Quiet

When `{{QUIET}}` is `yes` and nothing is new or changed versus the baseline, send no message. Do not send "no change". Do not announce that a routine fired.

## Approval

When `{{CLAIM_LOCK}}` is `yes`, listing an offer ends the run. Do not apply, redeem, buy, upgrade, switch plans, or click a claim flow unless the user approves that specific offer afterward. Approval for one vendor is not approval for the next.

## Baseline file

`baseline.json` is local and gitignored. Start from `baseline.example.json` with `"items": []`.

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

## Do not

- Invent a credit, a code, a deadline, or a qualification
- Treat a search snippet or a repost as confirmation
- Claim or pay without an explicit yes
- Hard-code someone else's plan, balance, or account
- Ping when the baseline already covers the scan and quiet mode is on
