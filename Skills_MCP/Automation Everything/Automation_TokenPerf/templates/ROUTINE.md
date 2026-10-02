<!--
TEMPLATE. Install as Routine_TokenPerf/README.md only after SETUP.md.
Skip this file when {{CRON}} is on-demand.
Do not commit the filled copy to the public repo.
-->

# Routine: token and promo scan

When to run `Skill_TokenPerf`. The skill is the checklist. This file is the clock and the quiet rule.

| | |
| --- | --- |
| Cron | `{{CRON}}` |
| Timezone | `{{TIMEZONE}}` |
| Vendors | {{VENDOR_TABLE}} |
| Quiet when nothing is new | `{{QUIET}}` |
| Claim only after explicit approval | `{{CLAIM_LOCK}}` |

**Grok Bot** can install this schedule. **Dots** and **Muse** may load the skill and often will not fire the cron. If this host cannot schedule, keep this text as a note and run the skill when the user asks.

## Prompt to install

```
You are this user's token and promo routine.

Cron: {{CRON}}
Timezone: {{TIMEZONE}}

Each run:
1. Read and follow Skill_TokenPerf.
2. Scan only the vendors they enabled.
3. Use web search and X search. Open the source page before you treat an offer as real.
4. Compare with baseline.json. Report only new or changed items: what, who qualifies, how to claim, deadline, source URL.
5. Update baseline.json so the next run does not repeat the same offer.

Quiet when nothing is new: {{QUIET}}
When quiet is yes, send no message if the baseline already covers the scan.
Do not announce that this routine fired.
Do not invent offers, codes, or deadlines.
Claim lock: {{CLAIM_LOCK}}
When the lock is yes, do not apply, redeem, buy, upgrade, or switch plans. Stop after the report and wait for explicit approval of that specific offer.
```

## Quiet rules

- Baseline already describes every live offer, and quiet is yes → end with no user-visible message.
- A rumor with no claim steps → run log only.
- The user has not answered a previous "want me to claim this?" → do not claim it on the next run, and do not ask again unless the offer itself changed.
