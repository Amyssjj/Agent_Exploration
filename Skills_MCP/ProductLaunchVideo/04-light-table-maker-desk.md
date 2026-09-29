<inputs>
Everything is pulled from motusai.co. No footage, no licensed music and no voice are used, so there is nothing to ask me for except a final check of the copy.
Product: Digital Me by MotusAI (https://motusai.co/product/digital-me). The lockup is the Motus mark (motusai.co/assets/motusai-mark.svg, the ink tile #0B0B0C with white and bone strokes, with its prefers-color-scheme block stripped) at 116px, next to "Digital Me" in Newsreader 480 at 104px, #151515.
Agent icons are the site's files, unaltered: motusai.co/assets/agents/claude-code.svg (#D97757 asterisk), codex.svg (OpenAI knot, mono), openclaw.svg (red #FF4D4D gradient), hermes.svg (mono). Mono icons take currentColor: bone #F4EFE6 on dark, #0B0B0C on the light pill. Give each inlined copy's gradient ids a unique suffix.
Fonts, all SIL OFL variable woff2 from Google Fonts: Newsreader (brand voice: title, name, line, docs heads), Inter (UI, the "me" tag), JetBrains Mono 500 (terminals, code), Caveat 600 (handwriting).
Palette: desk #CDD2CB; dark room #131315; pad bezel #43404B and glow #F3F7F1; ink #0B0B0C; type #151515; bone #F4EFE6; graphite #2C2D2F; navy #243440; UI card #0E0E10 with a 2px inset #232327 line; panel #151518; line #26262A; muted #8E8E88; green #63C27A; red #E5675F; comment #7F8C85; amber #D9A55B. Paper bases (multiplied onto the desk): kraft #D9CCAE, kraft2 #CFBF9C, bone #FBF8F1, cyan #5E8FB4, sage #A9B8AC, teal #1D3841, graph #F2F4EF, form #F5F4EE.
On-screen copy, verbatim:
The note, in Caveat: "retries are idempotent" / "+ jittered." / "never naive timers."
Claude Code terminal: header "claude code", chip "digital me", then $ claude "refactor the billing retry logic", "[Digital Me] Applying architecture_design_principles", "✓ taste attached · 2 knowledge assets in context".
The diff card, headed src/billing/retry.ts: "// retries are idempotent + jittered", "// never naive timers", "− setTimeout(retryCharge, 1000)", "+ queue.retry(charge, {", "+   backoff: 'expo', key: chargeId", "+ })", and the footer "✓ 2 files changed · tests pass".
The second note: "+ retry paths carry" / "idempotency keys".
The title: "meet digital", plus the kraft tag printed "me".
OpenClaw pane (header "OpenClaw · research agent"): "morning — what happened on X overnight?", "Overnight — TL;DR", "1 Agent interop spec ships", "2 Open-weights 30B tops coding evals", "3 EU guidance window extended".
Hermes pane (header "Hermes · ops agent"): "new release is out — update my skills?", "Crafting skills", "✓ research-digest — rewritten", "✓ inbox-triage — retuned", "+ release-watch — drafted".
Pill asks: "what happened on X overnight?", "new release — update my skills?", "review PR #214".
Codex pane: "Review PR #214 — error handling", "[Digital Me] Applying code_review_checklist", then "} catch (e) {" "console.log(e)" "}". The fix: "throw new ApiError(e, {" "retryable: isTimeout(e)" "})".
Status: "Codex is reviewing…", then "Codex caught it." Steps: "taste attached", "taxonomy loaded", "pattern matched", "comment posted".
Setup: "$ npm install -g digital-me", "$ digital-me setup", "✓ detected: claude-code · codex · openclaw", "✓ wiki scaffolded · runtimes wired", "doctor green".
Montage: rows "Renewal email rewritten in your voice", "Refund reply matched to policy + tone", "PR summary using the team's conventions", "Launch notes drafted in the house style", "Standup summary in your format"; the counter 1,284 to 1,287 with "+3 today · compounding"; "> build the metrics panel for digital-me-os", "[Digital Me] applying taste 'unified-storage'", "[Digital Me] applying knowledge 'dashboard spec'", "● drafting with your taste already applied…"; "→ learning_capture", then { "type": "knowledge", "text": "retries are idempotent + jittered" } and "↳ captured · now recalled by every agent you run"; a "Digital Me" hub card listing Knowledge, Taste, Decisions, Workflows with the four agent chips; the loop apply, work, capture, distill, review.
Docs pages: "How it works", "Agents change. Your intelligence compounds." (italic), "One intelligence, every agent", "The lifecycle, in every agent", "Two commands.", "then a deterministic lifecycle", "apply → work → capture → distill → review". Dashboard: "Is the machine getting better?", "1,221 sessions", "832 entries".
Tastes stack, in Caveat: never naive timers, wrap, classify, rethrow, so-what first, version everything, sources linked, 3 bullets, prefer primary posts, post the changelog, retune thresholds, in your voice, team conventions.
Last line: "Agents change. Your intelligence compounds."
Music: an original score synthesized in numpy (tools/score.py): half-time hip-hop at 100 BPM in D minor. No voice-over.
</inputs>

<direction>
A maker's-desk film: pencil and paper becoming live software. It is shot top-down over one backlit sage light table, never slid. There is no hand: the note writes itself in pencil, and its underline flourish flicks off the card bottom-left, carrying the eye out. Paper, tools and the tag are drawn procedurally. Paper is canvas with mottle, fibers and grain, multiplied over the desk so it glows. Tools (scissors, drafting divider, letter opener, pencil) are flat SVG silhouettes, #2C3137 with a thin edge highlight. Every product moment is a dark UI card with rounded corners (30px radius) lying on the same table, rebuilt as live DOM so it stays sharp at any zoom. The camera is one 2D transform: x, y and zoom. It leaves the table only by diving into a card or the green dot, and comes back by pulling out.
Two voices. The brand speaks in Newsreader, lowercase for the title, near-black #151515. The product speaks in Inter and JetBrains Mono at 44px and up. The recipe's version numeral becomes "me": Inter 800 at 168px, navy #243440, printed on a 300x220 kraft tag. The tag lies on the cyanotype in the cold open and on the desk at top-left, completes the title, drops into the wall and hands off to the serif "me".
Color comes only from the product: green for passes and doctor, red for the bug, the agents' own icons. The UI, not the desk, carries the saturated color.
One focal point at a time. Type holds still while read, and the camera moves between reads. The music's gaps are the story's beats: the title sits in the bass drop-out, the bug in digital silence, the fix on the drop, the tastes after the hard stop.
Transitions are physical: push through the pad's bezel into overexposed white; tilt as the terminal rises; snap-zoom onto the chip; whip back to the note; the note erodes, bursts to dust and condenses into the code comment; the card rolls and slides off the top as the title drops; words peel up; dive into the card; the dim frame splits into Codex's panel; truck across the desk; fly into the green doctor dot, which is also the green dot of the first montage row; the loop's runner blooms to white, and the white is the page; a 2-frame rise to the wall; a match cut on the word "me"; the line deletes to "intelligence" and scrambles into the mark.
Holds drift about 2 to 3% zoom. The final mark is dead still.
Banned: flat full-frame cards you didn't dive into, slide layouts, cross-dissolves, generic wipes, RGB-split, lens flares, camera shake, bouncy easing, drop shadows (a light table casts none; card edges are inset lines only), desk gradients or vignettes, eyebrows, labels, captions, legal lines, any text under about 44px held on screen (wall thumbnails are blurred to shape), stock AI imagery, monogram or robot placeholder icons, and a dark-void world.
</direction>

<structure>
100 BPM, half-time. A beat is 0.6 s (18 frames at 30 fps), a bar 2.4 s. The bar 1 downbeat falls at T0 = 0.40 s, and bar n starts at 0.4 + (n-1) x 2.4. That's 23 bars, plus a 1.2 s hold. END is 56.8 s (1,704 frames). All times below live in film/timing.json, which both picture and score read.
0.00 to 0.333, cold open (10 frames): camera on the cyanotype lifecycle sheet (a white ring with 5 stations and field arcs), zoom 0.92 to 0.95. The "me" tag lies across it, with teal and form sheets, a divider and a pencil.
Bar 1, 0.333 to 2.22: a dark room (#131315), wide on the light pad, with one blank kraft card. The glow switches on with a fluorescent stutter (brightness 0.16, then 0.95 / 0.42 / 0.9 / 0.6 between 0.42 and 0.56, settling by 0.9) and creeps 3.5% in scale. From 1.94, push through the bezel (scale up 1.9, cubic in). White #FBFCF9 overexposes from 2.0 to 2.22 on 1·4, then clears from 2.24 to 2.62 onto the desk: camera (0,10) at zoom 1.12, settling to zoom 0.95 by 2.8.
2.36 to 3.6: the three handwritten lines reveal, paced by glyph width. At 3.5 to 3.72 the underline flourish draws and exits bottom-left.
4.15 to 4.62 (2·3&): tilt down-left as the Claude Code terminal (1560x520) rises 520px into place.
4.62 to 6.2, bar 3: the prompt types while the camera rides the caret at zoom 2.0, keyed every 0.21 s.
6.3 to 6.7: pull back to zoom 1.02.
6.98 to 7.24 (3·4): an 8-frame snap-zoom to zoom 3.0 on the "digital me" chip. Enter at 7.26. The status line types, and the green ring around the mark sweeps from 7.30 to 7.98 through the bar 4 downbeat.
7.88 to 8.5 (4·1&): whip back to the note (zoom 1.05), pushing to 1.3 by 8.85.
8.8 (4·3): the kraft erodes in 8px cells, edges first.
9.1: 5,200 graphite particles, sampled from the Caveat glyphs, burst toward the lens.
9.4 (4·4): they condense into the two comment lines of the dark diff card (1640x940), which scales from 0.54 to 1 over 0.32 s.
Bar 5, the diff: the rows pop in on 8ths at 10.0, 10.3 and 10.6.
10.9 (5·2&): the card goes cyanotype two-tone.
11.2 to 12.25, the passes on 16ths: token bars, negative, bars, outline, negative, plain, bars, plain. The red line is struck from 11.5 and dims at 12.1. "● ● ●" shows at 12.25. The camera eases to (60,170) at zoom 1.32.
12.4 (bar 6): "✓ 2 files changed · tests pass".
13.0: the second kraft note slides in from the upper right and writes itself.
13.25 to 13.75: pull back to the title framing at zoom 0.62. From 13.55 to 13.9 the card rolls 4.5 degrees, and from 13.88 to 13.99 it slides off the top.
13.93: "meet digital" (Newsreader 540 at 292px) drops in from staggered heights (+70 and -52px) and lands in 4 frames.
14.05: the tag glides from the desk into the name's third slot.
Bar 7, 14.8 to 17.2, bass drop-out: hold with drift. At 16.9 and 17.05 the words peel up 700px, one per 16th, and fade.
16.85 to 17.25: whip down to the agents card.
Bar 8, 17.2: the pill rises. The card and the pill switch on the downbeat (OpenClaw), at 18.1 (Hermes) and at 18.7 (Codex), each with its icon and ask.
19.85 to 20.2 (9·1&): dive to zoom 1.3.
20.2 to 20.8: the bug. The red squiggle under console.log(e) blinks on 16ths, with a red gutter bar.
20.8: dim to 58% black.
21.1 to 21.7: digital silence. "Codex is reviewing…" (Inter 560 at 104px, centered) builds a word at a time at 21.12, 21.3 and 21.47, the 112px Codex icon breathing at the beat rate and a shimmer sweeping the words.
21.7 (9·4&): a 900px panel slides in from the left. The status shrinks by half to its top-left, and the camera shifts so the live card sits right.
The steps tick on 16ths at 22.0, 22.15, 22.3 and 22.45.
22.6 (10·2): the drop. "Codex caught it.", the last dot turns green, and the fix replaces the bug with a green glow fading over 0.4 s.
23.2: the panel exits left, and the camera recenters on the card.
24.35 to 24.9 (bar 11): pull back to zoom 0.62.
25.3 to 26.15: whip-truck right across the desk, past graph, cyan, teal, form and kraft sheets, the scissors, the letter opener and the divider.
26.55: settle on the setup terminal at zoom 1.02.
26.24 to 26.66: "$ digital-me setup" types.
26.8 (bar 12, sub drops out): Enter.
26.95: detected.
27.1, 27.4 and 27.7: the Claude Code, Codex and OpenClaw icons fly in from off-card (scale 1.5 to 1, rotations of -40, 30 and 50 degrees settling to 0) and dock.
27.85: wired.
28.0: "doctor green", its dot glow growing.
28.05 to 28.3: settle on the dot at zoom 1.35, then fly into it (zoom to 60, cubic in).
Montage, as dark screen scenes (#0B0B0C):
28.3, compound: we exit the green dot of row 2 (scale 16 to 1 over 0.55 s) while the rows drift up. The counter ticks 1,285, 1,286 and 1,287 on bar 13 beats 1, 2 and 3.
31.0: the OpenClaw chat builds upward.
32.2: the Hermes chat builds sideways.
33.7: the console types.
34.6: learning_capture types.
35.8: the hub card, with the four agent chips popping 0.05 s apart and wires drawing in.
36.7: the lifecycle ring, orbiting -10 degrees and scaling 1 to 1.08, with a white runner lapping once per bar.
39.62 to 39.93: the runner blooms into a soft-edged white disc filling the frame.
39.95: cut inside the white onto the bone docs page at zoom 25, pulling out to 0.9 by 40.45 ("How it works"). Scroll down through "One intelligence, every agent" and the lifecycle strip, with keys at 41.2, 42.4, 43.6 and 44.4.
44.5 (19·2&): "Two commands." rises 1600px from below.
47.2 (20·3): the dashboard drops onto the desk (scale 1.16 to 1, rotation -5 to -1 degrees).
47.8 to 47.87 (20·4): rise in 2 frames to the wall at zoom 0.3. "digital" (Newsreader 520px) types "digi" at 47.86 and "digital" at 47.94. The tag drops in at 48.0, scale 2.4 to 1.85.
48.06 to 48.61, every 0.05 s: 12 blurred artifacts pop in around the name (the diff, the Codex fix, the note, setup, 1,287, the second note, OpenClaw, the cyanotype loop, Hermes, the terminal, a form, a teal card).
50.5: "digital" fades over 0.24 s, and the tag stays.
50.8, the hard stop: cut on the word to a bare desk. A serif "me" (160px) sits left of center, with teal, sage and form sheets and a divider at the edges.
The tastes stack: 11 Caveat cards (820x540, mixed papers, rotated up to 14 degrees) land to its right at 51.1 and 51.7, then on 8ths at 52.0, 52.3 and 52.6, then 16ths at 52.75, 52.9, 53.05 and 53.2, then 32nds at 53.28 and 53.36.
53.5 (23·1&): the stack lifts up and right, "me" lifts off, and the props slide out.
53.52 to 54.36: "Agents change. Your intelligence compounds." (Newsreader 460 at 80px, centered) types on.
Deletes on 8ths: Agents at 54.7, change. at 54.85, Your at 55.0, compounds. at 55.15. The survivors glide to stay centered.
55.3 (23·4&): "intelligence" scrambles every 0.075 s and squeezes inward.
55.7: it resolves into the Digital Me lockup, which holds dead still to 56.8.
</structure>

<build>
1. One seek-driven page, not a HyperFrames timeline: film/index.html, core.js (grid, easing, PRNG, glyph tools), props.js (procedural paper, tools, tag), ui.js (all product cards as DOM) and film.js. The stage is 1920x1080. The world is one flat div, transformed as translate(960,540) scale(z) translate(-x,-y). Screen-space layers sit on top: the prologue pad, the white, the dim, the Codex panel and status, the montage scenes and the bloom, plus a canvas for the dust. window.seek(t) computes everything from t and awaits image decodes and a rAF. There is no CSS animation and no state between frames.
2. film/timing.json holds BPM 100, BEAT 0.6, BAR 2.4, T0 0.4, FPS 30, END 56.8, every event time above, and a "fast" list of windows for motion blur. Both film.js and tools/score.py read it.
3. The camera is a keyframe list [t, x, y, zoom, roll, ease], with the zoom interpolated geometrically. There is one easing family: settle (1-(1-u)^4), out5, in, inout, and a whip curve (a gentle launch, a violent middle, a long settle). Never read the previous frame's state inside camera(t).
4. Type: await document.fonts.load for every face before measuring. Keep a handwritten line as one shaped Caveat run, read the character boxes with Ranges, and reveal it with one advancing clip-path. The serif line is laid out once and then placed as absolute glyph spans. The dust samples glyph pixels from offscreen canvases.
5. Score: tools/score.py at 48 kHz, rng seed 20260925.
The pad chord changes every bar: Dm9 (50 53 57 60 64), Bbmaj9 (46 50 53 57 60), Fmaj9 (53 57 60 64 67), Cadd9/E (52 55 60 62 67). The pads are detuned polyBLEP saws through a lowpass.
Drums: kick on 1 and the & of 3, clap on 3, 808 roots on the same hits (D, Bb, F, E) with a glide every 4th bar. Hats run on 8ths, and on 16ths from bar 10. FM e-piano stabs fall on the & of 1 and on beat 4.
The drum pickup lands on 1·4, over a bar 1 drone and a riser. In bar 7 the drums drop out and a pluck motif plays (MIDI 69 72 74 77 76 74 72). In bars 12 to 13 the sub drops (kicks at 55%, no 808). Bars 13 to 16 carry a 16th pluck arpeggio. From 39.4 to 40.0 the hats drop out.
There is silence from 21.1 until the drop at 22.6, and a riser from 21.7. The drop is a kick at 1.2, a thud and a noise burst.
At the 50.8 hard stop the drums end and pads only remain: Bbmaj9 plus F, then an F-bass Fmaj9 pad fading out.
Every UI sound (pencil, key clicks per character, whooshes, crackle, shimmer, ticks, bells at tests, doctor and resolve, paper taps per stacked card) is placed from the timing file.
Mix: a noise-tail reverb, ducking under the kicks, a 24 Hz highpass, a 0.35 s fade at the end, and a look-ahead limiter.
tools/master.py sets the level to -14 LUFS (ebur128) with a -1.25 dB oversampled limiter, then hard-zeroes 21.1 to 21.7 with 4 ms fades. Measured: -14.1 LUFS, -1.3 dBTP. Write the WAVs at full int32 scale.
6. Render with tools/render.mjs (playwright-core with Chrome for Testing, flags --disable-lcd-text --force-color-profile=srgb --font-render-hinting=none). Use a 1920x1080 viewport at deviceScaleFactor 2 and page.screenshot({scale:'device'}) for true 3840x2160.
Each frame averages subframes over 1/60 s (a 180-degree shutter at 30 fps): 5 normally, 15 inside the "fast" windows. Each image is written 15/n times so one tmix=15 serves both.
Average in linear light. Pipe the frames as image2pipe at 450 fps through format=gbrpf32le, zscale sRGB-to-linear, tmix, select every 15th frame, zscale back to sRGB, then scale=out_color_matrix=bt709:out_range=tv, format=yuv422p10le. Encode prores_ks profile 3.
Render FROM/TO segments in parallel (about 2 to 4 s per frame per process with four in parallel). The delivered cut: frames 0-259, 260-395, 396-778, 779-1185, then 1186-1199 re-rendered at MAXSUB=45 (the bloom), 1200-1273, 1274-1431, then 1432-1437 at MAXSUB=45 (the 2-frame rise), then 1438-1703. Trim with -frames:v -c copy and join with the concat demuxer.
7. tools/deliver.sh writes three files:
- a ProRes 422 HQ master with pcm_s24le 48 kHz
- a 4K mp4: libx264 slow, crf 15, high@5.1, yuv420p, BT.709 tags, AAC 320k, +faststart
- a 1080p lanczos mp4 at crf 16
The result is 3840x2160, 30 fps, 1,704 frames, 56.8 s.
8. QC: node tools/render.mjs sheet gives one still per 8th note (187 frames, 8x8 tiles). Run draft 1 for a 1080p pass with sound. Step every transition frame by frame. tools/map.mjs exports the layout for a top-down map (renders/map.png). Loading film/index.html?preview gives a scrubber driven by the score.
</build>

<gotchas>
Caveat is contextual: split into per-glyph spans, it loses the dots on its i and j. Keep each line one run and clip it.
A status line placed in the world rides the camera. Put overlays that must stay centered in a screen layer.
Every inline copy of an SVG icon needs unique gradient ids, or hiding one copy blanks the others.
A CDP Page.captureScreenshot ignores the emulated DSF and returns 1920. Use page.screenshot with scale 'device' for 4K.
zscale can't go from untagged linear RGB straight to YUV ("no path between colorspaces"). Return to sRGB in RGB first, then convert with swscale. Check that the desk still reads #CDD2CB.
A module server must send MIME types, or Chrome refuses the scripts and the page never becomes ready.
The shell is zsh, so arrays are 1-indexed. To stop a segment early, send SIGTERM to its node parent (found via lsof on the .mov) so ffmpeg finalizes the file. ProRes is intra-only, so cuts and splices are frame-exact.
A hard-edged shape growing fast, or a 2-frame snap, still steps at 15 subframes. Give the bloom a radial-gradient edge and re-render those frames at 45.
Writing 24-bit-scaled samples into int32 WAVs reads 48 dB too quiet.
Start the pull-out from white on the page's blank margin, not inside the huge headline.
A console 404 (favicon) is harmless.
Only the agents' official icon files, unaltered. Only OFL fonts. The score is original. Kimi's UI, song and typefaces belong to the reference.
</gotchas>

<start>
Confirm the copy and icons above against motusai.co, write film/timing.json, and synthesize the score first so picture and sound share one grid. Then show me the top-down desk map with the camera path and a contact sheet at every 8th note, plus a 1080p draft with sound, before starting the 4K render.
</start>
