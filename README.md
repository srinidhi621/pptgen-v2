# ppt-gen-v2 — Ascendion Deck Generator

An **editable-PowerPoint generator** for Ascendion decks, driven entirely by Claude Code. Open Claude Code in this folder, describe the deck you want, and it builds an on-brand deck from the design system here and hands back an editable `.pptx` — real PowerPoint text boxes and shapes, not screenshots. No external API; a Claude Code enterprise license is the only requirement.

> _"Engineering To The Power Of AI."_  
> _"We. Do. Software."_  
> _"AI-Native software engineering."_

---

## What This Project Is

This is the second attempt at automating Ascendion deck generation. The [first project (`ppt-gen`)](../ppt-gen/) used Azure OpenAI + python-pptx and stalled on coordinate arithmetic, cross-slide consistency, and the difficulty of reviewing output without a visual feedback loop. This v2 is a clean rewrite with a fundamentally different approach.

**Key differences from v1:**

| | ppt-gen (v1) | ppt-gen-v2 |
|---|---|---|
| LLM access | Azure OpenAI / Gemini via API keys | Claude Code, enterprise license — no keys |
| Authoring medium | python-pptx coordinate math (the failure mode) | HTML/CSS — reuses the templates in this repo |
| Output | python-pptx, built from scratch each run | Editable native PPTX via an HTML→OOXML converter |
| Operation | external multi-step pipeline | one prompt to Claude Code in this folder |

---

## How You Use It

You don't run a pipeline. You open Claude Code in this folder and talk to it:

```
$ cd ppt-gen-v2
$ claude
> Build a 6-slide deck for a CIO audience introducing our Legacy
> Modernization offering. Confident tone. Content below:
> ...
```

Claude reads the design skill, authors the deck in HTML, runs the converter, and hands you `decks/<name>.pptx`. That is the whole interface.

## How It Works (Route A)

```
Your prompt + content
        │
        ▼
  Claude Code  ──reads──►  SKILL.md → README → slides/ templates
        │
        ▼
  decks/<name>.html        ← Claude authors the deck in HTML, reusing
        │                     the brand templates in slides/
        ▼
  tools/editable_pptx/export.py decks/<name>.html
        │
        ├─ 1. RENDER     headless Chromium loads the deck (bundled — invisible to you)
        ├─ 2. CAPTURE    walk the DOM; record each element's geometry + computed styles
        ├─ 3. CLASSIFY   each element → text / shape / image / rasterize
        ├─ 4. TRANSLATE  CSS → OOXML: px→EMU, rgb→srgbClr, runs→<a:r>, rotation, radius
        └─ 5. EMIT       assemble the .pptx (python-pptx skeleton + injected slide XML)
        │
        ▼
  decks/<name>.pptx        ← editable native PowerPoint
```

The converter walks **arbitrary DOM** — it does not assume a fixed set of template classes. Real decks invent their own section types: the Legacy deck in `decks/` uses `s-problem`, `s-pipeline`, `s-tier` and others that exist in no template library. Whatever the browser renders, the walker reads back as geometry.

Full technical design — OOXML reference, module breakdown, unit math, escape hatches — lives in **[`SPEC.md`](SPEC.md)**.

## Editable — With Asterisks

"Editable" means real, clickable PowerPoint text boxes and shapes for the bulk of every slide. Some CSS has no OOXML equivalent and is **rasterized per-element** (embedded as an image, not editable):

- Photo-knockout headlines (`background-clip: text`) — the hero "A" and photo-filled display words
- CSS filters / `backdrop-filter`
- Complex SVG (the `.s-arch` architecture diagrams)

Rasterization is per-element, not per-slide — the rest of the slide stays editable. Expect, too: **1–3px text-wrap drift** (CSS and PowerPoint wrap with different font metrics), and a hard requirement to **embed fonts** in the `.pptx` so decks render correctly on machines without Archivo Black / Nunito Sans. These are the standing costs of the fidelity-plus-editable tradeoff; see `SPEC.md`.

## Single Sources of Truth

Two documents govern the build. Everything else — including this README's project section — defers to them:

| Doc | Role |
|---|---|
| **[`SPEC.md`](SPEC.md)** | The *what* and *how* — architecture, contract, OOXML reference, module design, definition of done. |
| **[`PLAN.md`](PLAN.md)** | The *board* — epics → stories → tasks, vertical slices, status, what's next. The live state of the build. |

---

