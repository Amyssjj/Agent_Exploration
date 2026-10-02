# Setup questions

Ask these before you write `Skill_TokenPerf` or `Routine_TokenPerf`. One message is enough. Wait for the answers. Do not guess a cron, a vendor, or a plan tier.

## Required

1. **How often should the scan run?** Cron expression and timezone. Default you may offer: `39 8 * * 1-5` in `America/Los_Angeles` (weekday morning). If they want it only when they ask, they must say so. That answer means: install the skill, do not install a routine.
2. **Which vendors?** Default menu, all optional:
   - Anthropic / Claude, including Claude Code credits (`anthropic`)
   - OpenAI / ChatGPT / Codex (`openai`)
   - xAI / Grok (`xai`)
   - Google / Gemini (`google`)
   They can drop, rename, or add. For each one they keep, ask the plan tier in their own words (`set-your-plan` until they answer).
3. **Quiet when nothing is new?** The rule is yes: if `baseline.json` already covers the scan, send no message, including no "no change" ping. Confirm they want that. If they insist on a heartbeat, record that they opted out of quiet mode, and say so in the routine.
4. **Never claim without approval?** The rule is yes: do not apply, redeem, buy, upgrade, or switch plans unless they approve that specific offer in a later message. Confirm they want that lock. Do not install a skill that claims on its own.

## Record before you write

| Token | From |
| --- | --- |
| `{{CRON}}` | Question 1, or `on-demand` |
| `{{TIMEZONE}}` | Question 1 |
| `{{VENDOR_TABLE}}` | Question 2, enabled rows only |
| `{{QUIET}}` | `yes` unless they opted out |
| `{{CLAIM_LOCK}}` | `yes` |

Refuse to install while `{{CRON}}` is still `SET_AFTER_INTERVIEW` or `{{CLAIM_LOCK}}` is not `yes`.

## Install

- Skill path: `Skill_TokenPerf/SKILL.md` from [templates/SKILL.md](templates/SKILL.md).
- Routine path: `Routine_TokenPerf/README.md` from [templates/ROUTINE.md](templates/ROUTINE.md), only when `{{CRON}}` is a real cron.
- `config.json` from [templates/config.example.json](templates/config.example.json): set `cron`, `timezone`, `quiet_when_unchanged`, `claim_requires_approval`, and `enabled: true` plus `plan_tier` on the vendors they kept.
- `baseline.json` from [templates/baseline.example.json](templates/baseline.example.json). Leave `items` empty. Do not invent offers.
- Host with no scheduler: install the skill, keep the routine text in a local note, and tell them it will not fire by itself.

## Then do the work

If they asked to scan now, run the new skill once. Report only new or changed offers that you opened on a real page. Stop before any claim button.
