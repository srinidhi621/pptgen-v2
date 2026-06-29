# Editable PPTX Pipeline — Weekend Project Prompt

> **Paste this entire file at the start of a Claude Code session.** It sets context, defines roles, lays out the architecture, and breaks the work into shippable phases.

---

## 0 · Context (you must read this first)

I have an existing Ascendion design-system skill at:

```
/Users/Srinidhi/my_projects/ppt-gen-v2```

It contains:
- `README.md` + `SKILL.md` — brand foundations, content rules, voice
- `CLAUDE_CODE.md` — the existing Designer/Verifier/Exporter pipeline
- `colors_and_type.css` — design tokens
- `slides/index.html` — 8 corporate master templates
- `slides/extended-templates.html` — 10 team archetypes
- `slides/deck-stage.js` — runtime (scaling, navigation, print, slide indexing)
- `decks/Legacy System X-Ray & Navigator.html` — a finished 10-slide reference deck
- `tools/verify_deck.py` and `tools/export_deck.py` — the current pipeline (screenshot-mode PPTX only)
- `assets/` — logos, brand imagery, badges

**Read all of the above before writing any code.** Spend the first 15 minutes orienting. Use `cat`, `head`, `wc -l`. Don't skim.

## 1 · The goal (what we're building)

A **DOM-to-OOXML converter** that takes an HTML deck (built from the skill's templates) and emits a fully **editable** PowerPoint file. "Editable" means:

- Every text block is a native PowerPoint text box (you can click and retype)
- Every shape (rectangle, rounded rect, ellipse, line) is a native PowerPoint shape (right-click → Format Shape works)
- Every image is embedded as an actual image (not flattened into a slide screenshot)
- Fonts, colors, gradients, positions, rotations preserved
- Opens cleanly in PowerPoint for Mac, PowerPoint for Windows, and Keynote

This sits **alongside** the existing screenshot-mode exporter — don't remove it; the new code is `tools/editable_pptx/`.

## 2 · The contract

```bash
# Existing screenshot-mode (keep working):
python tools/export_deck.py decks/MyDeck.html --pptx

# New editable mode:
python tools/editable_pptx/export.py decks/MyDeck.html
# → decks/MyDeck.pptx  (native shapes, native text)
```

Same HTML in, "real" PowerPoint out.

---

## 3 · OOXML fundamentals (the 30-minute crash course)

A `.pptx` is a ZIP with this structure:

```
[Content_Types].xml          ← MIME types for every part
_rels/.rels                  ← root relationships
ppt/
  presentation.xml           ← slide list, size, master refs
  presProps.xml, viewProps.xml, tableStyles.xml
  theme/theme1.xml           ← color/font theme
  slideMasters/slideMaster1.xml
  slideMasters/_rels/slideMaster1.xml.rels
  slideLayouts/slideLayout1.xml … slideLayout11.xml  (11 standard layouts)
  slideLayouts/_rels/*
  slides/slide1.xml … slideN.xml
  slides/_rels/slideN.xml.rels
  media/image1.png, image2.jpeg, …
  _rels/presentation.xml.rels
```

**Slide dimensions** at 16:9 1920×1080:
- Slide size: `cx="12192000" cy="6858000"` (EMU)
- **1 inch = 914400 EMU**
- **1 pt = 12700 EMU**
- **1 CSS px at 1920px slide width = 6350 EMU** (since 12192000 / 1920)

### Anatomy of a slide XML

```xml
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <!-- spTree must start with required group properties -->
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6858000"/>
                          <a:chOff x="0" y="0"/><a:chExt cx="12192000" cy="6858000"/></a:xfrm></p:grpSpPr>

      <!-- A rectangle with mint fill at (100, 100) sized 800×200 px -->
      <p:sp>
        <p:nvSpPr><p:cNvPr id="2" name="Rect"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="635000" y="635000"/><a:ext cx="5080000" cy="1270000"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:solidFill><a:srgbClr val="2CDCAA"/></a:solidFill>
          <a:ln><a:noFill/></a:ln>
        </p:spPr>
        <p:txBody>
          <a:bodyPr wrap="square" rtlCol="0" anchor="ctr"/>
          <a:lstStyle/>
          <a:p>
            <a:pPr algn="ctr"/>
            <a:r>
              <a:rPr lang="en-US" sz="3200" b="1">
                <a:solidFill><a:srgbClr val="0A0A0F"/></a:solidFill>
                <a:latin typeface="Archivo Black"/>
              </a:rPr>
              <a:t>Hello, World</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
```

Key things to memorize:
- `<p:sp>` = shape (with optional `<p:txBody>` for text)
- `<p:pic>` = picture (image)
- `<p:cxnSp>` = connector / line
- `<a:xfrm>` = position + size (in EMU)
- `<a:prstGeom prst="rect|roundRect|ellipse|line">` = preset geometry
- `<a:solidFill>`, `<a:gradFill>` = fills
- `<a:rPr sz="...">` = text size in **hundredths of a point** (sz="3200" = 32pt)
- `<a:latin typeface="...">` = font family
- IDs (`id="N"`) must be unique and ≥ 2 across the slide (1 is reserved for the group)

### A minimal `[Content_Types].xml`

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Override PartName="/ppt/presentation.xml"
            ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <!-- one Override per slide, slideLayout, slideMaster, theme -->
</Types>
```

Tip: **the fastest way to internalize OOXML is to unzip an existing simple `.pptx` and read the XML.** Make a one-slide PowerPoint, save it, rename to `.zip`, unzip, study. Do this on day 1.

### `python-pptx` is your ally for boilerplate

Use it to bootstrap the presentation skeleton, slide masters, theme, content types, relationships — the parts that are boring and tedious. Then **bypass its high-level API** and inject your own slide XML via the `_element` attribute. Pattern:

```python
from pptx import Presentation
from pptx.util import Emu
from lxml import etree

prs = Presentation()  # template with one default slide master
prs.slide_width = Emu(12192000)
prs.slide_height = Emu(6858000)

# Add a blank slide using the existing blank layout
blank = prs.slide_layouts[6]
slide = prs.slides.add_slide(blank)

# Now inject our own shapes by manipulating slide.shapes._spTree directly
sp_tree = slide.shapes._spTree
sp_tree.append(etree.fromstring("""
<p:sp xmlns:a="..." xmlns:p="...">
  ...
</p:sp>
"""))

prs.save("output.pptx")
```

This gets you a valid PPTX with all the relationships hooked up correctly while still giving you full control over slide content.

---

## 4 · Architecture

```
HTML deck                                      Editable PPTX
   │                                                ▲
   ▼                                                │
[1. Capture]  Playwright + DOM walker               │
   │   Walk each slide, capture every element       │
   │   with bounds + computed styles                │
   ▼                                                │
[2. Classify]  Decide what each element becomes:    │
   │   text-leaf / shape / image / group / skip     │
   ▼                                                │
[3. Translate]  Map captured → OOXML primitives:    │
   │   • CSS rgb → <a:srgbClr>                      │
   │   • px bounds → EMU coords                     │
   │   • inline runs (<b>, <em>, <span>) → <a:r>    │
   │   • complex SVG → rasterized PNG (fallback)    │
   │   • background-clip:text → rasterized PNG      │
   ▼                                                │
[4. Emit]  Build the .pptx zip ───────────────────►─┘
       Use python-pptx for skeleton (theme, masters,
       relationships, content types). Inject raw XML
       for slide bodies.
```

### What HAS to be rasterized (escape hatches)

Some HTML features have no clean OOXML equivalent. Detect and rasterize:

1. **`background-clip: text`** — our photo-knockout headlines
2. **Complex SVG paths** — architecture diagrams with >20 path elements
3. **CSS filters** (`filter:`, `backdrop-filter:`)
4. **Pseudo-elements with non-trivial content** — keep `::before/::after` with simple shapes (we already query them), but if they have backgrounds + transforms + content all at once, rasterize the parent.
5. **Anything that prints inconsistently** — when in doubt, screenshot just that element and embed as image.

Rasterization is a **per-element** escape, not a per-slide one. The rest of the slide stays editable.

### How to rasterize one element

```python
# Take a screenshot of a specific element at 2x DPI
elem = page.locator(f"[data-capture-id='{eid}']")
elem.screenshot(path=tmp, omit_background=False, type='png', scale='device')
```

Then embed the PNG at the same bounds as the original element.

---

## 5 · Project structure

```
/Users/Srinidhi/my_projects/ppt-gen-v2/tools/editable_pptx/
├── README.md              ← architecture notes, gotchas, OOXML cheatsheet
├── export.py              ← orchestrator / CLI entrypoint
├── capture.py             ← Playwright DOM walker → JSON IR
├── ir.py                  ← intermediate representation dataclasses
├── classify.py            ← element role inference (text-leaf / shape / image / group)
├── translate.py           ← IR → OOXML element strings
├── emit.py                ← assemble the .pptx zip via python-pptx + injection
├── rasterize.py           ← Playwright per-element screenshot fallback
├── fonts.py               ← font-family normalization, optional embedding
├── colors.py              ← CSS color parsing → hex
├── units.py               ← px ↔ EMU conversions
├── xml_helpers.py         ← namespaced XML construction utilities
└── tests/
    ├── test_units.py
    ├── test_colors.py
    ├── test_capture_minimal.py    ← test on a hand-crafted 1-slide HTML
    └── fixtures/
        └── minimal.html
```

**Discipline:** every module < 300 lines. Split aggressively. The whole pipeline should fit in your head — if a module grows past 300 lines, find the seam and split it.

---

## 6 · Build plan — phased shipping

You will not get this right in one shot. **Ship vertical slices**, each producing a valid PPTX, each adding one capability.

### Phase 0 · Bootstrap (1–2 hours)

- Create project structure.
- Crack open a hand-made one-slide PowerPoint to study OOXML. Save artifacts to `tools/editable_pptx/reference/`.
- Write `units.py` and `colors.py` with unit tests. These are the only things you'll write twice if you get them wrong.
- Write `emit.py` that produces a valid PPTX with one slide containing one hardcoded mint rectangle and one hardcoded text box. **Verify it opens cleanly in PowerPoint** before going further.

### Phase 1 · Title slide only (4–6 hours)

Target deck: `slides/index.html` slide 1 (`.s-title`).

- Write `capture.py`: navigate to slide 1, walk the DOM, output JSON IR with bounds + key computed styles.
- Write `classify.py`: identify the headline text, the eyebrow, the subtitle, the deck-meta fields, the background image, the wordmark.
- Write `translate.py` + `emit.py`: emit each as a native PowerPoint primitive.
- **Don't try to do the hero photo's overlay effects yet** — rasterize the photo + scrim as one image.
- **End state:** open the output `.pptx` in PowerPoint, click the headline, retype "Foo Bar" → it changes. Done.

### Phase 2 · The 8 corporate templates (1 full day)

Target: every section in `slides/index.html`.

Each template introduces new requirements:
- `.s-stats` — stat grid (multiple identical text boxes, large numbers with sup)
- `.s-three` — three-column cards with backgrounds (rounded rects + nested text)
- `.s-quote` — rotated mega type (CSS `rotate(-9deg)` → PowerPoint shape rotation)
- `.s-offer` — pillars with bordered cards
- `.s-award` — gradient text (rasterize), photo column
- `.s-case` — light + dark hybrid
- `.s-section` — rotated condensed type

Build each in order. After each one: render, open in PowerPoint, fix the diffs. Don't move on until the previous template is solid.

Specifically attack these subsystems as you go:
- **Inline runs** — handle `<sup>`, `<b>`, `<span style="color: ...">` within a single paragraph
- **Gradients** — emit `<a:gradFill>` for linear, rasterize for complex
- **Rotation** — CSS `transform: rotate(Xdeg)` → shape `<a:xfrm rot="ANGLE60000">` (PowerPoint stores rotation in 60000ths of a degree)
- **Border-radius** → `<a:prstGeom prst="roundRect">` with adjustment value

### Phase 3 · Extended templates (1 day)

Target: every section in `slides/extended-templates.html`.

- `.s-quadstats`, `.s-journey`, `.s-playbook` — table-like layouts
- `.s-arch` — heavy SVG content; this is where rasterization fallback shines
- `.s-persona` — circular avatar (ellipse), border (outline)
- `.s-scoping` — table structure (might be cleanest emitted as a real `<a:tbl>`)
- `.s-services`, `.s-team`, `.s-roadmap`, `.s-usecase` — mixed shapes + text

Big learnings expected here:
- When SVG is unavoidable, do you convert simple paths to `<a:custGeom>` or just rasterize? **Default: rasterize.** Convert paths only when the same SVG repeats across many slides.
- Negative/overflow positioning (e.g. ribbons sticking out of cards) — handle with z-order + bounds outside parent
- Text autofit settings: use `<a:noAutofit/>` so PowerPoint doesn't resize text on edit

### Phase 4 · Polish & integration (1 day)

- Run on every deck in `decks/` and visually compare to HTML render
- Build the visual-diff harness (see "Verification" below)
- Add font embedding (`<p:embeddedFontLst>`) for Archivo Black + Nunito Sans so the deck looks right on machines without those fonts
- Wire the orchestrator: `python tools/editable_pptx/export.py decks/MyDeck.html` → done
- Document limitations in `tools/editable_pptx/README.md`

---

## 7 · Sub-agent roles

Use the `Task` tool to spawn these. The main agent is the **Architect/Builder**; spawn the others as needed.

### Architect (primary)

You hold the whole pipeline in your head. You read existing files before writing. You sketch the data flow before writing code. You split modules when they get big. You don't commit to a design until you've traced one end-to-end example through it.

### Builder (primary)

You implement one module at a time, with tests. You don't write a module that fails its tests. You verify each `.pptx` opens in PowerPoint before moving on. **You don't trust that "it generates a file" means "it works"** — broken `.pptx` files often open with PowerPoint silently dropping shapes; check that the rendered shapes match.

### Visual Verifier (sub-agent)

Spawn after each phase. Task description:

> Render `decks/Legacy System X-Ray & Navigator.html` to PNG via Playwright at 1920×1080 per slide. Then convert the generated `decks/Legacy System X-Ray & Navigator.pptx` to PNG via LibreOffice headless: `libreoffice --headless --convert-to pdf <pptx>`, then `pdftoppm -r 144 <pdf> out`. Compare per-slide PNGs side-by-side. Output a markdown report listing every visible regression: text position drift, missing shapes, color mismatch, wrong font. Be specific: "slide 5, headline shifted right by ~12px" not "looks slightly off."

The Verifier returns a list. Builder fixes. Iterate.

### Editorial Tester (manual, you ask the user)

After the pipeline reports done, **ask the user to manually open the PPTX in PowerPoint locally** and check:
- Click each text block — does the cursor appear and can you type?
- Right-click a shape — does "Format Shape" show the right fill / outline / size?
- Are images selectable and resizable, or have they fused into a slide background?
- Try changing the headline of slide 1. Save. Reopen. Did it persist?

This is the editability gate. Screenshot-perfect output that isn't editable defeats the project.

---

## 8 · References to study

- **python-pptx source** — `pptx/oxml/ns.py` for namespaces, `pptx/oxml/shapes/` for shape XML schemas. https://github.com/scanny/python-pptx
- **ECMA-376** — the OOXML spec, especially Part 1 §19 (DrawingML) and §20 (PresentationML). Massive but searchable.
- **OOXML cheatsheet** — https://officeopenxml.com/prSlide.php — the most readable overview of slide XML
- **Office Open XML Sample** — Microsoft's `Open-XML-SDK` repo has C# samples that show clean XML output. The C# is irrelevant; read the produced XML.

Make a habit: when adding any new feature, **find an existing PowerPoint deck that has that feature**, save it, unzip it, and copy the XML pattern. Don't invent OOXML — copy what Microsoft Office emits.

---

## 9 · Verification harness

Build this early; you'll lean on it daily.

```python
# tools/editable_pptx/tests/visual_diff.py

# 1. Render HTML deck to per-slide PNGs at 1920×1080 (Playwright)
# 2. Convert generated PPTX → PDF → per-page PNGs (LibreOffice + pdftoppm)
# 3. For each slide, output side-by-side comparison: html.png | pptx.png
# 4. Compute pixel-diff heatmap (Pillow) and write a markdown report
```

You should be able to run:

```bash
python tools/editable_pptx/tests/visual_diff.py decks/MyDeck.html
# → produces tests/diffs/<deck>/slide-NN.png comparison images
# → produces tests/diffs/<deck>/report.md
```

Re-run after every meaningful change. Track per-slide drift.

---

## 10 · Honest caveats — communicate these to the user

When you hit these, **tell the user, don't paper over them**:

1. **Text wrapping is the hardest part.** CSS wraps based on font-metric measurement; PowerPoint wraps based on font-metric measurement too — but with a slightly different algorithm. Expect 1–3px drift per line. If a headline wraps at "Word X" in HTML and "Word X-1" in PowerPoint, the fix is usually widening the text-box's `cx` by 1–2%.

2. **Subscript/superscript** — sup is `<a:rPr baseline="30000">` (30000 = 30% baseline shift). Sub is negative. The size doesn't auto-shrink the way browsers do; you have to set `sz` smaller manually.

3. **`text-wrap: balance`** — no OOXML equivalent. Pre-balance in HTML by inserting explicit `<br>` if needed before capture.

4. **`-webkit-background-clip: text`** — rasterize the element. Mark it `data-rasterize="true"` in the HTML so capture knows to skip walking into it.

5. **Pseudo-elements with `content: "—"` or symbols** — capture by reading `getComputedStyle(el, '::before')['content']` and emitting an extra synthetic text run. Mostly fine.

6. **CSS Grid bounding boxes** — children of a CSS Grid have correct `getBoundingClientRect()` values; the grid itself doesn't matter for OOXML since we emit absolute positions. So you can ignore the grid container and just emit the grid items as absolutely-positioned shapes.

7. **Fonts not on viewer machine** — embed them. PPTX font embedding is `<p:embeddedFontLst><p:embeddedFont><p:font typeface="..."/><p:regular r:embed="..."/></p:embeddedFont>...</p:embeddedFontLst>` in `presentation.xml`, plus the font file as a `application/x-fontdata` part. Worth the lift for client-facing decks.

---

## 11 · Definition of done

The project is done when:

- [x] `python tools/editable_pptx/export.py decks/Legacy System X-Ray & Navigator.html` produces a `.pptx` that opens cleanly in PowerPoint for Mac
- [x] Every text element is editable (click + retype works)
- [x] Every non-rasterized shape is a real `<p:sp>` (Format Shape works in PowerPoint)
- [x] Visual-diff report shows <5px drift on >90% of text elements across all 10 slides
- [x] Same pipeline works for any deck in `decks/` and any new deck built from the skill's templates
- [x] `tools/editable_pptx/README.md` documents what works, what's rasterized, what's still broken

**Out of scope** — be ruthless:
- Animations, transitions, slide timings
- Speaker notes (until v2)
- Non-16:9 aspect ratios
- Tables with merged cells (use simple grids of shapes instead — that's what our templates do anyway)
- Charts (we don't have any; if we add them, render to image and embed)

---

## 12 · First message you should write back to me

When you've read this prompt and the skill files, write back a structured message:

```
## Orientation summary

I've read:
- [list every file you read]

Key facts I've learned:
- [3–5 specific things from the skill that matter for this build]

## Proposed Phase 0 plan

Today I will:
- [concrete step]
- [concrete step]
- [concrete step]

I'll stop and check in with you when:
- [concrete checkpoint]

## Questions before I start

- [any clarifications — don't fabricate; ask if unsure]
```

Then wait for my "go" before writing any code.