## Repository Structure

```
/
├── README.md                       ← you are here (project overview + design system)
├── SPEC.md                         ← build spec: architecture, OOXML, contract   ◄ source of truth
├── PLAN.md                         ← JIRA-style board: epics / stories / tasks    ◄ source of truth
├── SKILL.md                        ← Ascendion design skill (Claude-invocable)
├── CLAUDE_CODE.md                  ← legacy screenshot-pipeline notes (superseded by SPEC)
├── colors_and_type.css             ← brand tokens (color, type, space, motion)
│
├── slides/                         ← HTML template library (the authoring substrate)
│   ├── deck-stage.js               ← <deck-stage> runtime: scaling, nav, print
│   ├── index.html                  ← 8 corporate templates (s-title, s-stats, s-three,
│   │                                  s-quote, s-offer, s-award, s-case, s-section)
│   └── extended-templates.html     ← 10 archetypes (s-quadstats, s-journey, s-playbook,
│                                      s-arch, s-persona, s-scoping, s-services, s-team,
│                                      s-roadmap, s-usecase)
│
├── tools/
│   ├── verify_deck.py              ← dev: screenshot + DOM overflow check
│   ├── export_deck.py              ← legacy: PDF + screenshot-mode PPTX (not editable)
│   └── editable_pptx/              ← THE BUILD: HTML→OOXML converter (see SPEC + PLAN)
│
├── assets/                         ← logos, brand imagery, analyst badges
├── preview/                        ← design-system specimen cards
└── decks/                          ← finished decks (HTML, and exported PPTX)
    └── Legacy System X-Ray & Navigator.html
```

---

## Setup (one-time, per machine)

```bash
python3 -m venv .venv
.venv/bin/pip install playwright python-pptx pillow lxml
.venv/bin/python -m playwright install chromium   # bundled browser — no system Chrome needed
```

The converter uses **bundled Chromium**, not your installed Chrome, so behaviour is identical on every colleague's machine.

### What to give Claude

A brief in plain language. Inline `[viz: …]` cues are optional hints:

```markdown
# Q3 Business Review — CIO audience, confident tone, ~5 slides

## Key messages
- Revenue up 23% YoY, driven by the AI Services practice
- Three new Fortune 500 logos in Q3
- AAVA™ now deployed at 12 enterprise clients
[viz: stat grid — 23 / 3 / 12 as hero numbers]
```

Without cues, Claude infers layout from content shape and message type.

---

## Status

The design system and HTML template library are complete. The HTML→OOXML converter is the active build.

**The live build state — what's done, in progress, and next — is in [`PLAN.md`](PLAN.md).** This README does not track build status; `PLAN.md` does.

---

## Design System Reference

The rest of this document is the Ascendion design system specification — the ground truth for brand tokens, typography, color, layout rules, and component conventions that the pipeline uses to produce on-brand output.

---

## Sources

This system was reverse-engineered from two PowerPoint decks the user provided:

| File | What it contains |
|---|---|
| `uploads/Corp Deck 2025 - Nov.pptx` | 20-slide Ascendion corporate deck. Master themes, hero imagery, global office data, AAVA™ product story, AI Arbitrage narrative, awards. |
| `uploads/AI Services  Applied AI Offerings.pptx` | 12-slide Applied AI offerings deck. Capability tree, services menu, advisory model, rapid prototyping, contact-center modernization, IDP, validation, ops. |

**Public references** (when the reader has access):
- Brand asset library: `https://ascendionhub.sharepoint.com/sites/CorporateMarketing-Hub/SitePages/Ascendion-Brand-Assets-Library.aspx` (internal SharePoint, not public)
- Public site: `https://ascendion.com`
- "AI &lt;/Recodes&gt; Tier One" thought-leadership: `https://ascendion.com/wp-content/uploads/2024/08/AI-Recodes-Tier-1.pdf`

**Team reference deck:** `uploads/designer_reference_slides.pptx` — 21 internal slides showcasing the in-house design vocabulary. Lifted 10 archetypes into `slides/extended-templates.html` and used its `25_New_ascendion colors` theme XML to refine the brand palette below.

No live codebase or Figma was supplied for this brand — everything below is derived from the deck masters, theme XML, and brand imagery embedded in those files.

---

## Company context

Ascendion positions itself as **"an AI-native software engineering disruptor"** — a pure-play services company that has rebuilt its delivery model around generative + agentic AI. Three messages recur across every slide:

