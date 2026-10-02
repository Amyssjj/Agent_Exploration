# Routine: weekday token and promo scan

When to run [Skill_TokenPerf](../Skill_TokenPerf/). This folder is a cron and a quiet rule. The skill is the scan checklist.

Grok Bot can install this. Dots and Muse may load the skill and still skip the schedule; on those hosts, run the skill when someone asks.

| | |
| --- | --- |
| Example cron | `39 8 * * 1-5` |
| Timezone | `America/Los_Angeles` |
| Skill | `Skill_TokenPerf` |
| Quiet | No message when nothing is new versus `baseline.json` |
| Approval | Never claim, redeem, buy, or upgrade without an explicit yes |

Move the minute and hour if you want a different morning. Keep it on weekdays unless you decide otherwise. The vendor list and plan tier live in the skill's `config.json`, not here.

## Prompt to install

```
You are the weekday token and promo routine.

Cron: 39 8 * * 1-5
Timezone: America/Los_Angeles

Each run:
1. Read and follow Skill_TokenPerf.
2. Scan only the vendors in the user's config (default Claude, Codex/ChatGPT, Grok, Gemini).
3. Use web search and X search. Open the source page before you treat an offer as real.
4. Compare with baseline.json. Report only new or changed items: what, who qualifies, how to claim, deadline, source URL.
5. Update baseline.json so the next run does not repeat the same offer.

Stay quiet when nothing is new or changed versus the baseline.
Do not send a "no change" message.
Do not announce that this routine fired.
Do not invent offers, codes, or deadlines.
Do not apply, redeem, buy, upgrade, or switch plans. Stop after the report and wait for explicit approval.
```

## Quiet rules

- Baseline already describes every live offer → end with no user-visible message.
- A rumor with no claim steps → run log only.
- The user has not answered a previous "want me to claim this?" → do not claim it on the next morning's run, and do not ask again unless the offer itself changed.
