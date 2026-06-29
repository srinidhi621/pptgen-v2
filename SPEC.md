# SPEC — Editable PPTX Converter (Route A)

> Technical source of truth for the HTML→OOXML converter. Pairs with **[`PLAN.md`](PLAN.md)** (the execution board). This doc owns *what we are building and how it works*; PLAN owns *the order we build it in and where we are*.

---

## 1 · Goal

Turn an HTML deck — authored by Claude from the templates in `slides/` — into a fully **editable** PowerPoint file. "Editable" means:

- Every text block is a native PowerPoint text box (click and retype).
- Every shape (rectangle, rounded rect, ellipse, line) is a native PowerPoint shape (right-click → Format Shape works).
- Every image is an embedded image (not a flattened slide screenshot).
- Fonts, colors, gradients, positions, rotations are preserved.
- Opens cleanly in PowerPoint for Mac, PowerPoint for Windows, and Keynote.

This is **additive**. The existing screenshot-mode exporter (`tools/export_deck.py`) stays as a fallback; the new code lives in `tools/editable_pptx/`.

### Non-negotiable design facts

1. **The converter walks arbitrary DOM.** It must not assume a fixed set of template classes. Real decks invent their own sections — `decks/Legacy System X-Ray & Navigator.html` uses `s-problem`, `s-compare`, `s-pipeline`, `s-tier`, `s-diff`, `s-outcomes`, `s-engage`, none of which exist in `slides/`. The walker reads back whatever the browser renders.
2. **A headless browser is required**, because CSS grid/flexbox positions don't exist until a layout engine computes them. Use **bundled Chromium** (`playwright install chromium`), never `channel="chrome"` — the tool must be self-contained on every colleague's machine and not depend on a system browser.
3. **The browser is invisible to the user.** It runs inside the export script Claude invokes; colleagues never launch it or install anything beyond the one-time setup.

---

## 2 · Contract

```bash
# Existing screenshot-mode (keep working, not editable):
python tools/export_deck.py decks/MyDeck.html --pptx

# New editable mode:
python tools/editable_pptx/export.py decks/MyDeck.html
# → decks/MyDeck.pptx   (native shapes, native text)
```

Same HTML in, real PowerPoint out. Output lands next to the input HTML.

---

## 3 · Architecture

```
HTML deck                                      Editable PPTX
   │                                                ▲
   ▼                                                │
[1. Capture]  Playwright (bundled Chromium)         │
   │   Render the deck; walk each slide's DOM,      │
   │   capture every element's bounds +             │
   │   computed styles → JSON IR                    │
   ▼                                                │
[2. Classify]  Decide what each element becomes:    │
   │   text-leaf / shape / image / group / skip /   │
   │   rasterize                                    │
   ▼                                                │
[3. Translate]  Map captured → OOXML primitives:    │
   │   • CSS rgb → <a:srgbClr>                      │
   │   • px bounds → EMU coords                     │
   │   • inline runs (<b>, <em>, <span>, <sup>) →   │
   │     <a:r>                                      │
   │   • rotation → <a:xfrm rot="...">              │
   │   • border-radius → prst="roundRect"           │
   │   • complex SVG / clip-text / filters →        │
   │     rasterized PNG (escape hatch)              │
   ▼                                                │
[4. Emit]  Build the .pptx zip ───────────────────►─┘
       python-pptx for the skeleton (theme, masters,
       relationships, content types). Inject raw XML
       for slide bodies.
```

### Module layout

```
tools/editable_pptx/
├── README.md          ← gotchas, what's rasterized, what's still broken
├── export.py          ← orchestrator / CLI entrypoint
├── capture.py         ← Playwright DOM walker → JSON IR
├── ir.py              ← intermediate representation dataclasses
├── classify.py        ← element role inference
├── translate.py       ← IR → OOXML element strings
├── emit.py            ← assemble the .pptx via python-pptx + injection
├── rasterize.py       ← Playwright per-element screenshot fallback
├── fonts.py           ← font-family normalization + embedding
├── colors.py          ← CSS color parsing → hex
├── units.py           ← px ↔ EMU conversions
├── xml_helpers.py     ← namespaced XML construction utilities
└── tests/
    ├── test_units.py
    ├── test_colors.py
    ├── test_capture_minimal.py
    └── fixtures/minimal.html
```

**Discipline:** every module < 300 lines. If one grows past that, find the seam and split.

---

## 4 · OOXML reference

A `.pptx` is a ZIP:

```
[Content_Types].xml          ← MIME types for every part
_rels/.rels                  ← root relationships
ppt/
  presentation.xml           ← slide list, size, master refs
  presProps.xml, viewProps.xml, tableStyles.xml
  theme/theme1.xml           ← color/font theme
  slideMasters/slideMaster1.xml  (+ _rels)
  slideLayouts/slideLayout1.xml … slideLayout11.xml  (+ _rels)
  slides/slide1.xml … slideN.xml  (+ _rels)
  media/image1.png, image2.jpeg, …
  _rels/presentation.xml.rels
```

### Units (16:9, 1920×1080)

- Slide size: `cx="12192000" cy="6858000"` (EMU)
- **1 inch = 914400 EMU**
- **1 pt = 12700 EMU**
- **1 CSS px at 1920px slide width = 6350 EMU** (12192000 / 1920)
- Rotation is stored in **60000ths of a degree** (`rot="ANGLE * 60000"`)
- Font size `sz` is in **hundredths of a point** (`sz="3200"` = 32pt)
- Superscript baseline: `<a:rPr baseline="30000">` (30%); subscript is negative

### Anatomy of a slide