1. **Engineering to the power of AI** — the brand's master tagline.
2. **AI Arbitrage** — a new commercial model where AI productivity gains are priced into the deal so client capital is freed from tech debt to fund innovation.
3. **Two booster rockets** — the **AAVA™** platform (AI engineering studios) and **METAL** (AI talent platform).

### Products / pillars referenced
- **AAVA™** — flagship "Intelligent Engineering Platform." AAVA Studios cover Product, Design, Architecture, Quality Engineering, Data Modernization, FinOps, AI-Powered Operations, OneView, Digital Ascender.
- **METAL** — AI talent cloud platform.
- **JUMP** — STEM workforce program.
- **RECODE** — CIO-aligned change advisory.
- **AI Studios** — physical client-facing co-innovation spaces (Hyderabad, Chennai, Austin, Makati City).

### Scale callouts (used constantly in collateral)
> 11,000+ Ascenders · 400+ Enterprise Clients · 36% of the Fortune 500 · 40+ Offices · 13 Countries · 10 Global Delivery Hubs · 4 AI Studios · ~2,000 Agentic Tasks built · 3,000 GenAI Developers · 300 Agent Developers

---


## CONTENT FUNDAMENTALS

The Ascendion voice is **declarative, AI-first, and impatient with the status quo.** It speaks to enterprise buyers (CIOs, CTOs, CHROs) but bypasses corporate hedging — sentences are short, often start with verbs, and resolve into a clean claim. Marketing copy treats AI as a force of nature ("GenAI is eating IT services," "the new game is enhanced humans") and frames Ascendion as the antidote, not a vendor.

### Voice & tone

| | |
|---|---|
| **POV** | First-person plural — "we," "our," "us." Employees are **"Ascenders."** Clients are "allies." |
| **Tense** | Present active. "Ascendion **delivers**…", "AAVA™ **uses** AI…", "We **are moving** work to software." |
| **Register** | Confident, slightly evangelical. The word "**revolution**," "**disruptor**," "**antidote**" appears often. |
| **Sentence length** | Short → medium. Big ideas land in 5–10 words. Numbers do the heavy lifting. |
| **Casing** | **Title Case** for slide headlines (most common: every Major Word Capitalised). **UPPERCASE** for eyebrows, the wordmark, and the giant condensed hero words ("PROGRESS ISN'T A STRAIGHT LINE"). Sentence case for body. |
| **Emoji** | **None.** Not part of the brand. Avoid completely. |
| **Punctuation quirks** | Em-dashes are common — used to set off claims. Trailing ellipses appear when posing a problem ("don't waste your people's time…"). Stylized inline tags like `<AI/Recodes>`, `Agentic AI`, `</Tier One>` borrow code-tag aesthetics. |
| **Trademark style** | `AAVA™` always appears with the trademark sup. `METAL`, `JUMP`, `RECODE` are written in full caps without the ™. |

### Recurring phrases & signature copy

- **"Engineering to the Power of AI"** — master tagline.
- **"We. Do. Software."** — punchy line on positioning slides.
- **"The new name of the game is productivity via ENHANCED humans."**
- **"Without Engineering^AI, these imperatives would be too expensive and risky."**
- **"AI Arbitrage will unlock capital for innovation."**
- **"Software engineering at the intersection of technology and talent."**
- **"Big enough for the Enterprise; small enough to serve."**
- **"Know How and Done That."** — AI experts positioning line.
- **"Tell me what to do / Help me do it / Operationalize it for me"** — the three-pillar AI services framing.
- **"Last Mile for value"** — the GenAI-doesn't-work-out-of-the-box line.

### Headline patterns

Pick one of three:
1. **Verb-led claim** — "Solving Global Engineering Problems", "Transforming your Contact Centre with Agentic AI"
2. **Diagnostic statement** — "Leaders Are Wrestling With Three Challenges", "GenAI is Eating IT Services"
3. **Mathematical metaphor** — "Engineering To The Power Of AI" (with `AI` typeset as a superscript exponent on the word `Engineering`)

### Body copy examples (paraphrased from decks)

> "Our global presence and diverse teams are dedicated to delivering AI-driven solutions that make a real impact. By combining cutting-edge technology with human expertise, we transform businesses and elevate everyday experiences for clients around the world."

> "Rapid prototyping enables us to explore the art of the possible, test feasibility quickly, and prioritize what delivers maximum value. Helps teams shift from 'Can we build this?' to 'Should we build this?'"

