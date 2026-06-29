---
name: ascendion-design
description: Use this skill to generate well-branded interfaces and assets for Ascendion — an AI-native IT services, consulting, and product engineering company. Contains essential design guidelines, colors, type, fonts, brand assets, slide templates, and copy/tone rules for prototyping decks, marketing pages, and product mocks.
user-invocable: true
---

# Ascendion Design Skill

Read **`README.md`** in this folder first — it is the source of truth for:

- Company context, products (AAVA™, METAL, JUMP, RECODE), and recurring scale callouts.
- **CONTENT FUNDAMENTALS** — voice, tone, casing, signature phrases, what to avoid.
- **VISUAL FOUNDATIONS** — color, type, imagery, layout, motion, hover/press rules.
- **ICONOGRAPHY** — the Lucide stand-in and when to use the photographic A vs the SVG A-mark.

**For Claude Code users:** also read **`CLAUDE_CODE.md`** — it defines the Designer / Verifier / Exporter role split and points at `tools/verify_deck.py` + `tools/export_deck.py` for local screenshot, PDF, and PPTX export.

Then explore the other available files:

```
colors_and_type.css     ← all design tokens (CSS variables: colors, type, spacing, shadows, motion)
assets/logos/           ← Ascendion wordmark + A-symbol SVGs
assets/brand-imagery/   ← cosmic, neon, surreal photography in the brand's library
assets/badges/          ← analyst recognition badges
preview/                ← 22 swatch / specimen / component cards (Design System tab)
slides/                 ← deck templates:
    │    index.html              — 8 corporate masters (title, stats, three-column, quote, offerings, award, case, section)
    └    extended-templates.html — 10 team archetypes (quad-stats, journey, playbook, architecture,
                                       persona, scoping, services, team, roadmap, use-case)
decks/                  ← finished decks built with this system (Legacy System X-Ray & Navigator etc.)
```

## How to use this skill

**If creating visual artifacts** (decks, mocks, throwaway prototypes, marketing pages):

1. Copy `colors_and_type.css` and the assets you need into your new HTML file's folder. Reference them with relative paths.
2. Always wrap your hero / title slides in `data-theme="dark"` or `.asc-dark` so the mint accent reads correctly. Light content slides need no class.
3. For slide decks:
   - **Corporate / marketing style** — clone `slides/index.html` and edit the eight `<section>` templates (`.s-title`, `.s-stats`, `.s-three`, `.s-quote`, `.s-offer`, `.s-award`, `.s-case`, `.s-section`).
   - **Team / internal style** — clone `slides/extended-templates.html` and edit any of the ten `<section>` templates (`.s-quadstats`, `.s-journey`, `.s-playbook`, `.s-arch`, `.s-persona`, `.s-scoping`, `.s-services`, `.s-team`, `.s-roadmap`, `.s-usecase`).
   - Mix freely — a real deck typically uses 2–3 templates from each library.
   - `deck-stage.js` handles scaling, navigation, and print.
4. **Always** use the brand voice: first-person plural, declarative, AI-first. The word "Ascenders" for employees. **No emoji.** Trademarked products styled exactly: `AAVA™`, `METAL`, `JUMP`, `RECODE`.
5. Stat callouts go big: 96–140px Archivo Black in mint (`#00FAC2` on dark, `#008566` on light). Pair with a small uppercase label below.
6. Use photographic backgrounds, not illustration. If you need an image you don't have, leave a labelled placeholder rather than generating a generic one.

**If working on production code** for Ascendion:

- Import `colors_and_type.css` and use its CSS variables — never hardcode hex.
- The two key surfaces are: white-background content (`--bg`, `--fg`) and ink-black hero (`[data-theme="dark"]`).
- Mint (`#00FAC2`) does NOT pass AA contrast on white. For text on white surfaces use deep-teal (`#008566`).
- For icons, link Lucide from CDN (see README "ICONOGRAPHY"). ⚠ This is a substitution — confirm with the brand owner.

## Font substitution notice

Brand fonts (PP Neue Machina Plain, Avenir LT 45 Book) are commercial and **not bundled in this skill**. The CSS substitutes:

| Brand font | Google Font substitute |
|---|---|
| PP Neue Machina Plain | Archivo Black |
| _condensed display variant_ | Big Shoulders Display |
| Avenir LT 45 Book | Nunito Sans |

If the user provides licensed font files, drop them into `fonts/` and update the `@font-face` block at the top of `colors_and_type.css`.

## If invoked without instructions

Ask the user what they want to build — common asks for this brand are:

- A sales deck (10–20 slides) on a specific offering or industry
- A one-pager / leave-behind for a client meeting
- A landing-page mock for a new AAVA™ studio or service line
- A pitch slide for an award submission
- A microsite hero for a thought-leadership piece

Then ask a few questions: **audience, length, photography or illustration?, dark hero or light deck?, which AAVA™/METAL/JUMP/RECODE products feature?, any client logos to include?**

Always behave as an expert designer producing on-brand HTML artifacts (or production code) — never invent new visual languages outside what `README.md` defines.
