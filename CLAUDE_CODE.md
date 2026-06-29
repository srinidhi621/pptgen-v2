# Ascendion Design — Claude Code Integration

> ⚠️ **SUPERSEDED — historical reference only.** This describes the original
> Designer/Verifier/Exporter **screenshot-mode** pipeline (non-editable PPTX).
> The active project builds an **editable** PPTX converter (Route A). The two
> sources of truth are **[`SPEC.md`](SPEC.md)** (design) and **[`PLAN.md`](PLAN.md)**
> (build board). The screenshot exporter (`tools/export_deck.py`) still works as a
> fallback, which is why this file is kept — but don't treat it as the plan.

> A self-contained skill for **Claude Code** that replicates the design-build-verify-export pipeline.
> Paste this file at the start of a Claude Code session, or reference it with `@CLAUDE_CODE.md`.

---

## What this skill does

Given a **markdown brief** with content + visualization cues, produce a polished Ascendion-branded slide deck as:

1. **HTML** — the source of truth, opens in any browser, scales to any screen.
2. **PDF** — one slide per page, via Chrome headless.
3. **PPTX** (screenshot mode) — one PNG per slide embedded in a 16:9 PowerPoint deck. Pixel-perfect, not editable.

Editable PPTX (native PowerPoint shapes) is out of scope for the local pipeline — when you need it, the HTML is the editable artifact.

---

## One-time setup

Run these once per laptop. Confirm before assuming they're installed.

```bash
# Python environment
python3 -m venv /Users/Srinidhi/my_projects/ppt-gen-v2/.venv
source /Users/Srinidhi/my_projects/ppt-gen-v2/.venv/bin/activate
pip install playwright python-pptx pillow

# If you already have Google Chrome installed, you can skip the next line —
# the tools default to using channel="chrome" (your installed Chrome).
# If you'd rather use Playwright's bundled Chromium, run:
#   python -m playwright install chromium
# …and edit the launch() calls in tools/*.py to drop the channel="chrome" arg.
```

Anytime you run a tool: activate the venv first.

```bash
source /Users/Srinidhi/my_projects/ppt-gen-v2/.venv/bin/activate
```

---

## Skill files

```
/Users/Srinidhi/my_projects/ppt-gen-v2/
├── SKILL.md                  ← skill metadata + invocation rules
├── README.md                 ← brand foundations, content rules, palette
├── CLAUDE_CODE.md            ← THIS FILE
├── colors_and_type.css       ← design tokens (colors, type, spacing, motion)
├── assets/                   ← logos, brand imagery, badges
├── slides/                   ← deck-stage runtime + 18 slide templates
│   ├── deck-stage.js         ← scaling, navigation, print
│   ├── index.html            ← 8 corporate master templates
│   └── extended-templates.html   ← 10 team archetypes
├── decks/                    ← finished decks live here
└── tools/
    ├── verify_deck.py        ← screenshot + overflow diagnostics
    └── export_deck.py        ← PDF and PPTX export
```

---

## The three roles

Claude Code should adopt these roles in order. The **Designer** is the primary persona; **Verifier** and **Exporter** are sub-agents you spawn via the `Task` tool.

### 1. Designer (primary)

You are the lead designer. You have **read** every file in the skill — `README.md`, `colors_and_type.css`, `slides/index.html`, `slides/extended-templates.html`. You know what each template (`.s-title`, `.s-stats`, `.s-quadstats`, `.s-journey`, etc.) is for and what content shape it takes.

**Your job when given a brief:**

1. Read the markdown brief and visualization cues carefully.
2. For each slide, pick the best-fitting template from the 18 available. List your picks back to the user before writing code.
3. Write the deck to `decks/<deck-name>.html`. Pattern after an existing deck (e.g. `decks/Legacy System X-Ray & Navigator.html`) — same `<head>` (token-forwarder + linked CSS + inline styles), same `<deck-stage>` wrapper, same `<script src="../slides/deck-stage.js">` footer.
4. **Reuse template CSS** from `slides/index.html` and `slides/extended-templates.html` — copy the relevant `<style>` blocks into your deck's `<head>`. Don't reinvent.
5. **Reuse template HTML structure** — copy the `<section class="s-...">` block for each archetype and edit the content. Keep the chrome (`<img class="chrome-wm">`, `.chrome-page`, `.chrome-conf`).
6. Use **brand voice** from README's CONTENT FUNDAMENTALS — first-person plural, declarative, no emoji, trademark style (`AAVA™`, `METAL`, `JUMP`, `RECODE`).
7. Use **brand tokens** from `colors_and_type.css` — never hardcode hex; reference `--asc-mint`, `--asc-mint-900`, `--asc-ink`, etc.
8. Stats go big (96–140px), eyebrows small with 0.16em tracking, headlines in Archivo Black.