> "AAVA™ accelerates software delivery by streamlining workflows with intelligent agents, maintaining top-quality standards."

### What to avoid

- ❌ Lowercase, "friendly" tech-bro voice (Ascendion is corporate-confident, not Slack-casual)
- ❌ Emoji in body copy, headlines, or as bullets
- ❌ Apologetic hedging ("we believe," "we think," "maybe")
- ❌ Generic engineering clichés without an AI angle
- ❌ Mixing the wordmark casing — it's always **ASCENDION** in display, never "Ascendion" inside the logo lockup (though "Ascendion" in body copy is fine)

---

## VISUAL FOUNDATIONS

### Color

The palette is built around **one signature color and a lot of restraint.**

| Token | Hex | Where it lives |
|---|---|---|
| **Mint** `--asc-mint` | `#2CDCAA` | The brand. Eyebrows on dark, accent strokes, hero stats, "AAVA™" wordmark. Source: official `25_New_ascendion colors` theme. |
| **Mint Bright** `--asc-mint-bright` | `#00FAC2` | Legacy / marketing-deck variant. Use only when matching the corporate hero look from the Nov 2025 deck. |
| **Deep teal** `--asc-mint-900` | `#006450` | Mint's accessible cousin for text on white. Source: official theme. |
| **Ink** `--asc-ink` | `#0A0A0F` | Hero deck slides, near-black backdrops. |
| **Slate** `--asc-slate` | `#71758A` | Secondary text on light, dividers on dark. |
| **Fog** `--asc-fog` | `#AFAAB9` | Tertiary text, gridlines. |
| **Paper** `--asc-paper` | `#F5F4F7` | Light surface, off-white slide bodies. |
| Accents | Magenta `#8C0059`, Purple `#6666CC`, Orange `#F5821E`, Yellow `#FFC000`, Lavender `#968CFA` | **From official theme.** Magenta for highlights, purple for AI/agentic, orange for energy callouts. Used sparingly. |
| Signature gradient | `#FD0199 → #52009B` | Thin underline rules and divider treatments only — never a giant gradient wash. |

**Rule of thumb:** dark hero slide = Ink background, white headline, **mint accent**. Light content slide = White or Paper background, Ink headline, deep-teal accent. Avoid mint on white as a primary fill — it doesn't pass contrast.

### Typography

| Role | Brand font | Substitute (this system) | Where it appears |
|---|---|---|---|
| Display | **PP Neue Machina Plain** | **Archivo Black** | Slide headlines, statistics, "AAVA™" lockup |
| Display condensed | _(custom hand-set / Neue Machina Inktrap)_ | **Big Shoulders Display** | Mega knockout words ("PROGRESS ISN'T A STRAIGHT LINE", the giant photo-filled "A") |
| Body | **Avenir LT 45 Book** | **Nunito Sans** (with Aptos in fallback chain for Office users) | Paragraph copy, bullets, footnotes, captions |
| System fallback | Aptos / Arial / Verdana | system-ui | Microsoft Office fallbacks present in master |
| Mono | _(none in source)_ | **JetBrains Mono** | Code samples, terminal-style accents in this system |

⚠️ **Font substitution notice for the user:** This system substitutes Google Fonts for the commercial brand fonts. Please send the licensed font files for PP Neue Machina Plain and Avenir LT 45 Book so I can replace the substitutes — until then, exports will look ~85% accurate but the geometric stroke character of PP Neue Machina (its squared-off counters, sharp inktraps) won't be perfectly captured by Archivo Black.

**Scale:** see `colors_and_type.css`. Deck calibration: H1 = 88px, H2 = 56px, eyebrow = 12px tracked +0.16em, stats = 96px, mega = up to 220px.

**Tracking:** display sizes use negative tracking (-0.015em to -0.03em). Eyebrows use generous tracking (+0.16em).

### Backgrounds & imagery

The brand uses **cinematic photography**, never illustration or hand-drawn SVG. Three categories recur:

1. **Cosmic / space** — astronaut on a moon-like surface under a mint-green nebula, rocket launches, milky-way arcs. These signal "ambition / new frontier."
2. **Futuristic interiors** — neon-lit data corridors, holographic dashboards, abstract glowing geometry. Cyan/teal + orange light is common.
3. **Conceptual surrealism** — minimalist figure standing in a sky-room with clouds, brain-in-lightbulb network. Cooler blues, contemplative mood.

