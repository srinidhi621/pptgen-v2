# ppt-gen-v2 — Ascendion Deck Generator

A fully self-contained pipeline that turns text content into branded Ascendion PowerPoint decks. Built on top of the Ascendion HTML design system in this repo. Runs entirely via Claude Code in headless mode — no external API keys, no manual steps.

> _"Engineering To The Power Of AI."_  
> _"We. Do. Software."_  
> _"AI-Native software engineering."_

---

## What This Project Is

This is the second attempt at automating Ascendion deck generation. The [first project (`ppt-gen`)](../ppt-gen/) used Azure OpenAI + python-pptx and stalled on coordinate arithmetic, cross-slide consistency, and the difficulty of reviewing output without a visual feedback loop. This v2 is a clean rewrite with a fundamentally different approach.

**Key differences from v1:**

| | ppt-gen (v1) | ppt-gen-v2 |
|---|---|---|
| LLM access | Azure OpenAI / Gemini via API keys | Claude Code headless mode, enterprise account |
| Rendering medium | python-pptx (coordinate arithmetic) | HTML/CSS (pre-built components in this repo) |
| Visual review | LibreOffice → PDF → raster | Claude vision model reads slide screenshots directly |
| Output | PPTX from python-pptx | PPTX via html-to-pptx conversion |
| Component reuse | None — code written from scratch each run | All slide components pre-built here; zero new code per run |

---

## Pipeline Architecture

```
User content (text, bullets, optional viz cues)
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  PHASE 1 — PLAN                             │
  │  Claude reads content + design system,      │
  │  outputs a deck plan: slide count, types,   │
  │  layout archetype per slide, content map.   │
  └─────────────────┬───────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────┐
  │  PHASE 2 — BUILD (HTML)                     │
  │  Claude assembles each slide from the       │
  │  pre-built component library in /slides/.   │
  │  No new CSS or layout code written.         │
  │  Output: a single self-contained HTML file. │
  └─────────────────┬───────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────┐
  │  PHASE 3 — VISUAL REVIEW (slide-by-slide)   │
  │  Headless browser screenshots each slide.   │
  │  Claude vision model inspects each image:   │
  │  overflow, contrast, alignment, density,    │
  │  brand adherence. Emits a fix list.         │
  └─────────────────┬───────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────┐
  │  PHASE 4 — REPAIR                           │
  │  Claude applies the fix list to the HTML.   │
  │  Re-screenshots only changed slides.        │
  │  Repeats until no critical issues remain    │
  │  (max 2 repair rounds).                     │
  └─────────────────┬───────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────┐
  │  PHASE 5 — EXPORT (HTML → PPTX)             │
  │  html-to-pptx conversion step.              │
  │  Each slide div becomes a native PPTX slide │
  │  at 1920×1080 (16:9).                       │
  └─────────────────┬───────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────┐
  │  PHASE 6 — FINAL VISUAL PASS                │
  │  Claude vision re-reviews the PPTX export   │
  │  to catch any conversion artifacts or       │
  │  font/layout regressions introduced by      │
  │  the html-to-pptx step.                     │
  └─────────────────┬───────────────────────────┘
                    │
                    ▼
             output.pptx
```

### Design principles (lessons from v1)

- **HTML, not coordinate arithmetic.** The browser handles layout. CSS grid and flexbox solve the geometry problems that broke v1's python-pptx approach.
- **Pre-built components, not generated code.** Every slide archetype lives in `/slides/` already. Claude selects and populates — it never writes layout code from scratch.
- **Vision review closes the loop.** The model actually _sees_ the slides. v1 had no visual feedback until a human opened the file.
- **Claude headless, not external APIs.** Uses the Claude enterprise account via `claude --headless` — no `.env`, no API key rotation, no Azure endpoint management.
- **One command, one output file.** The entire pipeline is a single CLI invocation. The PPTX drops in the current directory.

---

## Repository Structure

```
/
├── README.md                       ← you are here (project + design system docs)
├── SKILL.md                        ← Claude Code skill wrapper
├── colors_and_type.css             ← brand tokens (color, type, space, motion)
│
├── slides/                         ← pre-built slide component library
│   ├── index.html                  ← 8 corporate master templates
│   ├── extended-templates.html     ← 10 additional archetypes
│   ├── TitleSlide.jsx
│   ├── StatGridSlide.jsx
│   ├── OfferingsSlide.jsx
│   ├── ThreeColumnSlide.jsx
│   ├── BigQuoteSlide.jsx
│   ├── AwardSlide.jsx
│   └── CaseStudySlide.jsx
│
├── assets/
│   ├── logos/                      ← Ascendion wordmark + A-mark SVGs
│   ├── brand-imagery/              ← hero photos, signature graphics
│   └── badges/                     ← analyst recognition badges
│
├── preview/                        ← design system tab cards (one per concept)
│
├── pipeline/                       ← generation pipeline (to be built)
│   ├── run.sh                      ← entry point: `./pipeline/run.sh "content.md"`
│   ├── prompts/                    ← system prompts for each phase
│   │   ├── 01-plan.md
│   │   ├── 02-build.md
│   │   ├── 03-review.md
│   │   ├── 04-repair.md
│   │   └── 06-final-check.md
│   └── scripts/                    ← phase runner scripts
│       ├── screenshot.js           ← headless browser → slide images
│       └── html_to_pptx.py         ← HTML → PPTX conversion
│
└── decks/                          ← finished decks built from this system
    └── Legacy System X-Ray & Navigator.html
```

---

## Usage

```bash
# Basic usage — pass a content file, get a PPTX back
./pipeline/run.sh inputs/my-content.md

# Outputs: my-content.pptx in the current directory
# Intermediate artifacts in: runs/<timestamp>/
```

Content files are plain text or markdown. Include any visualization cues inline:

```markdown
# Q3 Business Review

## Slide intent
Executive summary for CIO audience. Confident tone. 4-5 slides max.

## Key messages
- Revenue up 23% YoY driven by AI Services practice
- Three new Fortune 500 logos added in Q3
- AAVA platform now deployed at 12 enterprise clients

[viz: stat grid — 23%, 3, 12 as hero numbers]

## Challenges
GenAI adoption is accelerating faster than our delivery capacity...
```

The `[viz: ...]` cues are optional hints to the planner. Without them, Claude infers appropriate layouts from the content structure and message type.

---

## Implementation Status

**Current state:** Design system complete. Pipeline not yet built.

### Build order

- [x] Design system — brand tokens, color, typography, motion
- [x] Slide component library — 18 archetypes across `index.html` + `extended-templates.html`
- [ ] Phase 1 — planner prompt + output schema
- [ ] Phase 2 — builder prompt + component selection logic
- [ ] Phase 3/4 — screenshot tooling + vision review prompt + repair loop
- [ ] Phase 5 — html-to-pptx conversion script
- [ ] Phase 6 — final visual check prompt
- [ ] `run.sh` — orchestrator tying all phases together
- [ ] End-to-end test with a real content brief

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
