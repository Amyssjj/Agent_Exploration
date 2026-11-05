# Token Bill Audit

Paste this whole message into Claude Code, on the computer where you use it. It reads usage numbers from your local logs, never your conversation text, and nothing leaves your machine. Edit the settings first if you like.

WINDOW: last 14 days
SESSION: my most expensive session
MY GUESS:
REPORT LANGUAGE: English
OUTPUT FOLDER: ~/token-bill

(WINDOW is "last N days" or "YYYY-MM-DD to YYYY-MM-DD". SESSION is a session id or words from its title. MY GUESS is optional: before seeing any data, write what you think eats your usage, and the report will grade it.)

---

You are auditing my Claude Code usage from my local logs. Build one HTML report that shows where my usage went, explains the mechanism behind it, and prices what I could change, using my own numbers. Follow the steps in order. Don't ask me anything unless a step says to.

## Ground rules

1. **Only `token_bill.py` touches the logs.** Never open, `cat`, `grep` or `head` a `.jsonl` file yourself. Transcripts can hold secrets, and reading them burns my usage. The script reads usage counters, timestamps, flags, block types and session titles, never message text. The one exception is the Step 1 bootstrap, which looks in my newest transcripts for this message's own script and prints nothing from them.
2. **Every number in the report comes from `data.json` or is arithmetic on it.** Never estimate, and never carry over a figure from anyone else's usage. Name the unit and the denominator each time: per step, per session, share of the whole bill, share of this thread.
3. **Dollars here are API-equivalent at list price.** They are not my invoice, and on a subscription they are not my plan meter, whose formula isn't public. Say so once, near the first dollar figure.
4. **Cost is not waste.** A step's price says what it cost, not whether it was useful. Never call spending waste.
5. **Change nothing.** Write only inside OUTPUT FOLDER. Don't touch settings, run `/compact`, or edit my projects. Recommend, don't act.
6. **Tag each claim** with where it comes from, using `<span class="tag">logs</span>` (measured from my transcripts), `docs` (stated in official docs), `derived` (arithmetic from those two) or `theory` (general LLM knowledge, not Anthropic's stated internals).

## Step 1 · Put the script on disk

Run this. It copies the script out of this message and verifies its SHA-256, so you don't retype it. Change `OUT` if OUTPUT FOLDER isn't the default.

```bash
python3 - <<'PY'
import glob, hashlib, json, os
OUT = os.path.expanduser("~/token-bill")
WANT = "f6c262b7d79203ab5f4dc189e1189fc0b34c487718491a8c807be097f390edf5"
begin, end = "# === token_bill.py BEGIN ===\n", "\n# === token_bill.py END ==="
root = os.path.join(os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"), "projects")
def texts(c):
    if isinstance(c, str):
        yield c
    elif isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and isinstance(b.get("text"), str):
                yield b["text"]
for f in sorted(glob.glob(root + "/**/*.jsonl", recursive=True), key=os.path.getmtime, reverse=True)[:12]:
    with open(f, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if "token_bill.py BEGIN" not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            msg = d.get("message") if isinstance(d, dict) else None
            if not isinstance(msg, dict) or d.get("type") != "user":
                continue
            for t in texts(msg.get("content")):
                t = t.replace("\r\n", "\n")
                if begin in t and end in t:
                    code = t.split(begin, 1)[1].split(end, 1)[0] + "\n"
                    if hashlib.sha256(code.encode()).hexdigest() == WANT:
                        os.makedirs(OUT, exist_ok=True)
                        with open(os.path.join(OUT, "token_bill.py"), "w", encoding="utf-8") as o:
                            o.write(code)
                        print("OK: saved and verified", os.path.join(OUT, "token_bill.py"))
                        raise SystemExit(0)
print("NOT FOUND")
PY
```

If it prints `NOT FOUND`, use your file tool to write everything between the two marker lines at the end of this message to `token_bill.py` in OUTPUT FOLDER, exactly. It needs Python 3.8 or later (`python` on Windows) and nothing else.

## Step 2 · Measure

```bash
python3 ~/token-bill/token_bill.py --days 14 --out ~/token-bill
```

Map my settings onto the flags: `--days N`, or `--start YYYY-MM-DD --end YYYY-MM-DD`, and `--session "words"` if I named a session. It prints a digest, which is `data.json` without the chart series. Read the digest once and work from that. Then handle `checks` and `meta`:

| If | Then |
|---|---|
| `meters_add_up` or `write_kinds_add_up` is false | Stop and tell me the script found a bug. Don't write a report. |
| `meta.unpriced_replies_by_model` isn't empty | Look the prices up at https://platform.claude.com/docs/en/about-claude/pricing, add them to `PRICES`, and rerun. If you can't, report how many replies were left out. |
| `meta.prices_as_of` is over three months old | Check the same page and update `PRICES` if it changed. |
| `logs_cover_window` is false | The logs start at `meta.earliest_reply_on_disk`, because Claude Code deletes transcripts after `cleanupPeriodDays` (30 by default). State the real window. |
| `coverage_ok` is false or null | False: my numbers don't match Claude Code's recorded spend, so say that up front. Null: there was nothing to compare, so say the totals are unvalidated. |
| `replay_holds` is false | Call the cap replay rough. |
| `meta.session_asked_for_was_found` is false | Say the session wasn't found and the report used my most expensive one. |
| `meta.replies` is under 200 or `meta.sessions` under 5 | Write a short report on what exists. Say there's too little data for patterns. Keep the one-session story, and drop the sections that need many sessions. |
| REPORT LANGUAGE isn't English | Translate the values of the `L` dictionary at the top of `token_bill.py` before building, and write all prose in that language. Keep commands, field names and numbers as they are. |

## Step 3 · Work out my story before writing

The bill is `steps × price per step`. Context size sets the price of a step, and time only charges when a wait outlives the cache. Decide which of those moves the most dollars for me, and which moves apply to me. Do not assume my usage looks like anyone else's. Someone on an API key with a 5-minute cache, someone who stays under 100k of context and someone running 900k marathons need three different reports. Lead with what's biggest for me, and cut what's irrelevant.

## Step 4 · Write `body.html` in OUTPUT FOLDER

Write the page body only, addressed to me as "you". Put `{{chart:name}}` and `{{table:name}}` on their own lines, and the build step fills them from the data, so never type a chart or a data table yourself. Use plain `h1`, `h2`, `h3`, `p`, `ul`, `table`, `code`, and `<p class="note">` for captions. Aim for 1,500 to 2,500 words, in short, concrete sentences. If a section has no data, drop it and say why in one line.

**`<h1>` Your Token Bill**, then a line with the real window and the API-equivalent caption.

**1 · The bill.** `{{chart:bill}}`, then `{{table:meters}}`. State `bill.total`, then what each slice paid for. If I wrote a guess, grade it here, plainly, and say a miss teaches more than a win.

**2 · The short version.** Four to six bullets, biggest dollars first. Each one gives a number and what it means. Include anything that corrects a common belief.

**3 · One real session.** Always show one real session before any aggregate. Use `deep_dive`, and name it by `title`.
- `{{chart:anatomy}}`: what real requests cost, including the most expensive return if there was one.
- `{{chart:sawtooth}}`: context climbing and falling at each compaction, with `compacted_at`, `landed_at` and `climb_steps`.
- A step's price as base plus rent: `base_per_step` plus `rent_per_100k` for every 100k of context, then `around_compaction` to show the price before and after.
- `{{chart:running}}`: what the thread cost against its opening price held flat. The excess is `context_charge` plus `time_charge`. The opening price is a chosen baseline, so say so.

**4 · Why it works this way.** Keep it short and tagged. Explain the mechanism from the facts below, on my numbers.
- The model has no memory, so each step re-sends everything.
- The four meters. Give the `meta.top_model_prices` ratios for my main model, not anyone else's.
- What "output" really contains: `{{table:output}}`, `bill.thinking_share_of_output_tokens` (null means my logs don't record it, not that there was none), `final_replies_share_of_bill`.
- The cache is a prefix: what breaks it, and what keeps it.
- It expires: `{{chart:cliff}}`, from my logs. Say which TTL I'm on from `meta.main_ttl_1h_share_of_threads`, then what the chart shows.
- The formula: `bill = Σ(read tokens × read price + written tokens × write price + output tokens × output price)`. Check that mean read × requests × price reproduces my read line.

**5 · Where it went.** `{{table:sessions}}`, then `concentration`, then `{{table:bands}}` (dollars per 1,000 output tokens by context, split by meter). Use `drivers` for the three axes: steps, context, and returns. Report `first_2n_vs_first_n_steps` for what a twice-as-long session really costs. Below about 150k, first loads can make small contexts look expensive, so the curve can be a U.

**6 · Coming back.** Use `returns`, `time` and `moves.read_vs_rebuild`. Show `returns.worst`. Say the price depends on the size of the context, not how long I was gone. If I'm on the 1-hour TTL, add `{{table:returns}}` for what idle compaction caught and what got a full rebuild. Don't claim why. Some rebuilds may predate the feature or my Claude Code version, so call them rebuilds, not misses, unless the logs show the feature was already running.

**7 · Many steps, and subagents.** Use `per_prompt` (give the median beside the mean), then `{{table:threads}}`. If `subagents.runs` is above zero: the entry fee, `{{table:breakeven}}`, `{{table:delegation}}`, the typical run from `steps_median`, `peak_ctx_median` and `return_tokens_median`. State that the comparison assumes equal steps, and a subagent may need more. Use `{{table:attribution}}` if one skill, agent or MCP server stands out.

**8 · The moves, priced for me.** Rank by dollars for me, and put each in one line: what to do, the number, the catch. Skip any move that doesn't apply, and say why in a line.

| Move | Applies when | Number | Catch |
|---|---|---|---|
| Cap the context: `/autocompact <tokens>` | `moves.cap.recommended` isn't null, `reach_recommended` is above 0, and `floor_measured` is true or `reach_300k` is above 0 | `{{chart:cap}}`, `recommended`, `best`, `eoq`, `focus` | A replay, not a measurement. It assumes the same steps and no rework. Give `rework_steps_per_compaction_to_erase_saving`. Say the recommended cap is the highest one keeping 90% of the best saving, because every compaction loses detail. If `top4_share_of_saving` is high, say a few threads carry it. If `floor_measured` is false the landing point is assumed, so call it rough. |
| New session at stage boundaries | `moves.new_session.payback_requests` is a small number | Payback in requests | Leaves out writing the handoff and any rework. |
| `/compact` before leaving | `moves.compact_before_leaving` exists and I'm on the 1-hour TTL | `{{table:compact}}`, `upper_bound_saving` | Upper bound. It assumes I'd compacted before every return and lost nothing I needed. |
| Delegate read-heavy work | `subagents.runs` is above zero, or my main context runs large | `{{table:breakeven}}`, inline against paid | Only pays above the subagent's own start size, on jobs longer than break-even that return little. |
| Change the cache TTL | `moves.ttl.main.net_benefit_of_1h` is above 0 while I'm on 5 minutes, or the `sub` figure is above 0 | Net benefit | Set `promptCacheTtl` or `subagentPromptCacheTtl` to `1h`. A subscription within plan limits already gets 1 hour on the main thread. |

**9 · How far to trust this.** Give `coverage` and what's outside the transcripts, then these traps, each with my number where one exists:
- **Weighting:** by tokens, reads are `bill.read_share_of_tokens`. By dollars they're far less. Both are true.
- **Confounding:** long sessions are different work. Only running one task both ways removes that.
- **Heavy tails:** the mean describes a few big sessions, so name them.
- **Proxy:** dollars aren't the plan meter. `/usage` reads the same local logs, so agreement with it isn't an independent check.
- **Causation:** `$ = steps × $/step`, so anything that grows with steps correlates with dollars. Span and calendar days look important for that reason alone.

Then give me the test that would settle it: fork one real session with `claude -p "<task>" --resume <id> --fork-session`, run the same task with and without the move, warm the cache first, count everything on the cheap side (the compaction or handoff, the first reply, any rework), hold model, effort and acceptance check constant, and write down the prediction first.

**10 · Findings index.** One `<table class="idx">`, with a row per finding: the finding, its number, the mechanism, the tag, and a status of Measured, Derived, Replayed or Not established.

## Step 5 · Build and check

```bash
python3 ~/token-bill/token_bill.py --render ~/token-bill/body.html --out ~/token-bill
```

It writes `report.html` and lists any placeholder that came back empty. Remove those, or say in the text why the section is missing, and rebuild. Then check every number in sections 1, 2 and 8 against `data.json`, and fix any that don't match.

## Step 6 · Tell me

Reply in REPORT LANGUAGE, in under 120 words: the path to `report.html`, the three biggest findings with their numbers, and the one move worth trying first. Add that the report shows session titles and project names, so I should remove them before sharing it.

## Facts to explain with

Checked against official docs on 2026-11-05. Apply them to my setup. If something in my logs disagrees, trust the logs and say so.

**Requests** `docs`: Claude Code re-sends the full context on every request: system prompt, project context, every message and tool result. Each tool call ends a request, and the next one carries everything so far plus the result. Cached re-reads bill at the cache read rate.

**Why the prices sit where they do** `theory`: input is processed in one parallel pass, and output is generated one token at a time, each needing a full pass. A cache read skips the work, and a cache write does the work and holds memory. Anthropic publishes prices and behaviour, not internals.

**Output** `docs`: output tokens include thinking, tool-call arguments and text, and thinking bills as output. Thinking can't be turned off on Opus 5.5, Sonnet 5.5, Haiku 5.5 or the Fable models.

**Long context** `docs`: there's no long-context surcharge on the 1M window, except Haiku 5.5 above 100K-token prompts.

**The cache is a prefix** `docs`: the match is exact from the start of the request, and a change anywhere recomputes everything after it. *Breaks it:* switching models, compaction (by design), tool definitions changing when tools aren't deferred, upgrading Claude Code, toggling fast mode, and changing effort except on Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable 5.1 with an API key or subscription. *Keeps it:* anything appended at the end, skills, plan mode, editing repo files, `/rewind`.

**Why it's a prefix** `theory`: attention only looks backward, so each token's stored state depends on every token before it.

**Cache lifetime** `docs`: entries expire after inactivity, and each hit resets the timer. On a Claude subscription within plan usage, the main conversation gets 1 hour. With an API key, a cloud provider or usage credits it gets 5 minutes. Subagents, compaction and other side requests get 5 minutes by default. Writes cost 1.25× input at 5 minutes and 2× at 1 hour. `promptCacheTtl` and `subagentPromptCacheTtl` take `5m` or `1h`.

**Compaction** `docs`: it sends a separate summary request, which isn't in the transcripts. While the cache is warm that request reads the prefix from cache, so it's cheap. After expiry it reprocesses the history as uncached input, which is why `/compact` costs the most on an old session. Either way the next turn rebuilds only the short summary. There's a floor: after compacting, the system prompt, tools, CLAUDE.md and summary all remain, so a cap near `moves.cap.floor_ctx` compacts constantly.

**Auto-compact** `docs`: `/autocompact 300k` saves for that model and stays on for later sessions, the range is 100k to 1M, and `/autocompact auto` restores the default. Sessions on a 1M window auto-compact near 967K by default. Trust `compactions.highest_before` for what I actually hit.

**Idle compaction** `docs`: it runs for an interactive local session with auto-compact on, on the 1-hour TTL, at 200,000 tokens or more by default, after about an hour idle, if the computer stays awake. The notice starts "Compacted while idle, before the prompt cache expired". `idleCompaction: false` turns it off.

**Subagents** `docs`: a subagent is a fresh conversation with its own system prompt. Its first request doesn't read the parent's cache. A fork inherits the parent's conversation and reads its cache, so it shrinks nothing, and the saving below applies to fresh subagents only.

**Other commands** `docs`: `/clear` costs nothing and starts fresh. `/rewind` returns to a prefix that's already cached. `/usage` is approximate, computed from local history on this machine, and its rows overlap, so they can add up past 100%.

**Derived rules** `derived`:
- Within one climb between compactions, total read ≈ `c₀·N + d·N²/2`, where `c₀` is the starting context, `d` the tokens added per step, and `N` the steps. Compaction resets the climb, so never say whole-session cost is quadratic. Use my measured `first_2n_vs_first_n_steps`.
- Subagent break-even: `saving per step = (P − C₀) × read price`, and `steps = entry fee ÷ saving per step`, with `P` the main context and `C₀` the subagent's start. Below `C₀` it never pays.
- New-session payback: `entry fee ÷ (context dropped × read price)`.
- Best cap (economic order quantity): `S + √(2·c·d ÷ r)`, with `S` the floor, `c` the cost per compaction, `d` tokens per step and `r` the read price.
- A token pays once to move in, then rent until compaction removes it. That's why keeping bulky tool results out of the main thread matters more than their sticker price.

**Words to keep straight:**
- A **step** is one model reply, deduped by message id.
- **Context** is the tokens sent on that step.
- **Main** is my interactive thread, **sub** is a subagent, and **bg** is a headless or SDK run.
- A **return** is a main-thread gap at least as long as that thread's cache lifetime.
- "Context share" is everything but output, and includes new content paid for once. `bill.repeat_share` is the part that's repetition. Don't merge the two.

## The script

```python
# === token_bill.py BEGIN ===
#!/usr/bin/env python3
"""token_bill.py: where your Claude Code usage went, measured from your own local logs.

READ-ONLY. Python standard library only, no network. It reads usage counters, timestamps, flags, block
types and session titles. It never reads, stores or prints message text, tool input or tool output.

  python3 token_bill.py --days 14 --out DIR         measure: writes DIR/data.json, prints a digest
  python3 token_bill.py --render BODY --out DIR     build:   fills {{chart:x}} / {{table:x}} into DIR/report.html
"""
import argparse, collections, datetime as dt, glob, html, json, math, os, re, statistics as st, sys

PRICES_AS_OF = "2026-11-05"   # https://platform.claude.com/docs/en/about-claude/pricing
# $ per million tokens: input, 5-minute cache write, 1-hour cache write, cache read, output
PRICES = {
    "claude-fable-5-1": (10, 12.5, 20, .25, 50), "claude-mythos-5-1": (10, 12.5, 20, .25, 50),
    "claude-fable-5": (10, 12.5, 20, 1, 50), "claude-mythos-5": (10, 12.5, 20, 1, 50),
    "claude-opus-5-5": (4, 5, 8, .2, 20), "claude-opus-5": (5, 6.25, 10, .5, 25),
    "claude-opus-4-8": (5, 6.25, 10, .5, 25), "claude-opus-4-7": (5, 6.25, 10, .5, 25),
    "claude-opus-4-6": (5, 6.25, 10, .5, 25), "claude-opus-4-5": (5, 6.25, 10, .5, 25),
    "claude-opus-4-1": (15, 18.75, 30, 1.5, 75), "claude-opus-4": (15, 18.75, 30, 1.5, 75),
    "claude-sonnet-5-5": (2, 2.5, 4, .1, 10), "claude-sonnet-5": (2, 2.5, 4, .2, 10),
    "claude-sonnet-4-6": (3, 3.75, 6, .3, 15), "claude-sonnet-4-5": (3, 3.75, 6, .3, 15),
    "claude-sonnet-4": (3, 3.75, 6, .3, 15), "claude-haiku-5-5": (.1, .125, .2, .01, .5),
    "claude-haiku-5-5>100k": (.5, .625, 1, .05, 2.5), "claude-haiku-4-5": (1, 1.25, 2, .1, 5),
    "claude-haiku-3-5": (.8, 1, 1.6, .08, 4),
}
SUMMARY = 8000    # assumed tokens in a compaction summary; the summary request is not in the transcripts
DROP = 0.6        # context falling below 60% of the previous step counts as a compaction
BIG = 100_000     # one reply writing this much cache counts as a big write
GAPS = ((0, 300), (300, 1800), (1800, 3300), (3300, 3600), (3600, 3900), (3900, 7200), (7200, 1e12))
BANDS = ((0, 5e4), (5e4, 1.5e5), (1.5e5, 3e5), (3e5, 6e5), (6e5, 1e12))
CAPS = (100e3, 125e3, 150e3, 175e3, 200e3, 225e3, 250e3, 300e3, 400e3, 500e3, 600e3, 800e3)
# Every visible chart and table string. To localize the report, translate the values here.
L = dict(read="Re-read from cache", rebuilt="Rebuilt after expiry", new="New content, written once", first="First loads and post-compaction",
         output="Model output", input="Fresh input", w5="Cache write, 5-minute", w1="Cache write, 1-hour", meter="Meter", per_m="$ / million",
         tokens="Tokens", usd="$", share="Share", session="Session", steps="Steps", prompts="Prompts", ctx="Mean / peak context", per_step="$ per step",
         delegated="In subagents", span="Span / active h", returns="Returns ($)", context="Context", replies="Replies", mean_ctx="Mean context",
         mean_out="Mean output", write="Write", total="Total", per_1k="Dollars per 1,000 output tokens", reply_type="Reply type", tool_silent="Tool step, no text",
         tool_text="Tool step with text", final="Final reply", other="Other", gap="gap since the previous request", lost="share of requests that lost the cache",
         step="main-thread step", cum="running total", flat="at the opening price", saved="saved vs what you paid", cap="auto-compact cap (tokens)",
         kind="Kind", n="Count", mean_cost="Mean cost of next reply", caught="Compacted while idle", missed="Full rebuild", warm_other="Other",
         scenario="Scenario", cost="Cost", actual="What you paid, as subagents", inline="Same steps, inline", inline_rent="Inline, plus rent on what would have stayed",
         main_ctx="Main thread at", breakeven="Steps to break even", never="never", choice="Choice", one_off="One-off cost", later="Each later request reads",
         warm="Compact before leaving (warm)", cold="Return, then compact (cold)", carry="Return and carry on", move="Move", worth="Estimated saving", how="Do this",
         compactions="Compactions", req="Request", back="Back after a gap", main="Main thread", sub="Subagents", bg="Background", thread="Where", per1k="$ per 1k output",
         med_ctx="Median context", attribution="Attributed to", project="Project", model="Model", day="Day", ctx_tokens="context tokens", mins="min")


def now():
    return dt.datetime.now().astimezone()


def norm(model):
    m = re.sub(r"^.*?(claude-)", r"\1", model or "")
    return re.sub(r"(-v\d+(:\d+)?|@\d+|-\d{8}|\[.*\])+$", "", m)


def rates(r):
    name = norm(r["model"])
    if name == "claude-haiku-5-5" and r["ctx"] > 100_000:
        name += ">100k"
    p = PRICES.get(name)
    if not p:
        return None
    k = (2 if r["speed"] == "fast" else 1) * (1.1 if r["geo"] == "us" else 1) / 1e6
    return dict(zip(("input", "w5m", "w1h", "read", "output"), (x * k for x in p)))


def median(xs, default=0):
    xs = list(xs)
    return st.median(xs) if xs else default


def mean(xs, default=0):
    xs = list(xs)
    return st.mean(xs) if xs else default


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def ols(x, y):
    """Slope and 95% half-width for one regressor."""
    n, mx, my = len(x), mean(x), mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    if n < 3 or not sxx:
        return None, None
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    res = sum((c - my - b * (a - mx)) ** 2 for a, c in zip(x, y))
    return b, 1.96 * math.sqrt(res / (n - 2) / sxx)


# ---------- reading the logs ----------
def desktop_sessions():
    """CLI session id -> (title, every CLI session id in that desktop session). Desktop app only."""
    roots = ("~/Library/Application Support/Claude", os.path.join(os.environ.get("APPDATA", "~"), "Claude"), "~/.config/Claude")
    chains = {}
    for root in roots:
        for path in glob.glob(os.path.join(os.path.expanduser(root), "claude-code-sessions", "**", "local_*.json"), recursive=True):
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    d = json.load(fh)
            except (ValueError, OSError):
                continue
            ids = [i for i in [d.get("cliSessionId"), *(d.get("priorCliSessionIds") or [])] if i]
            for i in ids:
                chains[i] = (d.get("title"), ids)
    return chains


def scan(files, root):
    rows, prompts, compacts, titles, recorded = {}, collections.defaultdict(set), [], {}, {}
    keep = ('"assistant"', '"user"', "compact_boundary", "custom-title", "cost-state")
    for f in files:
        in_sub = "subagents" in f.split(os.sep)
        project = os.path.relpath(f, root).split(os.sep)[0]
        with open(f, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if not any(k in line for k in keep):
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(d, dict):
                    continue
                kind, sid = d.get("type"), d.get("sessionId")
                if kind == "custom-title":
                    titles[sid] = d.get("customTitle")
                    continue
                if kind == "cost-state":
                    recorded[sid] = max(recorded.get(sid, 0), d.get("totalCostUSD") or 0)
                    continue
                if not d.get("timestamp"):
                    continue
                t = dt.datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
                side = in_sub or bool(d.get("isSidechain"))
                if d.get("subtype") == "compact_boundary":
                    c = d.get("compactMetadata") or {}
                    compacts.append({"t": t, "session": sid, "side": side, "trigger": c.get("trigger"), "pre": c.get("preTokens"),
                                     "post": c.get("postTokens"), "precomputed": bool(c.get("precomputed"))})
                    continue
                msg = d.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                blocks = [b.get("type") for b in content if isinstance(b, dict)] if isinstance(content, list) else []
                if (kind == "user" and not side and not str(d.get("entrypoint")).startswith("sdk") and not d.get("isMeta")
                        and not d.get("isCompactSummary") and "tool_result" not in blocks):
                    prompts[sid].add((d.get("uuid"), t))
                u = msg.get("usage")
                if kind != "assistant" or not u or msg.get("model") == "<synthetic>":
                    continue
                rec = {"t": t, "session": sid, "project": project, "file": f, "model": msg.get("model"), "entry": d.get("entrypoint"),
                       "side": side, "agent": None if in_sub else d.get("agentId"), "input": u.get("input_tokens") or 0, "output": u.get("output_tokens") or 0,
                       "read": u.get("cache_read_input_tokens") or 0, "write": u.get("cache_creation_input_tokens") or 0,
                       "w1h": (u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0, "speed": u.get("speed"), "geo": u.get("inference_geo"),
                       "think": (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0, "stop": msg.get("stop_reason"),
                       "text": "text" in blocks, "tool": "tool_use" in blocks,
                       "who": ("skill: " + d["attributionSkill"]) if d.get("attributionSkill") else ("subagent: " + d["attributionAgent"]) if d.get("attributionAgent")
                       else ("mcp: " + d["attributionMcpServer"]) if d.get("attributionMcpServer") else None}
                mid = msg.get("id") or "%s:%s" % (f, d.get("uuid"))
                prev = rows.get(mid)
                if prev is None or rec["output"] >= prev["output"]:
                    if prev:
                        rec["side"] = rec["side"] or prev["side"]
                        rec["text"] = rec["text"] or prev["text"]
                        rec["tool"] = rec["tool"] or prev["tool"]
                        rec["stop"] = rec["stop"] or prev["stop"]
                    rows[mid] = rec
                else:
                    prev["text"] = prev["text"] or rec["text"]
                    prev["tool"] = prev["tool"] or rec["tool"]
                    prev["stop"] = rec["stop"] or prev["stop"]
    return list(rows.values()), prompts, compacts, titles, recorded


def price_rows(rows):
    priced, unpriced = [], collections.Counter()
    for r in rows:
        r["ctx"] = r["input"] + r["read"] + r["write"]
        p = rates(r)
        if not p:
            unpriced[r["model"]] += 1
            continue
        w1 = min(r["w1h"], r["write"])
        r["p"] = p
        r["parts"] = {"input": r["input"] * p["input"], "output": r["output"] * p["output"], "read": r["read"] * p["read"],
                      "write": w1 * p["w1h"] + (r["write"] - w1) * p["w5m"]}
        r["w_usd5"], r["w_usd1"] = (r["write"] - w1) * p["w5m"], w1 * p["w1h"]
        r["cost"] = sum(r["parts"].values())
        r["cat"] = "bg" if str(r["entry"]).startswith("sdk") else "sub" if r["side"] else "main"
        r["thread"] = (r["cat"], (r["agent"] or r["file"]) if r["cat"] == "sub" else r["session"])
        priced.append(r)
    return priced, unpriced


def rebuilt_tokens(a, b):
    """Tokens b wrote back that a already held and the cache no longer served."""
    if not b["write"] or b["ctx"] < DROP * a["ctx"]:
        return 0
    return min(b["write"], max(0, a["ctx"] - b["read"]))


def write_rate(r):
    return r["parts"]["write"] / r["write"] if r["write"] else 0


def gap(a, b):
    return (b["t"] - a["t"]).total_seconds()


# ---------- measuring ----------
def label_for(sid, titles, chains):
    return titles.get(sid) or (chains.get(sid) or (None,))[0] or (sid or "unknown")[:8]


def sessions_table(rows, prompts, threads, ttl_of, total):
    returns, return_cost = collections.Counter(), collections.Counter()
    for key, v in threads.items():
        if key[0] == "main":
            for a, b in zip(v, v[1:]):
                if gap(a, b) >= ttl_of[key]:
                    returns[b["session"]] += 1
                    return_cost[b["session"]] += b["cost"]
    by = collections.defaultdict(list)
    for r in rows:
        by[r["session"]].append(r)
    out = []
    for s, v in by.items():
        v.sort(key=lambda r: r["t"])
        times = [r["t"] for r in v]
        gaps = [(b - a).total_seconds() for a, b in zip(times, times[1:])]
        cost = sum(r["cost"] for r in v)
        out.append({"id": s, "project": v[0]["project"], "cost": cost, "steps": len(v), "prompts": len(prompts.get(s, ())),
                    "delegated": sum(r["cost"] for r in v if r["cat"] == "sub") / cost if cost else 0, "mean_ctx": mean(r["ctx"] for r in v),
                    "peak_ctx": max(r["ctx"] for r in v), "span_h": (times[-1] - times[0]).total_seconds() / 3600,
                    "active_h": sum(g for g in gaps if g < 3600) / 3600, "returns": returns[s], "return_cost": return_cost[s]})
    out.sort(key=lambda d: -d["cost"])
    return out


def write_kinds(threads):
    usd, tok, reb_cat = collections.Counter(), collections.Counter(), collections.Counter()
    for key, v in threads.items():
        for i, b in enumerate(v):
            if not b["write"]:
                continue
            rate = write_rate(b)
            if i == 0:
                parts = {"first_load": b["write"]}
            elif b["ctx"] < DROP * v[i - 1]["ctx"]:
                parts = {"post_compaction": b["write"]}
            else:
                rb = rebuilt_tokens(v[i - 1], b)
                parts = {"rebuild": rb, "new_content": b["write"] - rb}
            for k, n in parts.items():
                usd[k] += n * rate
                tok[k] += n
            reb_cat[key[0]] += parts.get("rebuild", 0) * rate
    return usd, tok, reb_cat


def cliff(threads, cat):
    out = []
    for lo, hi in GAPS:
        n = lost = 0
        for key, v in threads.items():
            if key[0] != cat:
                continue
            for a, b in zip(v, v[1:]):
                if a["ctx"] < 20_000 or b["ctx"] < DROP * a["ctx"]:
                    continue
                if lo <= gap(a, b) < hi:
                    n += 1
                    lost += b["read"] < 0.5 * a["ctx"]
        out.append({"lo_min": lo / 60, "hi_min": None if hi > 1e11 else hi / 60, "lost": lost, "n": n})
    return out


def what_time_costs(threads, total):
    cells = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for key, v in threads.items():
        for a, b in zip(v, v[1:]):
            g = gap(a, b)
            c = cells[(key[0], "under 5 min" if g < 300 else "5-60 min" if g < 3600 else "1h+")]
            c[0] += 1
            c[1] += rebuilt_tokens(a, b) * write_rate(b)
            c[2] += b["cost"]
    waiting = sum(c[1] for k, c in cells.items() if k[1] != "under 5 min")
    return {"rows": [{"thread": k[0], "gap": k[1], "gaps": c[0], "rebuild_usd": c[1], "next_reply_usd": c[2]} for k, c in sorted(cells.items())],
            "rebuilds_from_waiting_usd": waiting, "share_of_bill": waiting / total, "rebuilds_from_other_causes_usd": sum(c[1] for c in cells.values()) - waiting}


def returns_section(mains, ttl_of, rows, total):
    out, big, kinds = [], [], collections.defaultdict(list)
    for key, v in mains.items():
        for a, b in zip(v, v[1:]):
            g = gap(a, b)
            if b["write"] >= BIG:
                big.append((b, g, a))
            if g >= ttl_of[key]:
                out.append(b["cost"])
                if a["ctx"] >= 200_000:
                    k = "missed" if b["write"] >= BIG else "caught" if b["ctx"] < DROP * a["ctx"] else "other"
                    kinds[k].append((b["cost"], a["ctx"]))
    after = [(b, g) for b, g, a in big if g >= min(ttl_of.values(), default=3600)]
    avg = sum(r["cost"] for r in rows) / len(rows)
    res = {"returns": len(out), "returns_usd": sum(out), "mean_next_reply": mean(out), "mean_reply_all": avg, "big_writes": len(big), "big_writes_after_ttl": len(after),
           "big_write_mean_usd": mean(b["cost"] for b, _ in after), "times_average": (mean(b["cost"] for b, _ in after) / avg) if avg else 0,
           "at_200k_plus": {k: {"n": len(x), "mean_usd": mean(c for c, _ in x), "median_ctx": median(a for _, a in x)} for k, x in kinds.items()}}
    if big:
        b, g, a = max(big, key=lambda x: x[0]["cost"])
        res["worst"] = {"usd": b["cost"], "gap_h": g / 3600, "written": b["write"], "date": b["t"].astimezone().strftime("%Y-%m-%d"), "session": b["session"]}
    return res


def bands(rows, total):
    out = []
    for lo, hi in BANDS:
        g = [r for r in rows if lo <= r["ctx"] < hi]
        o = sum(r["output"] for r in g) / 1000
        if not g or not o:
            continue
        cost = sum(r["cost"] for r in g)
        out.append({"lo": lo, "hi": None if hi > 1e11 else hi, "replies": len(g), "mean_ctx": mean(r["ctx"] for r in g), "mean_out": 1000 * o / len(g),
                    "read": sum(r["parts"]["read"] for r in g) / o, "write": sum(r["parts"]["write"] for r in g) / o, "output": sum(r["parts"]["output"] for r in g) / o,
                    "total": cost / o, "share": cost / total, "usd_per_100": 100 * cost / len(g)})
    return out


def per_prompt(prompts, mains):
    counts, reads = [], []
    for s, items in prompts.items():
        v = mains.get(s, [])
        ts = sorted(t for _, t in items)
        for i, t0 in enumerate(ts):
            t1 = ts[i + 1] if i + 1 < len(ts) else None
            g = [r for r in v if r["t"] >= t0 and (t1 is None or r["t"] < t1)]
            counts.append(len(g))
            reads.append(sum(r["parts"]["read"] for r in g))
    steps = [r for v in mains.values() for r in v]
    return {"prompts": len(counts), "mean": mean(counts), "median": median(counts), "p90": st.quantiles(counts, n=10)[8] if len(counts) > 1 else max(counts, default=0), "max": max(counts, default=0),
            "read_usd_mean": mean(reads), "read_usd_median": median(reads), "steps_with_tools": mean(1 if r["tool"] else 0 for r in steps)}


def subagent_section(threads, mains, by_cat):
    runs = []
    for key, v in threads.items():
        if key[0] == "sub":
            runs.append({"steps": len(v), "cost": sum(r["cost"] for r in v), "first_cost": v[0]["cost"], "ctx0": v[0]["ctx"], "ctxN": v[-1]["ctx"],
                         "peak": max(r["ctx"] for r in v), "last_out": v[-1]["output"], "t0": v[0]["t"], "session": v[0]["session"], "rows": v})
    if not runs:
        return {"runs": 0}
    actual = inline = tail_total = wins = matched = 0
    for x in runs:
        v = mains.get(x["session"], [])
        before = [r for r in v if r["t"] <= x["t0"]]
        if not before:
            continue
        matched += 1
        host, c0, cf = before[-1], x["rows"][0]["ctx"], 0
        for i, r in enumerate(x["rows"]):
            grow = max(r["ctx"] - c0, 0)
            scale_w, scale_o = host["p"]["w5m"] / r["p"]["w5m"], host["p"]["output"] / r["p"]["output"]
            cf += (host["ctx"] + grow) * host["p"]["read"] + (r["parts"]["write"] * scale_w if i else 0) + r["parts"]["output"] * scale_o
        after = [r for r in v if r["t"] > x["t0"]]
        remain = 0
        for j, r in enumerate(after):
            if j and r["ctx"] < DROP * after[j - 1]["ctx"]:
                break
            remain += 1
        actual += x["cost"]
        inline += cf
        tail_total += cf + remain * max(x["ctxN"] - c0, 0) * host["p"]["read"]
        wins += cf < x["cost"]
    res = {"runs": len(runs), "usd": sum(x["cost"] for x in runs), "matched_to_main": matched, "steps_median": median(x["steps"] for x in runs),
           "mean_cost": mean(x["cost"] for x in runs), "first_reply_usd": median(x["first_cost"] for x in runs), "start_ctx": median(x["ctx0"] for x in runs),
           "peak_ctx_median": median(x["peak"] for x in runs), "return_tokens_median": median(x["last_out"] for x in runs),
           "paid": actual, "inline": inline, "inline_with_rent": tail_total, "inline_cheaper_runs": wins}
    return res


def category_table(rows):
    out = []
    for cat in ("main", "sub", "bg"):
        g = [r for r in rows if r["cat"] == cat]
        o = sum(r["output"] for r in g) / 1000
        if g and o:
            out.append({"thread": cat, "usd": sum(r["cost"] for r in g), "steps": len(g), "per_1k": sum(r["cost"] for r in g) / o, "median_ctx": median(r["ctx"] for r in g)})
    return out


def compaction_stats(mains):
    pairs = [(a, b) for v in mains.values() for a, b in zip(v, v[1:]) if b["ctx"] < DROP * a["ctx"]]
    climbs = [b["ctx"] - a["ctx"] for v in mains.values() for a, b in zip(v, v[1:]) if b["ctx"] >= DROP * a["ctx"] and b["ctx"] > a["ctx"]]
    return pairs, climbs


def replay(v, cap, floor, back, ttl):
    """One main thread re-priced as if it had compacted at cap, landing on floor. Same steps, no rework."""
    spent, held, n = v[0]["cost"], v[0]["ctx"], 0
    for a, b in zip(v, v[1:]):
        p = b["p"]
        wr = p["w1h"] if ttl >= 3600 else p["w5m"]
        dropped = b["ctx"] < DROP * a["ctx"]
        added = 0 if dropped else max(b["ctx"] - a["ctx"], 0)
        rate = write_rate(b) or wr
        if not dropped and b["read"] < 0.5 * a["ctx"]:
            spent += (held + added) * rate
        else:
            spent += held * p["read"] + added * rate
        spent += b["parts"]["output"]
        held += added
        if held > cap and cap > floor:
            spent += held * p["read"] + SUMMARY * p["output"] + back * wr + (floor - back) * p["read"]
            held, n = floor, n + 1
    return spent, n


def cap_section(mains, ttl_of, total, focus_key):
    real_all = sum(r["cost"] for v in mains.values() for r in v)
    if not real_all:
        return {"applies": False}
    pairs, climbs = compaction_stats(mains)
    peak = max(r["ctx"] for v in mains.values() for r in v)
    measured = bool(pairs)
    floor = median((b["ctx"] for a, b in pairs), 0) or median(v[0]["ctx"] for v in mains.values()) + SUMMARY
    back = median((b["write"] for a, b in pairs), 0) or 0.6 * floor
    caps = [c for c in CAPS if floor < c < peak]
    ttl = {k[1]: t for k, t in ttl_of.items()}
    res = {"applies": bool(caps), "peak_ctx": peak, "floor_ctx": floor, "write_back": back, "floor_measured": measured, "compactions_seen": len(pairs),
           "reach_300k": sum(max(r["ctx"] for r in v) >= 3e5 for v in mains.values()), "main_threads": len(mains), "main_usd": real_all}
    if not caps:
        return res
    curve = []
    for cap in caps:
        runs = [replay(v, cap, floor, back, ttl[s]) for s, v in mains.items()]
        spent, n = sum(x[0] for x in runs), sum(x[1] for x in runs)
        curve.append({"cap": cap, "usd": spent, "saved_main": (real_all - spent) / real_all, "saved_bill": (real_all - spent) / total, "compactions": n})
    best = max(curve, key=lambda c: c["saved_bill"])
    good = [c for c in curve if c["saved_bill"] >= .9 * best["saved_bill"]] if best["saved_bill"] > 0 else []
    res.update(curve=curve, best=best, recommended=max(good, key=lambda c: c["cap"]) if good else None)
    pick = res["recommended"]["cap"] if good else 3e5
    res["reach_recommended"] = sum(max(r["ctx"] for r in v) >= pick for v in mains.values())
    probe = max(mains.values(), key=lambda v: sum(r["cost"] for r in v))[0]["p"]
    d, wr = mean(climbs, 0), (probe["w1h"] if max(ttl.values()) >= 3600 else probe["w5m"])
    if d:
        k = 2 * floor
        for _ in range(5):
            c = SUMMARY * probe["output"] + back * wr + k * probe["read"]
            k = floor + math.sqrt(2 * c * d / probe["read"])
        res["eoq"] = {"best_cap": k, "cost_per_compaction": c, "tokens_per_step": d, "floor": floor, "read_per_m": probe["read"] * 1e6}
    if focus_key in mains:
        v = mains[focus_key]
        own = [(a, b) for a, b in zip(v, v[1:]) if b["ctx"] < DROP * a["ctx"]]
        f2, b2 = (median(b["ctx"] for a, b in own), median(b["write"] for a, b in own)) if own else (floor, back)
        real = sum(r["cost"] for r in v)
        focus = []
        for cap in caps:
            s, n = replay(v, cap, f2, b2, ttl[focus_key])
            focus.append({"cap": cap, "usd": s, "saved": (real - s) / real, "compactions": n})
        near = replay(v, .995 * max(r["ctx"] for r in v), f2, b2, ttl[focus_key])[0]
        res["focus"] = {"real_usd": real, "real_compactions": len(own), "curve": focus, "replay_vs_real_at_its_own_ceiling": near / real}
        at = next((c for c in focus if c["cap"] == pick), None)
        if at and at["compactions"]:
            res["focus"]["rework_steps_per_compaction_to_erase_saving"] = (real - at["usd"]) / (at["usd"] / len(v)) / at["compactions"]
    saved = sorted(((sum(r["cost"] for r in v) - replay(v, pick, floor, back, ttl[s])[0], sum(r["cost"] for r in v)) for s, v in mains.items()), key=lambda t: -t[1])
    whole = sum(x for x, _ in saved)
    if whole > 0:
        res["top4_share_of_saving"] = sum(x for x, _ in saved[:4]) / whole
    return res


def other_moves(mains, ttl_of, threads, subs, rows, cap, top_model):
    res, p = {}, {k: v / 1e6 for k, v in zip(("input", "w5m", "w1h", "read", "output"), PRICES.get(norm(top_model), (0, 0, 0, 0, 0)))}
    if not p["read"]:
        return res
    main_rows = [r for v in mains.values() for r in v]
    on_1h = sum(r["w1h"] for r in main_rows) >= .5 * max(1, sum(r["write"] for r in main_rows))
    wr = p["w1h"] if on_1h else p["w5m"]
    res["read_vs_rebuild"] = wr / p["read"]
    starts = [v[0] for v in mains.values() if v[0]["ctx"] < 200_000]
    if starts and main_rows:
        fee, start, avg = median(r["cost"] for r in starts), median(r["ctx"] for r in starts), mean(r["ctx"] for r in main_rows)
        saved = max(avg - start, 0) * p["read"]
        res["new_session"] = {"entry_fee": fee, "start_ctx": start, "mean_main_ctx": avg, "saved_per_request": saved, "payback_requests": fee / saved if saved else None}
    floor = cap.get("floor_ctx") or 0
    leaving = [(a, b) for k, v in mains.items() for a, b in zip(v, v[1:]) if gap(a, b) >= ttl_of[k] and b["write"] >= BIG and b["ctx"] >= DROP * a["ctx"]]
    if leaving:
        size = max(a["ctx"] for a, b in leaving)
        warm, cold, later = size * p["read"] + SUMMARY * p["output"], size * p["input"] + SUMMARY * p["output"], floor * p["read"]
        back = floor * wr
        saving = sum(max(b["cost"] - (a["ctx"] * p["read"] + SUMMARY * p["output"] + back), 0) for a, b in leaving)
        res["compact_before_leaving"] = {"size": size, "warm": warm, "cold": cold, "carry_on": size * wr, "later_compacted": later, "later_carry": size * p["read"],
                                         "rebuilt_returns": len(leaving), "paid": sum(b["cost"] for a, b in leaving), "upper_bound_saving": saving}
    if subs.get("runs"):
        fee, c0, table = subs["first_reply_usd"], subs["start_ctx"], []
        for size in (1e5, 2e5, 3e5, 4e5, 6e5):
            table.append({"main_ctx": size, "steps": math.ceil(fee / ((size - c0) * p["read"])) if size > c0 else None})
        res["delegate"] = {"entry_fee": fee, "start_ctx": c0, "table": table}
    ttl = {}
    for cat in ("main", "sub"):
        avoid = spared = 0
        g = [v for k, v in threads.items() if k[0] == cat]
        for v in g:
            for a, b in zip(v, v[1:]):
                if 300 <= gap(a, b) < 3600 and b["ctx"] >= DROP * a["ctx"]:
                    avoid += a["ctx"] * (b["p"]["w5m"] - b["p"]["read"])
                    spared += rebuilt_tokens(a, b) * (b["p"]["w1h"] - b["p"]["w5m"])
        premium = sum(r["write"] * (r["p"]["w1h"] - r["p"]["w5m"]) for v in g for r in v) - spared
        share = sum(r["w1h"] for v in g for r in v) / max(1, sum(r["write"] for v in g for r in v))
        ttl[cat] = {"share_1h": share, "rebuilds_a_1h_ttl_avoids": avoid, "premium_of_1h_ttl": premium, "net_benefit_of_1h": avoid - premium}
    res["ttl"] = ttl
    return res


def drivers(sessions, mains):
    res = {}
    g = [d for d in sessions if d["steps"] >= 5 and d["cost"] > 0]
    if len(g) >= 8:
        cost, steps = [math.log(d["cost"]) for d in g], [math.log(d["steps"]) for d in g]
        b, _ = ols(cost, steps)
        mc, ms = mean(cost), mean(steps)
        res["steps_share_of_cost_variance"] = sum((x - ms) * (y - mc) for x, y in zip(steps, cost)) / sum((y - mc) ** 2 for y in cost)
        res["sessions_in_that"] = len(g)
    g = [d for d in sessions if d["steps"] >= 50 and d["mean_ctx"] > 0]
    if len(g) >= 8:
        b, h = ols([math.log(d["mean_ctx"]) for d in g], [math.log(d["cost"] / d["steps"]) for d in g])
        res["doubling_context_raises_step_price"] = {"pct": 100 * (2 ** b - 1), "low": 100 * (2 ** (b - h) - 1), "high": 100 * (2 ** (b + h) - 1), "sessions": len(g)}
    q = []
    for v in mains.values():
        if len(v) >= 100:
            n = len(v) // 4
            f, l = v[:n], v[-n:]
            q.append((sum(r["cost"] for r in f) / n, sum(r["cost"] for r in l) / n, mean(r["ctx"] for r in f), mean(r["ctx"] for r in l)))
    if q:
        res["same_session_last_vs_first_quarter"] = {"threads": len(q), "dearer": sum(x[1] > x[0] for x in q), "step_price_ratio": median(x[1] / x[0] for x in q if x[0]),
                                                     "context_ratio": median(x[3] / x[2] for x in q if x[2])}
    dbl = []
    for n in (25, 50, 100, 200):
        x = [sum(r["cost"] for r in v[:2 * n]) / sum(r["cost"] for r in v[:n]) for v in mains.values() if len(v) >= 2 * n and sum(r["cost"] for r in v[:n])]
        if x:
            dbl.append({"n": n, "threads": len(x), "cost_ratio": median(x)})
    res["first_2n_vs_first_n_steps"] = dbl
    return res


def deep_dive(key, v, sessions, titles, chains, ttl):
    n, cost = len(v), [r["cost"] for r in v]
    total, rent = sum(cost), sum(r["parts"]["read"] for r in v)
    big = sum(r["parts"]["write"] for r in v if r["write"] >= BIG)
    drops = [i for i in range(1, n) if v[i]["ctx"] < DROP * v[i - 1]["ctx"]]
    returns = [i for i in range(1, n) if gap(v[i - 1], v[i]) >= ttl]
    k = min(50, max(5, n // 5))
    opening = sum(cost[:k]) / k
    time_charge = sum(max(cost[i] - opening, 0) for i in returns)
    inc = [b["ctx"] - a["ctx"] for a, b in zip(v, v[1:]) if b["ctx"] >= DROP * a["ctx"] and b["ctx"] > a["ctx"]]
    around = []
    for d in drops:
        be = [r["cost"] for r in v[max(0, d - 20):d] if r["write"] < BIG]
        af = [r["cost"] for r in v[d + 1:d + 21] if r["write"] < BIG]
        if be and af:
            around.append({"step": d + 1, "before": mean(be), "after": mean(af)})
    keep = sorted(set(range(0, n, max(1, n // 280))) | {n - 1} | set(drops) | {max(0, d - 1) for d in drops})
    run, cum = 0, []
    for c in cost:
        run += c
        cum.append(run)
    samples = [0, 1, 2, 3] if n > 3 else list(range(n))
    ret = max(returns, key=lambda i: cost[i], default=None)
    anatomy = []
    for i in samples + ([ret] if ret is not None else []):
        a = v[i - 1] if i else None
        rb = rebuilt_tokens(a, v[i]) if a else 0
        rate = write_rate(v[i])
        anatomy.append({"step": i + 1, "back_after_h": gap(a, v[i]) / 3600 if i == ret else None, "ctx": v[i]["ctx"], "read": v[i]["parts"]["read"], "rebuilt": rb * rate,
                        "new": v[i]["parts"]["write"] - rb * rate, "output": v[i]["parts"]["output"], "total": cost[i]})
    above = sum(r["cost"] for r in v if r["ctx"] >= 3e5)
    sess = next((d for d in sessions if d["id"] == key), None)
    return {"session": key, "title": label_for(key, titles, chains), "steps": n, "usd": total, "whole_session_usd": sess["cost"] if sess else total, "read_usd": rent,
            "write_usd": sum(r["parts"]["write"] for r in v), "output_usd": sum(r["parts"]["output"] for r in v), "peak_ctx": max(r["ctx"] for r in v), "first_ctx": v[0]["ctx"],
            "mean_ctx": mean(r["ctx"] for r in v), "tokens_added_per_step": mean(inc), "compacted_at": [v[d - 1]["ctx"] for d in drops], "landed_at": [v[d]["ctx"] for d in drops],
            "climb_steps": [b - a for a, b in zip([0] + drops, drops + [n])], "share_above_300k": above / total if total else 0, "returns": len(returns),
            "returns_cost": [round(cost[i], 2) for i in returns][:20], "around_compaction": around, "base_per_step": (total - rent - big) / n,
            "rent_per_100k": rent / max(1, sum(r["ctx"] for r in v)) * 1e5, "big_writes_usd": big, "opening_steps": k, "opening_price": opening, "at_opening_price": opening * n,
            "time_charge": time_charge, "context_charge": total - opening * n - time_charge, "anatomy": anatomy,
            "series": {"step": [i + 1 for i in keep], "ctx": [v[i]["ctx"] for i in keep], "cum": [round(cum[i], 3) for i in keep]}}


def coverage(ours_by_session, recorded, chains):
    seen, pairs = set(), []
    for s, rec in recorded.items():
        if s in seen:
            continue
        ids = (chains.get(s) or (None, [s]))[1]
        seen.update(ids)
        if all(i in ours_by_session for i in ids) and max(recorded.get(i, 0) for i in ids) > 1:
            pairs.append((sum(ours_by_session[i] for i in ids), max(recorded.get(i, 0) for i in ids)))
    if not pairs:
        return {"checked": False}
    ratios = sorted(o / r for o, r in pairs)
    return {"checked": True, "sessions": len(pairs), "aggregate": sum(o for o, _ in pairs) / sum(r for _, r in pairs), "median": st.median(ratios)}


def measure(args):
    root = os.path.join(os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"), "projects")
    if args.start:
        start = dt.datetime.strptime(args.start, "%Y-%m-%d").astimezone()
        end = (dt.datetime.strptime(args.end, "%Y-%m-%d") + dt.timedelta(days=1)).astimezone() if args.end else now()
    else:
        end = now()
        start = end - dt.timedelta(days=args.days)
    allfiles = glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)
    if not allfiles:
        sys.exit("No transcripts under %s. Set CLAUDE_CONFIG_DIR if you moved them." % root)
    rows, prompts, compacts, titles, recorded = scan(allfiles, root)   # all of them: a session's recorded total spans its whole history
    rows, unpriced = price_rows(rows)
    earliest = min((r["t"] for r in rows), default=start)
    ours = collections.Counter()
    for r in rows:
        ours[r["session"]] += r["cost"]
    rows = [r for r in rows if start <= r["t"] < end]
    if not rows:
        sys.exit("No priced replies between %s and %s. Unpriced models: %s" % (start.date(), end.date(), dict(unpriced)))
    prompts = {s: {(u, t) for u, t in items if start <= t < end} for s, items in prompts.items()}
    chains = desktop_sessions()
    total = sum(r["cost"] for r in rows)
    threads = collections.defaultdict(list)
    for r in rows:
        threads[r["thread"]].append(r)
    for v in threads.values():
        v.sort(key=lambda r: r["t"])
    ttl_of = {}
    for k, v in threads.items():
        ttl_of[k] = 3600 if sum(r["w1h"] for r in v) >= .5 * max(1, sum(r["write"] for r in v)) else 300
    mains = {k[1]: v for k, v in threads.items() if k[0] == "main"}
    main_ttl = {k: t for k, t in ttl_of.items() if k[0] == "main"}
    ttl_by_session = {k[1]: t for k, t in main_ttl.items()}
    sessions = sessions_table(rows, prompts, threads, ttl_of, total)
    usd, tok, reb_cat = write_kinds(threads)
    by = {k: collections.Counter() for k in ("model", "project", "day", "who")}
    meters = collections.Counter()
    out_kind, out_n = collections.Counter(), collections.Counter()
    for r in rows:
        by["model"][r["model"]] += r["cost"]
        by["project"][r["project"]] += r["cost"]
        by["day"][r["t"].astimezone().strftime("%Y-%m-%d")] += r["cost"]
        by["who"][r["who"] or "(none)"] += r["cost"]
        for k in ("input", "output", "read"):
            meters[k + "_usd"] += r["parts"][k]
            meters[k + "_tok"] += r[k]
        meters["w5_usd"] += r["w_usd5"]
        meters["w1_usd"] += r["w_usd1"]
        meters["w1_tok"] += min(r["w1h"], r["write"])
        meters["w5_tok"] += r["write"] - min(r["w1h"], r["write"])
        meters["think_tok"] += r["think"]
        kind = "final" if r["stop"] == "end_turn" else "tool_text" if r["tool"] and r["text"] else "tool_silent" if r["tool"] else "other"
        out_kind[kind] += r["parts"]["output"]
        out_n[kind] += 1
    top_model = by["model"].most_common(1)[0][0]
    p_top = PRICES.get(norm(top_model), (0, 0, 0, 0, 0))
    costs = [d["cost"] for d in sessions]
    written = sum(usd.values())
    focus = None
    if args.session:
        q = args.session.lower()
        hits = [s for s in mains if s.startswith(args.session) or q in str(label_for(s, titles, chains)).lower()]
        focus = max(hits, key=lambda s: sum(r["cost"] for r in mains[s]), default=None)
    matched = focus is not None if args.session else None
    if focus is None and mains:
        focus = max(mains, key=lambda s: sum(r["cost"] for r in mains[s]))
    cat_tab = category_table(rows)
    subs = subagent_section(threads, mains, cat_tab)
    capd = cap_section(mains, main_ttl, total, focus)
    moves = other_moves(mains, ttl_by_session, threads, subs, rows, capd, top_model)
    cov = coverage(ours, recorded, chains)
    main_comp = [c for c in compacts if not c["side"] and start <= c["t"] < end and c["pre"]]
    shares = {"read": meters["read_usd"] / total, "rebuilt": usd["rebuild"] / total, "new": usd["new_content"] / total,
              "first": (usd["first_load"] + usd["post_compaction"]) / total, "output": meters["output_usd"] / total, "input": meters["input_usd"] / total}
    tokens_all = sum(meters[k] for k in ("input_tok", "output_tok", "read_tok", "w5_tok", "w1_tok"))
    data = {
        "meta": {"start": start.isoformat(), "end": end.isoformat(), "days": round((end - start).total_seconds() / 86400, 1), "files_read": len(allfiles), "earliest_reply_on_disk": earliest.astimezone().strftime("%Y-%m-%d"),
                 "session_asked_for_was_found": matched, "replies": len(rows), "sessions": len(sessions), "main_threads": len(mains), "prices_as_of": PRICES_AS_OF, "unpriced_replies_by_model": dict(unpriced),
                 "top_model": top_model, "top_model_share": by["model"][top_model] / total, "top_model_prices": dict(zip(("input", "w5m", "w1h", "read", "output"), p_top)),
                 "entrypoints": dict(collections.Counter(str(r["entry"]) for r in rows)), "main_ttl_1h_share_of_threads": mean(1 if t >= 3600 else 0 for t in main_ttl.values()),
                 "desktop_chains_found": len({tuple(c[1]) for c in chains.values() if len(c[1]) > 1})},
        "bill": {"total": total, "tokens": tokens_all, "meters": dict(meters), "writes_usd": dict(usd), "writes_tokens": dict(tok), "rebuild_by_thread": dict(reb_cat), "shares": shares,
                 "context_share": 1 - shares["output"], "repeat_share": shares["read"] + shares["rebuilt"], "read_share_of_tokens": meters["read_tok"] / tokens_all,
                 "thinking_share_of_output_tokens": (meters["think_tok"] / max(1, meters["output_tok"])) if meters["think_tok"] else None},
        "output_anatomy": [{"kind": k, "replies": out_n[k], "usd": v, "share": v / max(1e-9, meters["output_usd"])} for k, v in out_kind.most_common()],
        "final_replies_share_of_bill": sum(r["parts"]["output"] for r in rows if r["cat"] == "main" and r["stop"] == "end_turn") / total,
        "by_thread": cat_tab,
        "concentration": {"top1": sum(costs[:1]) / total, "top3": sum(costs[:3]) / total, "top10": sum(costs[:10]) / total, "median_session": median(costs),
                          "top_day_share": (max(by["day"].values()) / total)},
        "top_sessions": [dict(d, title=label_for(d["id"], titles, chains), share=d["cost"] / total) for d in sessions[:10]],
        "by_model": by["model"].most_common(), "by_project": by["project"].most_common(10), "by_day": sorted(by["day"].items()), "by_attribution": by["who"].most_common(12),
        "cache_cliff": {"main": cliff(threads, "main"), "sub": cliff(threads, "sub")},
        "time": what_time_costs(threads, total), "returns": returns_section(mains, ttl_by_session, rows, total) if mains else {},
        "context_bands": bands(rows, total), "per_prompt": per_prompt(prompts, mains), "subagents": subs, "drivers": drivers(sessions, mains),
        "compactions": {"main": len(main_comp), "median_before": median(c["pre"] for c in main_comp), "median_after_boundary": median(c["post"] or 0 for c in main_comp),
                        "highest_before": max([c["pre"] for c in main_comp], default=0), "auto": sum(c["trigger"] == "auto" for c in main_comp),
                        "precomputed": sum(c["precomputed"] for c in main_comp)},
        "deep_dive": deep_dive(focus, mains[focus], sessions, titles, chains, ttl_by_session[focus]) if focus else None,
        "moves": dict(moves, cap=capd),
        "coverage": cov,
    }
    if data["returns"].get("worst"):
        data["returns"]["worst"]["title"] = label_for(data["returns"]["worst"]["session"], titles, chains)
    data["checks"] = {"meters_add_up": abs(sum(meters[k] for k in ("input_usd", "output_usd", "read_usd", "w5_usd", "w1_usd")) - total) < .01,
                      "write_kinds_add_up": abs(written - meters["w5_usd"] - meters["w1_usd"]) < .01, "all_replies_priced": not unpriced,
                      "logs_cover_window": earliest <= start + dt.timedelta(days=1), "coverage_ok": (cov["median"] >= .9 and cov["aggregate"] >= .85) if cov.get("checked") else None,
                      "replay_holds": (abs(capd["focus"]["replay_vs_real_at_its_own_ceiling"] - 1) < .1) if capd.get("focus", {}).get("real_compactions") else None}
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "data.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, default=str)
    print(json.dumps(digest(data), separators=(",", ":"), default=str, ensure_ascii=False))
    return data


def digest(x):
    if isinstance(x, dict):
        return {k: digest(v) for k, v in x.items() if k != "series"}
    if isinstance(x, (list, tuple)):
        return [digest(v) for v in x]
    if isinstance(x, float):
        return round(x, 4) if abs(x) < 10 else round(x, 1)
    return x


# ---------- building the page ----------
def usd(x):
    if x is None:
        return "–"
    return "${:,.0f}".format(x) if abs(x) >= 100 else "${:,.2f}".format(x) if abs(x) >= 1 else "${:.3f}".format(x)


def tok(x):
    if x is None:
        return "–"
    return "{:.2f}B".format(x / 1e9) if x >= 1e9 else "{:.0f}M".format(x / 1e6) if x >= 1e7 else "{:.1f}M".format(x / 1e6) if x >= 1e6 else "{:.0f}k".format(x / 1e3) if x >= 1e3 else "{:.0f}".format(x)


def pc(x):
    return "{:.1f}%".format(100 * x)


def table(head, rows):
    h = "".join("<th>%s</th>" % html.escape(str(c)) for c in head)
    b = "".join("<tr>" + "".join("<td>%s</td>" % html.escape(str(c)) for c in r) + "</tr>" for r in rows)
    return '<div class="scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (h, b)


def svg(w, h, body, label):
    return '<svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>' % (w, h, html.escape(label, quote=True), "".join(body))


def txt(x, y, s, size=12, anchor="start", cls="m", weight=400):
    return '<text x="%.1f" y="%.1f" font-size="%d" text-anchor="%s" class="%s" font-weight="%d">%s</text>' % (x, y, size, anchor, cls, weight, html.escape(str(s)))


def rect(x, y, w, h, cls):
    return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" class="%s"/>' % (x, y, max(w, 0), max(h, 0), cls)


def hline(x1, y1, x2, y2, cls="rule", dash=""):
    return '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="%s"%s/>' % (x1, y1, x2, y2, cls, ' stroke-dasharray="%s"' % dash if dash else "")


def legend(y, items, w=720):
    out, x = [], 0
    for cls, label in items:
        out += [rect(x, y - 10, 11, 11, cls), txt(x + 16, y, label, 12)]
        x += 30 + 6.6 * sum(2 if ord(ch) > 0x2E80 else 1 for ch in label)
        if x > w - 120:
            x, y = 0, y + 18
    return out, y


def stacked(rows, order, label):
    """Horizontal stacked bars, one row per (name, values dict)."""
    left, width = 140, 500
    top = max(sum(v.get(k, 0) for k in order) for _, v in rows) or 1
    body, y = [], 6
    for name, vals in rows:
        body.append(txt(0, y + 17, name, 12, cls="i"))
        x = left
        for k in order:
            w = width * vals.get(k, 0) / top
            body.append(rect(x, y, w, 24, "f-" + k))
            x += w
        body.append(txt(x + 6, y + 17, usd(sum(vals.get(k, 0) for k in order)), 12, cls="i"))
        y += 34
    lg, y = legend(y + 14, [("f-" + k, L[k]) for k in order])
    return svg(720, y + 10, body + lg, label)


def chart_bill(d):
    w = d["bill"]["writes_usd"]
    m = d["bill"]["meters"]
    vals = {"read": m["read_usd"], "rebuilt": w.get("rebuild", 0), "new": w.get("new_content", 0), "first": w.get("first_load", 0) + w.get("post_compaction", 0), "output": m["output_usd"]}
    order, total, width, body, x = ("read", "rebuilt", "new", "first", "output"), d["bill"]["total"], 720, [], 0
    for k in order:
        wd = width * vals[k] / total
        body.append(rect(x, 4, wd, 46, "f-" + k))
        if wd > 60:
            body.append(txt(x + 8, 33, pc(vals[k] / total), 14, cls="on", weight=600))
        x += wd
    lg, y = legend(74, [("f-" + k, "%s %s" % (L[k], usd(vals[k]))) for k in order])
    return svg(width, y + 12, body + lg, "The bill split by what each dollar paid for")


def chart_anatomy(d):
    a = (d.get("deep_dive") or {}).get("anatomy") or []
    if not a:
        return ""
    rows = [("%s %d" % (L["req"], r["step"]) if r["back_after_h"] is None else "%s (%.1fh)" % (L["back"], r["back_after_h"]), r) for r in a]
    return stacked(rows, ("read", "rebuilt", "new", "output"), "What real requests from this session cost")


def chart_cliff(d, cat="main"):
    b = [x for x in d["cache_cliff"][cat]]
    if not sum(x["n"] for x in b):
        return ""
    W, H, left, base = 720, 300, 44, 240
    bw, body = (W - left) / len(b), []
    for pct_ in (0, 50, 100):
        y = base - 2 * pct_
        body += [hline(left, y, W, y), txt(left - 8, y + 4, "%d%%" % pct_, 11, "end")]
    for i, x in enumerate(b):
        share = x["lost"] / x["n"] if x["n"] else 0
        cx = left + bw * i + bw / 2
        body.append(rect(cx - bw * .32, base - 200 * share, bw * .64, max(200 * share, 1.5 if x["n"] else 0), "f-rebuilt" if share > .5 else "f-read"))
        body.append(txt(cx, base - 200 * share - 7, "%d / %d" % (x["lost"], x["n"]), 11, "middle", "i", 600))
        hi = x["hi_min"]
        body.append(txt(cx, base + 17, ("%.0f–%.0f" % (x["lo_min"], hi)) if hi else "%.0f+" % x["lo_min"], 11, "middle"))
    body.append(txt((W + left) / 2, base + 38, "%s (%s) · %s" % (L["gap"], L["mins"], L["lost"]), 11, "middle"))
    return svg(W, H, body, "Share of requests that lost the cache, by gap since the previous request")


def path(pts):
    return '<path d="%s" fill="none" class="line"/>' % "".join("%s%.1f %.1f" % ("L" if i else "M", x, y) for i, (x, y) in enumerate(pts))


def chart_sawtooth(d):
    s = (d.get("deep_dive") or {}).get("series")
    if not s:
        return ""
    W, left, base, H = 720, 54, 250, 300
    top, n = max(s["ctx"]) * 1.05, s["step"][-1]
    X = lambda v: left + (W - left - 8) * v / n
    Y = lambda v: base - 230 * v / top
    body = []
    step = 100e3 if top < 6e5 else 200e3 if top < 1.2e6 else 500e3
    t = 0
    while t < top:
        body += [hline(left, Y(t), W, Y(t)), txt(left - 8, Y(t) + 4, tok(t) if t else "0", 11, "end")]
        t += step
    body += [path([(X(a), Y(b)) for a, b in zip(s["step"], s["ctx"])]), txt(left, base + 18, "1", 11), txt(W - 8, base + 18, "{:,}".format(n), 11, "end"),
             txt((W + left) / 2, base + 36, "%s · %s" % (L["step"], L["ctx_tokens"]), 11, "middle")]
    return svg(W, H, body, "Context size at each step of this main thread")


def chart_running(d):
    dd = d.get("deep_dive") or {}
    s = dd.get("series")
    if not s:
        return ""
    W, left, base, H = 720, 54, 250, 300
    top, n = max(s["cum"][-1], dd["at_opening_price"]) * 1.08 or 1, s["step"][-1]
    X = lambda v: left + (W - left - 90) * v / n
    Y = lambda v: base - 230 * v / top
    body = [hline(left, base, X(n), base), hline(X(0), Y(0), X(n), Y(dd["at_opening_price"]), "dash", "6 4"), path([(X(a), Y(b)) for a, b in zip(s["step"], s["cum"])]),
            txt(X(n) + 6, Y(s["cum"][-1]) + 4, usd(s["cum"][-1]), 12, cls="i", weight=600), txt(X(n) + 6, Y(dd["at_opening_price"]) + 4, usd(dd["at_opening_price"]), 12),
            txt((X(n) + left) / 2, base + 22, "%s · %s vs %s" % (L["step"], L["cum"], L["flat"]), 11, "middle")]
    return svg(W, H, body, "Running total of this main thread against its opening price held flat")


def chart_cap(d):
    c = d["moves"]["cap"]
    if not c.get("curve"):
        return ""
    pts = [(x["cap"], 100 * x["saved_bill"], x["compactions"]) for x in c["curve"] if x["cap"] >= 1.3 * c["floor_ctx"]] or [(x["cap"], 100 * x["saved_bill"], x["compactions"]) for x in c["curve"]]
    W, left, base, H = 720, 48, 250, 300
    lo, hi = min(0, min(p[1] for p in pts)), (max(p[1] for p in pts) * 1.3) or 1
    x0, x1 = pts[0][0], pts[-1][0]
    X = lambda v: left + (W - left - 30) * (v - x0) / max(1, x1 - x0)
    Y = lambda v: base - 220 * (v - lo) / (hi - lo)
    body = [hline(left, Y(0), W, Y(0)), txt(left - 8, Y(0) + 4, "0%", 11, "end"), path([(X(p[0]), Y(p[1])) for p in pts])]
    pick = (c.get("recommended") or c["best"])["cap"]
    marks = {pts[0][0], pts[-1][0], c["best"]["cap"], pick}
    for i, p in enumerate(pts):
        body.append('<circle cx="%.1f" cy="%.1f" r="%d" class="dot"/>' % (X(p[0]), Y(p[1]), 6 if p[0] == pick else 3.5))
        if p[0] in marks:
            side = "start" if i == 0 else "end" if i == len(pts) - 1 else "middle"
            up = 30 if p[0] == c["best"]["cap"] and c["best"]["cap"] != pick else 12
            body.append(txt(X(p[0]), Y(p[1]) - up, "%s · %.1f%% · %d" % (tok(p[0]), p[1], p[2]), 11, side, "i", 600 if p[0] == pick else 400))
    body.append(txt((W + left) / 2, base + 26, "%s · %s · %s" % (L["cap"], L["saved"], L["compactions"]), 11, "middle"))
    return svg(W, H, body, "Replayed saving at each auto-compact cap")


def tables(d):
    b, m = d["bill"], d["bill"]["meters"]
    pr = d["meta"]["top_model_prices"]
    t = {"meters": table((L["meter"], L["per_m"], L["tokens"], L["usd"], L["share"]), [(L[k], pr[p], tok(m[k2 + "_tok"]), usd(m[k2 + "_usd"]), pc(m[k2 + "_usd"] / b["total"]))
                         for k, p, k2 in (("read", "read", "read"), ("w5", "w5m", "w5"), ("w1", "w1h", "w1"), ("input", "input", "input"), ("output", "output", "output"))])}
    t["output"] = table((L["reply_type"], L["replies"], L["usd"], L["share"]), [(L.get(x["kind"], x["kind"]), "{:,}".format(x["replies"]), usd(x["usd"]), pc(x["share"])) for x in d["output_anatomy"]])
    t["threads"] = table((L["thread"], L["usd"], L["steps"], L["per1k"], L["med_ctx"]), [(L[x["thread"]], usd(x["usd"]), "{:,}".format(x["steps"]), usd(x["per_1k"]), tok(x["median_ctx"])) for x in d["by_thread"]])
    t["sessions"] = table((L["session"], L["usd"], L["share"], L["delegated"], L["ctx"], L["steps"], L["per_step"], L["span"], L["returns"]),
                          [(str(s["title"])[:48], usd(s["cost"]), pc(s["share"]), "%.0f%%" % (100 * s["delegated"]), "%s / %s" % (tok(s["mean_ctx"]), tok(s["peak_ctx"])),
                            "{:,}".format(s["steps"]), usd(s["cost"] / s["steps"]), "%.0f / %.0f" % (s["span_h"], s["active_h"]), "%d (%s)" % (s["returns"], usd(s["return_cost"]))) for s in d["top_sessions"]])
    t["bands"] = table((L["context"], L["replies"], L["mean_ctx"], L["mean_out"], L["read"], L["write"], L["output"], L["total"], L["share"]),
                       [("%s–%s" % (tok(x["lo"]), tok(x["hi"])) if x["hi"] else tok(x["lo"]) + "+", "{:,}".format(x["replies"]), tok(x["mean_ctx"]), "{:,.0f}".format(x["mean_out"]), "%.3f" % x["read"],
                         "%.3f" % x["write"], "%.3f" % x["output"], "%.3f" % x["total"], pc(x["share"])) for x in d["context_bands"]])
    r = d.get("returns") or {}
    k = r.get("at_200k_plus") or {}
    t["returns"] = table((L["kind"], L["n"], L["mean_cost"], L["med_ctx"]), [(L[n], k[c]["n"], usd(k[c]["mean_usd"]), tok(k[c]["median_ctx"])) for c, n in (("caught", "caught"), ("missed", "missed"), ("other", "warm_other")) if c in k])
    s = d["subagents"]
    if s.get("runs"):
        t["delegation"] = table((L["scenario"], L["cost"]), [(L["actual"], usd(s["paid"])), (L["inline"], usd(s["inline"])), (L["inline_rent"], usd(s["inline_with_rent"]))])
    mv = d["moves"]
    if mv.get("delegate"):
        t["breakeven"] = table([L["main_ctx"]] + [tok(x["main_ctx"]) for x in mv["delegate"]["table"]], [[L["breakeven"]] + [x["steps"] if x["steps"] else L["never"] for x in mv["delegate"]["table"]]])
    c = mv.get("compact_before_leaving")
    if c:
        t["compact"] = table(("%s %s" % (L["choice"], tok(c["size"])), L["one_off"], L["later"]), [(L["warm"], usd(c["warm"]), usd(c["later_compacted"])), (L["cold"], usd(c["cold"]), usd(c["later_compacted"])), (L["carry"], usd(c["carry_on"]), usd(c["later_carry"]))])
    t["attribution"] = table((L["attribution"], L["usd"], L["share"]), [(k2, usd(v), pc(v / b["total"])) for k2, v in d["by_attribution"]])
    t["projects"] = table((L["project"], L["usd"], L["share"]), [(k2, usd(v), pc(v / b["total"])) for k2, v in d["by_project"]])
    t["models"] = table((L["model"], L["usd"], L["share"]), [(k2, usd(v), pc(v / b["total"])) for k2, v in d["by_model"]])
    return t


CSS = """:root{--bg:#fbfaf7;--ink:#1d2320;--muted:#66706b;--rule:#dcdfda;--read:#0f6e84;--rebuilt:#b9431f;--new:#c98a12;--first:#8f9a94;--output:#6a4ca3;--code:#f0efe9}
@media (prefers-color-scheme:dark){:root{--bg:#141716;--ink:#e8ebe8;--muted:#9aa39e;--rule:#333a36;--read:#35a2bd;--rebuilt:#e0663f;--new:#dfa735;--first:#74807a;--output:#9b7fd6;--code:#20252a}}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);max-width:780px;margin:0 auto;padding:36px 16px 80px;font:16px/1.65 -apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif}
h1{font-size:32px;line-height:1.2;margin:0 0 8px}h2{font-size:23px;margin:44px 0 10px}h3{font-size:17px;margin:26px 0 6px}p,li{margin:8px 0}svg{width:100%;height:auto;display:block;margin:14px 0}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13.5px;margin:14px 0}th{font:600 11px ui-monospace,Menlo,monospace;color:var(--muted);text-align:right;vertical-align:bottom;border-bottom:1px solid var(--ink);padding:6px}
td{text-align:right;padding:6px;border-bottom:1px solid var(--rule);font-variant-numeric:tabular-nums;white-space:nowrap}th:first-child,td:first-child{text-align:left;padding-left:0;white-space:normal;min-width:150px}
code,pre{font-family:ui-monospace,Menlo,monospace;font-size:13.5px;background:var(--code);border-radius:4px}code{padding:1px 5px}pre{padding:12px 14px;overflow-x:auto}.note{color:var(--muted);font-size:13.5px}
table.idx td,table.idx th{white-space:normal;text-align:left;vertical-align:top}.tag{font:600 10.5px ui-monospace,Menlo,monospace;border:1px solid var(--rule);border-radius:3px;padding:0 4px;color:var(--muted);white-space:nowrap}
svg text{fill:var(--muted)}svg text.i{fill:var(--ink)}svg text.on{fill:#fff}.rule{stroke:var(--rule);stroke-width:1}.dash{stroke:var(--muted);stroke-width:1.5}.line{stroke:var(--read);stroke-width:2;stroke-linejoin:round}.dot{fill:var(--read)}
.f-read{fill:var(--read)}.f-rebuilt{fill:var(--rebuilt)}.f-new{fill:var(--new)}.f-first{fill:var(--first)}.f-output{fill:var(--output)}"""


def render(args):
    with open(os.path.join(args.out, "data.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    with open(args.render, encoding="utf-8") as fh:
        body = fh.read()
    charts = {"bill": chart_bill, "anatomy": chart_anatomy, "cliff": chart_cliff, "cliff_sub": lambda x: chart_cliff(x, "sub"), "sawtooth": chart_sawtooth, "running": chart_running, "cap": chart_cap}
    tabs = tables(d)
    missing = []

    def fill(m):
        kind, name = m.group(1), m.group(2)
        out = charts[name](d) if kind == "chart" and name in charts else tabs.get(name, "") if kind == "table" else ""
        if not out:
            missing.append(m.group(0))
        return out

    body = re.sub(r"\{\{(chart|table):([a-z_]+)\}\}", fill, body)
    title = (re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S) or [None, "Token bill"])[1]
    page = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>%s</style></head><body>%s</body></html>' % (re.sub("<[^>]+>", "", title), CSS, body)
    dest = os.path.join(args.out, "report.html")
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote", dest, "| empty placeholders:", missing or "none")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=float, default=14)
    ap.add_argument("--start", help="YYYY-MM-DD, local time")
    ap.add_argument("--end", help="YYYY-MM-DD, local time, inclusive")
    ap.add_argument("--session", help="deep-dive this session: id prefix or words from its title")
    ap.add_argument("--out", default=os.path.expanduser("~/token-bill"))
    ap.add_argument("--render", help="path of the report body to build into report.html")
    args = ap.parse_args()
    render(args) if args.render else measure(args)


if __name__ == "__main__":
    main()
# === token_bill.py END ===
```