All imagery is **photographic and color-graded toward cool tones** — blues, teals, deep blacks — with the mint accent doing the warm/cool contrast work. No warm-and-fuzzy stock photography of laughing teams in meeting rooms. **No illustrations, no flat 3D vector scenes, no hand-drawn motifs.**

**Full-bleed treatment** is the default for hero slides. Body slides use white backgrounds with one accent image off to the side, or no image at all.

**Signature "knockout" effect:** large display letterforms (often a single "A" or a short word) filled with photography. CSS `background-clip: text` replicates this — see `.asc-knockout` in the tokens.

### Layout rules

- **16:9, 1920×1080** is the canonical canvas (decks).
- **Generous margins** — typically 80–120px outer padding on a 1920px-wide slide.
- **Three-column grids** are the workhorse for "challenges / pillars / outcomes" slides. Twelve-column underlies finer detail.
- **Fixed footer**: small wordmark or "ASCENDION CONFIDENTIAL" eyebrow bottom-left, page number bottom-right, sometimes a thin mint or gradient rule.
- **Sticky stat columns** on the right side of hero slides (e.g. "11,000+ / Ascenders / Globally" stack).
- The huge condensed type element ("PROGRESS ISN'T A STRAIGHT LINE") **anchors a corner of the slide at an angle**, often rotated -20° to 20°, breaking the grid intentionally.

### Borders, corners, shadows, transparency

- **Corner radii** are restrained: 0, 2, 4, 8, 12px. **No pill-shaped containers** except for tag/chip components and CTA buttons in product UI. The brand favors sharp or slightly softened edges.
- **Cards** use either: (a) hairline 1px border at `rgba(0,0,0,0.10)` with no shadow on white surfaces, or (b) solid dark fill `--asc-graphite` with no border on dark surfaces. **Drop shadows are subtle and neutral** — never colored, never heavy.
- **Borders** are the primary container-separation method, not shadows.
- **Transparency / blur** is sparingly used — mostly on photographic hero overlays (a 30–50% ink-black scrim under headline type) to lift contrast. Glassmorphism is not part of the brand.
- **Protection gradients** (linear black-to-transparent) are used under text laid over photographs so headlines remain legible.

### Motion

The decks are static, but for prototypes built with this system, motion should feel **engineered, not playful.**

- **Easing:** `cubic-bezier(0.2, 0.7, 0.2, 1)` for entrances; `cubic-bezier(0.65, 0, 0.35, 1)` for in-out transitions.
- **Duration:** 140ms (micro), 220ms (default), 420ms (slow hero).
- **Style:** fades, short slides (8–16px), subtle scale (0.97 → 1.0). **No bounces, no springs, no playful overshoot.** Hover states use a 140ms color/opacity transition, never scale.

### Interaction states

- **Hover (button, link):** color shifts to `--asc-mint-700` (or for solid mint buttons, background darkens by ~12%). Underlines remain. No scale.
- **Pressed:** background darkens another step (-8% lightness), or for outlined buttons, fill flashes to 10% mint tint. No scale-down.
- **Focus:** 2px solid mint ring offset by 2px (`outline: 2px solid var(--asc-mint); outline-offset: 2px`).
- **Disabled:** 40% opacity, `cursor: not-allowed`.

---

## ICONOGRAPHY

The decks use a mixed-bag iconography approach that's **less consistent than the type and color system.** What you'll see across the source material:

| Source | Style | How to handle |
|---|---|---|
| **The "A" mark** (Ascendion symbol) | Heavy condensed slab letterform, used at small sizes alone or inside the wordmark | Use `assets/logos/ascendion-a-mark-*.svg` — already extracted |
| **Inline category icons in offerings/services grids** | Mostly flat 2-color glyphs (mint or magenta on white), simple geometric metaphors — a brain, a gear-with-AI-spark, a stack of documents, etc. They're not consistent — appear to be sourced from a mix of stock icon libraries inside PowerPoint | **Substitute with [Lucide Icons](https://lucide.dev)** (loaded from CDN). Lucide's 24px stroke style matches the visual weight of the inline icons in the AI offerings deck closely enough that the system feels coherent. ⚠️ **This is a substitution** — there is no official Ascendion icon library available; the user should specify if one exists. |
| **Emoji** | **Never used.** Don't introduce. |
| **Unicode arrows / glyphs** | Occasional `→`, `↗`, `™`. Use these freely; don't replace with SVGs. |
| **Awards / analyst badges** | Photographic/raster (HFS Horizons, ISG Provider Lens, Gartner mentions). These are vendor-supplied and used as-is. See `assets/badges/`. |