```xml
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6858000"/>
                          <a:chOff x="0" y="0"/><a:chExt cx="12192000" cy="6858000"/></a:xfrm></p:grpSpPr>

      <!-- mint rectangle at (100,100)px sized 800×200px -->
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

Key elements:
- `<p:sp>` = shape (with optional `<p:txBody>`)
- `<p:pic>` = picture · `<p:cxnSp>` = connector/line
- `<a:xfrm>` = position + size (EMU) · `<a:prstGeom prst="rect|roundRect|ellipse|line">` = geometry
- `<a:solidFill>`, `<a:gradFill>` = fills · `<a:latin typeface="...">` = font
- IDs must be unique and ≥ 2 per slide (1 is the group)

### python-pptx as skeleton, raw XML for bodies

Use python-pptx to bootstrap the boilerplate (masters, theme, content types, relationships), then inject your own slide XML via `_spTree`:

```python
from pptx import Presentation
from pptx.util import Emu
from lxml import etree

prs = Presentation()
prs.slide_width = Emu(12192000)
prs.slide_height = Emu(6858000)

slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
slide.shapes._spTree.append(etree.fromstring("<p:sp …>…</p:sp>"))
prs.save("output.pptx")
```

This yields a valid PPTX with correct relationships while giving full control over content.

> **Don't invent OOXML — copy it.** When adding a feature, make a one-slide PowerPoint that has it, save, rename `.pptx`→`.zip`, unzip, and copy the XML pattern. Stash references in `tools/editable_pptx/reference/`.

---

## 5 · Escape hatches (what must be rasterized)

Some HTML has no clean OOXML equivalent. Detect and rasterize **per element** — the rest of the slide stays editable:

1. **`background-clip: text`** — photo-knockout headlines (the hero "A", photo-filled words)
2. **Complex SVG** — architecture diagrams with many path elements (`.s-arch`)
3. **CSS filters** (`filter:`, `backdrop-filter:`)
4. **Pseudo-elements** combining background + transform + content at once
5. **Anything that prints inconsistently** — when in doubt, screenshot just that element

Authors can force this by marking an element `data-rasterize="true"` so capture skips walking into it.

```python
elem = page.locator(f"[data-capture-id='{eid}']")
elem.screenshot(path=tmp, type='png', scale='device')  # 2x DPI
```

Embed the PNG at the original element's bounds.

**Default for SVG: rasterize.** Convert paths to `<a:custGeom>` only when the same SVG repeats across many slides.

---

## 6 · Known limitations (communicate these honestly)

1. **Text wrapping is the hardest part.** CSS and PowerPoint both wrap on font metrics but with slightly different algorithms — expect 1–3px drift per line. If a headline wraps a word differently, widen the text-box `cx` by 1–2%.
2. **Sub/superscript** don't auto-shrink like browsers do — set `sz` smaller manually alongside the `baseline` shift.
3. **`text-wrap: balance`** has no OOXML equivalent — pre-balance with explicit `<br>` before capture if needed.
4. **Fonts not on the viewer's machine** — embed them (`<p:embeddedFontLst>` in `presentation.xml` + the font file as an `application/x-fontdata` part). Required for Archivo Black + Nunito Sans, or decks reflow on machines that lack them.
5. **CSS Grid containers** can be ignored — children report correct `getBoundingClientRect()`, and we emit absolute positions anyway.
6. **Pseudo-element symbols** (`content: "—"`) — read via `getComputedStyle(el, '::before')` and emit a synthetic run.
7. **Autofit** — use `<a:noAutofit/>` so PowerPoint doesn't resize text when the user edits.

---

## 7 · Verification (developer/maintainer tool only)

Colleagues never need this. Whoever builds or tunes the converter uses a visual-diff harness:

```
tools/editable_pptx/tests/visual_diff.py <deck.html>
  1. Render HTML deck → per-slide PNGs at 1920×1080 (Playwright)
  2. Convert generated PPTX → PDF → per-page PNGs (LibreOffice + pdftoppm)
  3. Side-by-side comparison + pixel-diff heatmap (Pillow)
  4. Markdown report listing every regression, specifically:
     "slide 5, headline shifted right ~12px" — not "looks slightly off"
```

LibreOffice + Poppler are **dev dependencies**, not runtime ones. Re-run after every meaningful change; track per-slide drift.

---

## 8 · Definition of done

- [ ] `python tools/editable_pptx/export.py decks/Legacy System X-Ray & Navigator.html` produces a `.pptx` that opens cleanly in PowerPoint for Mac.
- [ ] Every text element is editable (click + retype works).
- [ ] Every non-rasterized shape is a real `<p:sp>` (Format Shape works).
- [ ] Visual-diff report shows <5px drift on >90% of text elements across all 10 slides.
- [ ] Same pipeline works for any deck in `decks/` and any new deck built from the templates.
- [ ] Fonts are embedded; the deck renders correctly on a machine without Archivo Black / Nunito Sans.
- [ ] `tools/editable_pptx/README.md` documents what works, what's rasterized, what's still broken.

### Out of scope (be ruthless)

- Animations, transitions, slide timings
- Speaker notes (defer)
- Non-16:9 aspect ratios
- Tables with merged cells (templates use grids of shapes instead)
- Charts (none exist; if added, render to image and embed)

---

## 9 · References

- **python-pptx source** — `pptx/oxml/ns.py` (namespaces), `pptx/oxml/shapes/` (shape XML). https://github.com/scanny/python-pptx
- **ECMA-376** — OOXML spec, Part 1 §19 (DrawingML), §20 (PresentationML).
- **OOXML cheatsheet** — https://officeopenxml.com/prSlide.php (most readable slide-XML overview).
- **Microsoft Open-XML-SDK** — C# samples; ignore the C#, read the XML it produces.
