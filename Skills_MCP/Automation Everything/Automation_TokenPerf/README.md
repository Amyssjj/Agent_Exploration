# Automation: token and promo scan

Handoff for a weekday (or other) scan for free or promotional LLM credits. This folder is the interview. It is not the installed skill.

## Security & privacy

- Credentials stay in environment variables or a local secret store (`export VAR=…`). Never commit API keys, tokens, cookies, or Bearer headers.
- Do not print secrets. Mask them in status output.
- Do not paste account balances, plan invoices, or claim links that contain tokens into a public channel.
- Listing an offer is a read. Redeeming, buying, upgrading, or switching plans waits for an explicit yes.
- Vendor list, plan tier, and cron belong to the user who answered `SETUP.md`. Do not write those answers back into this repo.
- `baseline.json` stays on their machine and out of git. It can name offers they have already seen.

## What you do with this folder

1. **Interview.** Read [SETUP.md](SETUP.md) and ask every required question. You may offer the defaults in the same message. Record an answer only after they accept or replace it.
2. **Install.** Fill [templates/SKILL.md](templates/SKILL.md) and, when they named a cron, [templates/ROUTINE.md](templates/ROUTINE.md). Write `Skill_TokenPerf` and `Routine_TokenPerf` into their skill home, or into the host's native skill and routine. Copy [templates/config.example.json](templates/config.example.json) to a local `config.json` and [templates/baseline.example.json](templates/baseline.example.json) to `baseline.json`. Copy [templates/.gitignore](templates/.gitignore) so those files stay untracked.
3. **Run.** Do one scan with the new skill if they asked to run it now. Stay quiet when nothing is new. Do not claim anything on that first run.

**Grok Bot** can schedule the routine. **Dots** and **Muse** may load the skill and often will not fire the cron. Say which of those you installed.

Leave every `{{TOKEN}}` and every `SET_AFTER_INTERVIEW` value behind in this repo. The filled copies live only on the user's host.
