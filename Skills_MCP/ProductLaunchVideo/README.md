# Product Launch Video Prompts (Claude Opus 5.5 + Claude Code)

Four prompts I ran in Claude Code with Opus 5.5. Each one produced a finished product launch film for [Digital Me](https://motusai.co/product/digital-me), with brief, storyboard, beat grid, camera, music or score, sound design, render and QC all done by the agent. None of the films uses a diffusion or video model. Every frame is code (HTML/CSS/WebGL) rendered in a headless browser, so each one is a program that computes the picture from time `t`.

Walkthrough (Chinese, 9 min): [youtu.be/c-IpbIIpzsY](https://youtu.be/c-IpbIIpzsY)

## The prompts

| File | Look | Output | Engine | Sound | You supply |
| --- | --- | --- | --- | --- | --- |
| [01-mono-cinematic-cursor.md](01-mono-cinematic-cursor.md) | Black and white, one 3D take; a cursor carries the story | 24.0 s · 1920×1080 · 30 fps | HyperFrames 0.8.77 + GSAP, analytic CSS 3D camera, spring easing | Catalog music bed (120 BPM) + SFX | Icons, 3 fonts, logo SVG, music bed, 3 SFX |
| [02-dark-kinetic-type-hands.md](02-dark-kinetic-type-hands.md) | Apple keynote-style kinetic type in a dark 3D void | 36.7 s · 3840×2160 · 24 fps | Custom `seek(t)` page, Playwright capture, 15-subframe motion blur, ProRes master | A licensed song, analysed into a beat grid (122.978 BPM) | The song (bring your own licence); the site supplies the rest |
| [03-3d-dot-oner.md](03-3d-dot-oner.md) | One dot becomes curve, ribbon, liquid, particles, type, then the logo | 15.0 s · 1920×1080 · 60 fps | HyperFrames + three.js r181, raymarched SDF liquid, 240 fps capture for motion blur | Original score synthesized in Node from the same timing file | Nothing (all from the live site) |
| [04-light-table-maker-desk.md](04-light-table-maker-desk.md) | Top-down paper-and-light-table desk; handwritten notes become live UI | 56.8 s · 3840×2160 · 30 fps | Custom `seek(t)` page, Playwright capture, linear-light motion blur, ProRes master | Original half-time hip-hop score synthesized in numpy | Nothing except a copy check |

## The six-part structure

Every prompt uses the same six tags. Each tag does one job.

| Tag | What goes in it |
| --- | --- |
| `<inputs>` | Product, verbatim on-screen copy, palette hex values, fonts, icons, footage, music, and what the agent must ask you for |
| `<direction>` | The look, the camera language, how attention moves, and an explicit **Banned** list |
| `<structure>` | Duration, BPM and the beat grid, then every event timed to bar · beat · 16th |
| `<build>` | Stack, versions, file layout, camera maths, render and encode commands, QC steps |
| `<gotchas>` | Failures already hit and their fixes, plus licensing |
| `<start>` | The first actions, and the review gates: storyboard or contact sheet, then a draft, then your approval before the final render |

The structure comes from a motion-design prompt template another creator open-sourced on X.

## Why the timing is exact

Each prompt fixes a beat grid before any picture or sound exists (`src/timing.js`, `film/timing.json`, or a `B(bar, beat, 16th)` function). Picture and score both read that one file, so the grid works as a contract between them. With a supplied song (02), the agent analyses the track first (STFT, kick peaks, a least-squares grid fit) and derives the grid from it. With no song (03, 04), it writes the grid, then synthesizes the score on it.

Every frame is a pure function of `t`, with no state carried between frames. Because of that, seeking, scrubbing, sub-frame motion blur and parallel segment rendering all stay deterministic.

## How to use one for your product

1. Open Claude Code and select Opus 5.5.
2. Paste your product URL and a reference video you like, plus the prompt closest to that look.
3. Ask it to analyse the reference and rewrite all six parts for your product: your copy, palette, fonts, icons, and a timeline for your length and BPM. Keep `<gotchas>` and extend it.
4. Set a `/goal` so it loops from brief to storyboard, build, self-review and fixes on its own.
5. Review the gates in `<start>`: the storyboard, the contact sheets and the draft. Approve before the final render.

Rendering needs Node, ffmpeg, and headless Chrome (Playwright). [HyperFrames](https://hyperframes.heygen.com) is needed for 01 and 03.

## Licensing

- The prompt text is free to reuse and adapt.
- Fonts are SIL OFL (Inter, Newsreader, JetBrains Mono, Caveat and others), three.js is MIT, and the scores in 03 and 04 are original.
- Agent icons (Claude Code, Codex, OpenClaw, Hermes) are their owners' marks. Use only the official files, and only to name integrations.
- The song in 02 ("OMW (Short version)" by Jane & The Boy) is licensed to me through Artlist and is **not** included. Use your own licensed track.
- This folder holds no media files.
