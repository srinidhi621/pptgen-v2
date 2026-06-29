#!/usr/bin/env python3
"""
verify_deck.py — open an HTML deck in headless Chromium, screenshot each
slide at native 1920×1080, and check for DOM-level overflow violations.

Usage:
    python tools/verify_deck.py decks/<deck-name>.html
    python tools/verify_deck.py decks/<deck-name>.html --out screenshots/

Output:
    A folder of per-slide PNG screenshots + a JSON report printed to stdout.
    Exit code 0 if all slides pass; 1 if any slide has overflow.

Assumes the deck uses <deck-stage> with the goTo(n) API exposed
(true for every deck built from this skill).
"""

import argparse
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def verify(html_path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"deck": str(html_path), "slides": [], "console_errors": []}

    with sync_playwright() as p:
        # Uses your installed Google Chrome instead of Playwright's bundled
        # Chromium — saves the ~150MB download. To use bundled instead,
        # change to: p.chromium.launch()
        browser = p.chromium.launch(channel="chrome")
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        page.on("console", lambda msg: (
            report["console_errors"].append(msg.text)
            if msg.type == "error" else None
        ))

        page.goto(html_path.absolute().as_uri(), wait_until="networkidle")

        # Force deck-stage out of its scaled mode so screenshots are 1:1.
        page.evaluate("""
            const ds = document.querySelector('deck-stage');
            if (ds) ds.setAttribute('noscale', '');
        """)
        # Let the layout settle.
        page.wait_for_timeout(400)

        total = page.evaluate("document.querySelector('deck-stage').length")
        print(f"Found {total} slides", file=sys.stderr)

        for i in range(total):
            page.evaluate(f"document.querySelector('deck-stage').goTo({i})")
            page.wait_for_timeout(350)  # transition settle

            # Screenshot the active slide
            slide_path = out_dir / f"slide-{i+1:02d}.png"
            slide_el = page.locator("deck-stage section[data-deck-active]")
            slide_el.screenshot(path=str(slide_path))

            # Overflow check: walk every descendant and flag anything that
            # bottoms-out below 1080 or extends right of 1920. Chrome
            # bottom-pads scrolling, so use getBoundingClientRect relative
            # to the slide root.
            violations = page.evaluate("""
                () => {
                    const slide = document.querySelector('deck-stage section[data-deck-active]');
                    if (!slide) return [];
                    const sb = slide.getBoundingClientRect();
                    const W = sb.width, H = sb.height;
                    const out = [];
                    slide.querySelectorAll('*').forEach(el => {
                        const r = el.getBoundingClientRect();
                        const right = r.right - sb.left;
                        const bottom = r.bottom - sb.top;
                        if (bottom > H + 2 || right > W + 2) {
                            // Skip absolutely-positioned chrome that's intentionally placed
                            // (data-noncommentable, page numbers, etc.) — chrome is fine
                            // even if it touches the edge.
                            const tag = el.tagName.toLowerCase();
                            const cls = (el.className || '') + '';
                            if (cls.includes('chrome-') || cls.includes('tapzone')) return;
                            out.push({
                                tag, cls: cls.slice(0, 60),
                                text: (el.textContent || '').trim().slice(0, 60),
                                right: Math.round(right), bottom: Math.round(bottom),
                                overflowX: Math.round(right - W),
                                overflowY: Math.round(bottom - H),
                            });
                        }
                    });
                    return out;
                }
            """)

            label = page.evaluate(
                "document.querySelector('deck-stage section[data-deck-active]').getAttribute('data-screen-label')"
            ) or f"Slide {i+1}"

            report["slides"].append({
                "index": i + 1,
                "label": label,
                "screenshot": str(slide_path),
                "violations": violations,
            })

            status = "PASS" if not violations else f"OVERFLOW × {len(violations)}"
            print(f"  [{i+1:2d}/{total}] {label} — {status}", file=sys.stderr)

        browser.close()

    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path, help="Path to deck HTML")
    ap.add_argument("--out", type=Path, default=None, help="Screenshot output dir")
    args = ap.parse_args()

    if not args.html.exists():
        print(f"ERROR: {args.html} does not exist", file=sys.stderr)
        return 2

    out = args.out or args.html.parent / f".verify-{args.html.stem}"
    report = verify(args.html, out)

    # Pretty JSON to stdout for the agent to read
    print(json.dumps(report, indent=2))

    total_violations = sum(len(s["violations"]) for s in report["slides"])
    print(f"\nDone. {len(report['slides'])} slides, "
          f"{total_violations} overflow violation(s), "
          f"{len(report['console_errors'])} console error(s).", file=sys.stderr)
    print(f"Screenshots → {out}/", file=sys.stderr)

    return 0 if total_violations == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
