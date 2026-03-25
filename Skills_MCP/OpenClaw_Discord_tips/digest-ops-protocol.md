# Daily Digest — COO Operations Protocol

## 1. Review & Publish (Automated via Heartbeat)

**When:** Every heartbeat after 7:15 AM PST.

**Architecture:** Cron (7 AM) generates data → writes staging file. COO (heartbeat) reviews → fixes → publishes. Jing never sees raw cron output.

**How:**
1. Read staging file: `references/digest-staging.json`
2. Review against outcome checklist:
   - [ ] All 6 agents have real status (not "unknown" or "blocked")
   - [ ] **Empty memory verified:** If an agent's memory/ is empty, check `sessions_list` for recent sessions. No sessions = agent genuinely idle (not a problem to flag). Sessions exist but no memory = agent forgot to log (flag as process gap, not to Jing). Only flag to Jing if it's a real problem COO can't resolve.
   - [ ] Blockers capture real issues
   - [ ] Knowledge curation has substance
   - [ ] `self_check.gaps` addressed
3. Fix any gaps using `sessions_history()` and `sessions_list()`
4. Build Discord components v2 message from reviewed data (format: `references/daily-digest-format.md`)
5. Include feedback modal with pre-filled context
6. Post to #daily-digest
7. Delete staging file
8. Log to memory

**Key rule:** COO is the gatekeeper. The digest is only as good as COO's review.

## 2. Feedback Processing

**Trigger:** When Jing submits the feedback modal on a digest, it arrives as a user message in the COO #daily-digest session (`agent:coo:discord:channel:1466291101735452746`).

**CRITICAL ROUTING RULE:** The #daily-digest session is NOT where Jing expects conversation. Follow this flow:

**Processing steps:**
1. **Parse** the modal submission — extract rating, context_ref, and feedback text
2. **Store** in DB:
   ```sql
   INSERT INTO feedback (date, type, agent, description, source, related_goal, rating, context_ref, cron_run_id)
   VALUES ([date], 'digest_feedback', 'coo', [feedback_text], 'jing_modal', 'cron_reliability', [rating], [context_ref], [cron_run_id]);
   ```
3. **Reply briefly in #daily-digest:** ONLY say "✅ Feedback logged: [rating]. Processing in #coo." — nothing more. No diagnosis, no fixes, no long responses.
4. **Forward to #coo:** Use `message(action="send", channel="discord", target="1466002014394646707")` to post:
   - Jing's feedback (rating + text)
   - Your diagnosis of the issue
   - What you're fixing
   - Confirmation when done
5. **Act based on rating:**
   - **good:** Log ✅ in #coo. No further action.
   - **needs_work:** Diagnose + fix cron prompt or format reference. Post explanation to #coo.
   - **useless:** URGENT. Fix immediately. Post full explanation to #coo.

**Key rule:** #daily-digest = digests only. #coo = conversations with Jing. Never mix them.

## 3. Trend Tracking

**When:** Every Tuesday and Friday (the twice-weekly COO ↔ Jing review cadence).

**How:**
1. Query feedback trends:
   ```sql
   SELECT date, rating, description 
   FROM feedback 
   WHERE type = 'digest_feedback' 
   ORDER BY date DESC 
   LIMIT 14;
   ```
2. Look for patterns:
   - **3+ consecutive "needs_work"** → systemic issue, not one-off. Escalate to Jing with root cause analysis.
   - **Any "useless"** → should already be fixed, but verify the fix landed.
   - **Repeated same feedback** → the previous fix didn't work. Try a different approach.
   - **All "good" for 7+ days** → system is stable. Consider reducing COO oversight frequency.
3. Generate a trend summary:
   - Digest quality score: % of "good" ratings over last 7 days
   - Top recurring issue (if any)
   - Fixes applied this week
   - Recommendation: maintain/adjust/overhaul
4. Include in the Tuesday/Friday review post to #coo.

**Escalation rules:**
- 3+ needs_work in a row → post alert to #coo before next review
- Any useless → immediate fix + alert
- Same feedback text appears twice → previous fix failed, escalate

## DB Schema Reference
```sql
-- Digest feedback fields
feedback.rating     -- 'good' | 'needs_work' | 'useless'
feedback.context_ref -- 'digest|2026-03-07|cron:3a05c178...|session:abc123'
feedback.cron_run_id -- extracted cron run ID for traceability
feedback.type        -- 'digest_feedback' for modal submissions
feedback.source      -- 'jing_modal' for feedback button submissions
```
