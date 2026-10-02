# Skill: token and promo scan

Scan checklist for free or promotional LLM credits across the providers you list. The skill reports new or changed claim steps. It does not redeem them.

Unattended weekday runs live in [Routine_TokenPerf](../Routine_TokenPerf/).

Agent contract: [SKILL.md](SKILL.md).

## Configure

```bash
cp config.example.json config.json
cp baseline.example.json baseline.json
```

Set each vendor's `plan_tier` to the plan you actually pay for. `baseline.json` is the memory of offers you already know. Both files stay local (`config.json` and `baseline.json` are gitignored; the examples are safe to commit).
