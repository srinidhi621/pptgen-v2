# PLAN — Build Board

> The live execution board for the editable PPTX converter. Pairs with **[`SPEC.md`](SPEC.md)** (the technical design). This doc owns *what order we build in and where we are*; SPEC owns *what it is and how it works*. Update this file after every working session.

## How this board works

- **Hierarchy:** Epic → Story → Task. IDs are stable (`E1`, `S1.2`, `T1.2.3`).
- **Status:** `TODO` · `WIP` · `BLOCKED` · `DONE`. One Story is `WIP` at a time.
- **Vertical slices.** Every Story must end in a `.pptx` you can open in PowerPoint. No Story is "build the parser" with nothing to run — each adds one visible capability end-to-end.
- **Test gate.** A Story is `DONE` only when its acceptance check passes. Checks are concrete and verifiable (a unit test, or "open in PowerPoint, retype the headline, it changes").
- **Build the next bit only after the current slice is solid.** Don't move on with known regressions in the previous slice.

## Current focus

→ **E0 — Foundations.** Nothing built yet. Start at `S0.1`.

## Status at a glance

| Epic | Title | Status |
|---|---|---|
| E0 | Foundations & self-contained environment | TODO |
| E1 | First vertical slice — title slide end-to-end | TODO |
| E2 | Corporate templates (`slides/index.html`, 8) | TODO |
| E3 | Extended templates (`slides/extended-templates.html`, 10) | TODO |
| E4 | Fidelity, fonts & real decks | TODO |
| E5 | Claude Code skill wiring (one-prompt workflow) | TODO |

---

## E0 · Foundations & self-contained environment  — `TODO`

**Goal:** a reproducible, browser-self-contained dev environment and the two primitives (`units`, `colors`) everything else depends on, proven by emitting one hardcoded slide that opens cleanly in PowerPoint.

### S0.1 · Self-contained environment — `TODO`
- [ ] T0.1.1 Create `.venv`; install `playwright python-pptx pillow lxml`.
- [ ] T0.1.2 `playwright install chromium` (bundled — **no `channel="chrome"`**, per SPEC §1).
- [ ] T0.1.3 Write `scripts/setup.sh` doing the above idempotently.
- **Done when:** fresh checkout → `scripts/setup.sh` → `python -c "import playwright, pptx, PIL, lxml"` succeeds and Chromium is present, with no system Chrome installed.

### S0.2 · OOXML reference artifacts — `TODO`
- [ ] T0.2.1 Make a 1-slide PowerPoint by hand (one rect, one text box); save, unzip into `tools/editable_pptx/reference/`.
- [ ] T0.2.2 Annotate the minimal `slide1.xml`, `[Content_Types].xml`, and `.rels` in `reference/README.md`.
- **Done when:** `reference/` holds a readable minimal example to copy XML patterns from.

### S0.3 · Core primitives with tests — `TODO`
- [ ] T0.3.1 `units.py`: `px_to_emu`, `pt_to_emu`, `deg_to_60k`; constants from SPEC §4.
- [ ] T0.3.2 `colors.py`: parse `#hex`, `rgb()`, `rgba()`, named → 6-digit hex + alpha.
- [ ] T0.3.3 `tests/test_units.py`, `tests/test_colors.py`.
- **Done when:** `pytest` green; `px_to_emu(1920) == 12192000` exactly.

### S0.4 · "Hello rectangle" emit — `TODO`
- [ ] T0.4.1 `emit.py`: one slide, one hardcoded mint rect + one text box, via python-pptx skeleton + injected XML (SPEC §4).
- [ ] T0.4.2 `export.py` CLI stub that writes `output.pptx`.
- **Done when:** `output.pptx` opens cleanly in PowerPoint for Mac; the rect responds to Format Shape; the text box is editable. *(manual gate)*

---

## E1 · First vertical slice — title slide end-to-end  — `TODO`

**Goal:** convert `slides/index.html` slide 1 (`.s-title`) into an editable PPTX, hero photo rasterized, everything else native. Proves the whole capture→classify→translate→emit chain on one real slide.

### S1.1 · IR + capture skeleton — `TODO`
- [ ] T1.1.1 `ir.py`: dataclasses (node tag, bounds, computed styles, role, text-runs, children).
- [ ] T1.1.2 `capture.py`: load deck (bundled Chromium), set `noscale`, `goTo(0)`, walk the active slide's DOM, assign `data-capture-id`, emit JSON IR with bounds + key computed styles.
- [ ] T1.1.3 `tests/test_capture_minimal.py` on `fixtures/minimal.html`.
- **Done when:** capturing index.html slide 1 yields IR JSON containing the eyebrow, headline, subtitle, deck-meta, wordmark, and background nodes with correct bounds.

### S1.2 · Classify v0 — `TODO`
- [ ] T1.2.1 `classify.py`: assign `text-leaf / shape / image / rasterize / skip` per SPEC §5.
- **Done when:** title-slide nodes get sensible roles; the hero photo + scrim is flagged `rasterize`.