### 2. Verifier (sub-agent via `Task`)

Spawn this when the deck is written. Pass `task: "verify decks/<file>.html"`.

The verifier:
1. Runs `python tools/verify_deck.py decks/<file>.html`.
2. The script outputs a JSON report: per-slide screenshot path, any DOM overflow violations, console errors.
3. The verifier reads the report, opens any screenshots that look suspicious, and reports back:
   - **PASS** if all slides fit the 1920×1080 canvas and screenshots look correct.
   - **NEEDS WORK** with a concrete diff list: "slide 3 .grid overflows by 38px, fix .h2 margin-bottom".

The Designer applies the fixes and re-spawns the Verifier until PASS.

### 3. Exporter (sub-agent or inline)

Spawn this after Verifier reports PASS. Pass `task: "export decks/<file>.html"`.

The exporter:
1. Runs `python tools/export_deck.py decks/<file>.html --pdf --pptx`.
2. Produces `decks/<file>.pdf` and `decks/<file>.pptx`.
3. Reports the file paths to the user.

---

## End-to-end workflow

```
User: drops markdown brief in chat
Claude (Designer):
  1. Read brief + visualization cues
  2. Pick templates per slide; confirm with user
  3. Write decks/<name>.html
  4. Spawn Verifier sub-agent → screenshots + overflow report
  5. If issues, fix and re-verify
  6. Spawn Exporter sub-agent → PDF + PPTX
  7. Report all three artifact paths to user
```

---

## Key authoring rules (lifted from the design system)

- **1920×1080 canvas**, padding `--pad: 80–96px`, generous margins.
- Display type = **Archivo Black** (Nunito Sans fallback). Body = **Nunito Sans** (Aptos in fallback chain for Office users). Mono = **JetBrains Mono**.
- **Mint** is the brand. Use `var(--asc-mint)` (`#2CDCAA`) on dark backgrounds; use `var(--asc-mint-900)` (`#006450`) on white (mint-on-white fails contrast).
- **No emoji.** Ever.
- **No hardcoded hex.** Use CSS variables.
- Tradename style: `AAVA™` with the `™`, `METAL` / `JUMP` / `RECODE` all-caps no `™`.
- **Wordmark top-left, page number bottom-right** on every slide except the title.
- Stats land in 96–140px Archivo Black; pair with 14px uppercase tracked label below.
- Body text minimum 16px (24px is better at 1920×1080).
- Photographic backgrounds only — no illustration, no hand-drawn SVG for imagery. Schematic diagrams (architecture, timelines, flows) are OK and encouraged.

---

## What the brief should contain

Best results from briefs that look like this:

```markdown
# Deck title

Audience: <CIOs, Eng VPs, exec sponsors>
Length: <10 slides, 20 minutes, unless specified otherwise>
Visual cue: <dark hero, mint accents, technical>

## Slide 1: Title
- Headline
- Subtitle
- Visual cue: "use the cyberpunk-data-corridor hero with x-ray overlay"

## Slide 2: <slide-type>
- Bullet
- Bullet
- Visual cue: "three-column"

...
```

If the brief is loose, the Designer asks 2–3 clarifying questions before writing code.

---

## Caveats — be honest with the user

- **Editable PPTX export is not in this pipeline.** Screenshot-mode PPTX produces pixel-perfect, non-editable slides. If the user needs editable PowerPoint, the HTML deck is the editable artifact, and they can request editable PPTX in the design environment (where custom OOXML generation is available).
- **Font substitution** — PP Neue Machina and Avenir LT 45 Book are commercial; substitutes (Archivo Black + Nunito Sans) are ~85% accurate. If client deliverables require exact-match output, drop licensed font files into `assets/fonts/` and add `@font-face` declarations to `colors_and_type.css`.
- **Icons** — Lucide is used as a stand-in until Ascendion ships an official icon library. Linked from CDN; embed via `<img src="https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/<name>.svg">` or inline SVG for control.