### Lucide icon CDN

```html
<!-- For static rendering -->
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<i data-lucide="brain"></i>
<script>lucide.createIcons();</script>

<!-- Or per-icon SVG -->
<img src="https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/brain.svg" alt="" width="24" />
```

Use these Lucide glyphs for the recurring deck categories:

| Concept | Lucide icon |
|---|---|
| AI / agentic | `brain`, `bot`, `cpu` |
| Engineering | `cog`, `wrench`, `code-2` |
| Speed / velocity | `zap`, `rocket`, `gauge` |
| Trust / governance | `shield-check`, `lock`, `eye` |
| Capital / ROI | `trending-up`, `wallet`, `dollar-sign` |
| Talent | `users`, `user-plus` |
| Data | `database`, `bar-chart-3` |
| Cloud / infra | `cloud`, `server` |
| Quality | `check-circle-2`, `bug` |

### When to use the photographic "A" knockout vs. the SVG A-mark

- **Photographic A** — hero/marketing moments where the deck wants to convey scale, ambition, the "human × technology" intersection. Letterform is filled with imagery (sky, water, neon corridor).
- **SVG A-mark** — small-scale uses: favicons, app icons, footers, signatures, video bumpers. Always solid color (mint, white, or ink — never gradient).

---

## Quick-start usage

```html
<!DOCTYPE html>
<html data-theme="dark">  <!-- or omit for light theme -->
<head>
  <link rel="stylesheet" href="colors_and_type.css">
</head>
<body>
  <p class="asc-eyebrow">Engineering<sup>AI</sup></p>
  <h1>Software Engineering To The Power Of AI</h1>
  <p class="asc-lede">11,000+ Ascenders, 400+ enterprise clients, one unified AI delivery platform.</p>

  <div class="asc-stat">36%</div>
  <div class="asc-stat__label">of the Fortune 500 are clients</div>

  <hr class="asc-grad-rule">
</body>
</html>
```

---

## Caveats & open questions for the brand owner

1. **Font licensing:** PP Neue Machina and Avenir LT 45 Book are commercial. Substituted with Archivo Black + Nunito Sans. Aptos (Microsoft default, ships with Office) is in the body-font fallback chain since the team reference deck uses it.
2. **Iconography:** The decks don't ship a consistent icon set. Lucide is used as a stand-in. _Please confirm if Ascendion has a defined icon library._
3. **No product/web UI was provided.** This system covers brand foundations + deck templates. UI kits for any web property would need a separate codebase or Figma import.
4. **Imagery library:** The brand asset SharePoint URL was referenced inside the deck but isn't publicly accessible. Hero photography is captured from what was embedded in the source PPTX.
5. **Two palette eras coexist:** the corporate Nov 2025 deck uses mint `#00FAC2`; the team reference deck's official `25_New_ascendion colors` theme uses `#2CDCAA`. This system prefers `#2CDCAA` as canonical (matches the named theme) but exposes the bright variant as `--asc-mint-bright` for explicit corporate-hero use.

## Extended slide templates (from team reference deck)

`slides/extended-templates.html` ships 10 additional archetypes lifted from the internal team deck and rendered in current Ascendion brand language:

| Class | Use for |
|---|---|
| `.s-quadstats` | 4-quadrant stat tiles with sources strip — market sizing, "why now" intros |
| `.s-journey` | 6-stage horizontal journey with sub-steps + outputs per stage |
| `.s-playbook` | 5-column framework (What / Why / How / Build / Scale) |
| `.s-arch` | Reference architecture: sources → pipeline → outputs, with feedback loop |
| `.s-persona` | Persona-led user story: avatar + pain + wish + solution approach |
| `.s-scoping` | Scoping matrix: N focus areas × Objective / Focus / Value-Add |
| `.s-services` | Services-suite menu: 4 practice cards + value-props sidebar + partners strip |
| `.s-team` | Project staffing: leadership + delivery grid + communication cadence |
| `.s-roadmap` | 5-phase MVP roadmap with deliverables, durations, and gate checkpoints |
| `.s-usecase` | Use case overview with modules, data-flow mini-diagram, and benefits sidebar |

Copy the relevant `<section>` block from `extended-templates.html` into a new deck, swap content, done.