### S1.3 · Translate + emit the title slide — `TODO`
- [ ] T1.3.1 `translate.py`: text node → `txBody`; box → `prstGeom`; px→EMU via `units`; color via `colors`.
- [ ] T1.3.2 Extend `emit.py` to assemble a slide from translated nodes.
- **Done when:** title-slide `.pptx` opens; clicking the headline and typing "Foo Bar" changes it. *(manual gate)*

### S1.4 · Rasterize escape hatch v0 — `TODO`
- [ ] T1.4.1 `rasterize.py`: per-element screenshot at 2× DPI, embed as `<p:pic>` at original bounds.
- **Done when:** hero photo+scrim renders correctly as an embedded image while the rest of the slide stays editable.

**Epic gate:** title slide is editable and matches the HTML render within tolerance.

---

## E2 · Corporate templates (`slides/index.html`)  — `TODO`

**Goal:** convert all 8 corporate sections. Each Story adds one subsystem. Order = increasing difficulty. Open each in PowerPoint before moving on.

- [ ] **S2.1 · `s-stats`** — multiple text boxes, big numbers; **subsystem:** inline runs + superscript (`<sup>`, baseline shift).
- [ ] **S2.2 · `s-three`** — three rounded-rect cards with nested text; **subsystem:** `roundRect` + body padding/anchor.
- [ ] **S2.3 · `s-offer`** — bordered pillar cards; **subsystem:** `<a:ln>` outlines.
- [ ] **S2.4 · `s-quote`** — rotated mega type; **subsystem:** rotation (`rot` in 60000ths).
- [ ] **S2.5 · `s-award`** — gradient text + photo column; **subsystem:** `gradFill` vs rasterize decision.
- [ ] **S2.6 · `s-case`** — light+dark hybrid; **subsystem:** per-slide background/theme handling.
- [ ] **S2.7 · `s-section`** — rotated condensed display type (reuses rotation).
- *(`s-title` done in E1.)*

**Each Story done when:** that section converts editable within <5px text drift and opens cleanly. **Epic gate:** all 8 sections pass; visual-diff <5px on >90% of text elements.

---

## E3 · Extended templates (`slides/extended-templates.html`)  — `TODO`

**Goal:** convert all 10 extended archetypes. This is where the rasterization fallback and table-like layouts get exercised.

- [ ] **S3.1 · `s-quadstats` + `s-playbook`** — grid-of-shapes "table" layouts.
- [ ] **S3.2 · `s-journey` + `s-roadmap`** — horizontal stage flows; **subsystem:** connectors (`<p:cxnSp>`).
- [ ] **S3.3 · `s-arch`** — heavy SVG architecture diagram; **subsystem:** SVG rasterization fallback (SPEC §5).
- [ ] **S3.4 · `s-persona`** — circular avatar (`ellipse`) + outline.
- [ ] **S3.5 · `s-scoping`** — table structure; **decide:** real `<a:tbl>` vs grid of shapes.
- [ ] **S3.6 · `s-services` + `s-team` + `s-usecase`** — mixed shapes+text; **subsystem:** overflow/ribbon positioning + z-order.

**Epic gate:** all 10 sections convert; visual-diff within DoD tolerance.

---

## E4 · Fidelity, fonts & real decks  — `TODO`

**Goal:** satisfy SPEC §8 Definition of Done on a real multi-slide deck.

- [ ] **S4.1 · Font embedding** — `<p:embeddedFontLst>` + font parts for Archivo Black + Nunito Sans; deck renders on a machine without them.
- [ ] **S4.2 · Visual-diff harness** — `tests/visual_diff.py` (Playwright PNG vs LibreOffice→PDF→PNG, Pillow heatmap, markdown report). Dev-only deps (SPEC §7).
- [ ] **S4.3 · Convert the Legacy deck end-to-end** — `decks/Legacy System X-Ray & Navigator.html`; tune drift to <5px on >90% of text across all 10 slides.
- [ ] **S4.4 · Generality check** — convert a brand-new deck built fresh from the templates; confirm the arbitrary-DOM walker handles bespoke section classes.
- [ ] **S4.5 · Limitations doc** — `tools/editable_pptx/README.md`: what works, what's rasterized, what's still broken.

**Epic gate:** SPEC §8 Definition of Done is met on the Legacy deck.

---

## E5 · Claude Code skill wiring (one-prompt workflow)  — `TODO`

**Goal:** a colleague opens Claude Code in this folder, gives a brief, and gets an editable `.pptx` with no manual steps.

- [ ] **S5.1 · Author-and-export flow** — extend the skill so Claude, given a brief, writes `decks/<name>.html` from the templates, then runs `tools/editable_pptx/export.py`.
- [ ] **S5.2 · End-to-end dry run** — a colleague-style prompt → editable `.pptx`, zero manual steps in between.
- [ ] **S5.3 · Colleague onboarding** — per-machine `scripts/setup.sh` + a short "how to use" doc.

**Epic gate:** from a single prompt in this folder, a colleague gets an editable native-PowerPoint deck.

---

## Backlog (not scheduled)

- `<a:custGeom>` for SVG paths that repeat across many slides (instead of rasterizing each).
- Auto text-fit: heuristic to widen a text box `cx` by 1–2% when PowerPoint wraps a word differently than CSS.
- Speaker notes.
- Chart support (render-to-image until a real need appears).
- CI to run the unit tests + a smoke export on every change.
