---
name: church-media-design
description: Design standard and end-to-end procedure for PEFA Magina Cathedral media (posters, public notices, flyers, social posts, projection slides, livestream cards, lower-thirds and overlays, giving/QR slides, print handouts). Covers brief → HTML master → render → review loop → Canva (via html-to-canva) → per-platform export set, print PDF, file naming and handover. Use this whenever the user asks for any church graphic, notice, announcement, slide, screen, overlay, thumbnail-style poster or QR code for PEFA Magina (pefamagina.com), even if they only say "make one for the church", "for the screens", "for the stream" or "for WhatsApp/Instagram/TikTok".
---

# Church media design (PEFA Magina)

The bar is the media notice of Nov 2026 (camera hero, "YOU MAY BE / ON CAMERA"), which the user
signed off after six review rounds. Every new piece should land at that level on the first
render, so the user spends their rounds on taste, not on fixing basics. The rules below are
the decisions from those rounds. Each has a reason; apply them, don't rediscover them.

## Workflow (in order)

1. **Brief.** Get: purpose and audience; *event-specific or general church use* (this changes
   the palette, see design-standard); every platform/screen it goes to; exact wording, numbers
   and links. Ask only for what you can't verify. Look at the user's references (Ruach,
   City Lighters, Life Church Limuru, Elevation…) for structure, not for copying.
2. **HTML master.** One generator script with one preset per size (positions per preset, same
   content). Fonts via `@font-face` to local static TTFs, absolute layout, real text.
   Details: `references/workflow.md`.
3. **Render and look.** `scripts/render.sh in.html out.png W H [scale]` (headless Chromium).
   Look at every render yourself at full size *and* zoomed (icons, edges, small text) before
   showing it. Fix what the checklist catches before the user sees it.
4. **Review loop with the user.** Show the PNG inline. Change one thing per message they send;
   keep the previous version as `name-vN.html` so any step can be undone. Record decisions in
   memory as they happen.
5. **Canva** (when the user wants it editable or "in Canva"): use the **html-to-canva** skill
   (`cv init/lint/build`, import, export, `cv audit`, `cv calibrate`, re-import, `cv accept`).
   One import per size; a Codex child with the Canva connector merges them into **one
   multi-page project**; page titles are set in the editor (the connector can't).
   Details and gotchas: `references/workflow.md#canva`.
6. **Export set and handover.** Per-platform PNGs, A4 print PDF with vector text, CAPS
   numbered file names, one zip. Sizes, naming, WhatsApp delivery: `references/export-handover.md`.

Projection slides and livestream cards follow the same path; mockups first (HTML + PNG,
several variations, one recommended), Canva only after the user picks a direction.

## Non-negotiables

- **People photos are cut out only, never retouched**: no tone, brightness, smoothing or object
  removal; only a meticulous cut with a soft, even edge (≈3 px ramp at final size).
- **Content carries the page.** Photo/scene is atmosphere *behind* the words (dimmed, tinted,
  veiled); the headline and message sit on top and read first.
- **Restraint.** One accent colour doing a job; no glow/"shine" on type or badges; no boxed
  callouts with side bars (reads "old school"); no HUD gimmicks (REC/LIVE tags) unless asked.
- **Generous margins**: ≥10% of width at the sides on social (108 px at 1080), footer well
  clear of the bottom edge.
- **Facts are exact**: names, numbers, links, Paybill/account, dates. Never invent; use a
  visible placeholder (`Paybill ______`) when a fact is missing, and say so.
- **QR codes**: error correction H, 4-module quiet zone, decoded by machine before handover,
  never a `#fragment` link, UTM per channel. `references/qr-codes.md`, `scripts/qr.py`.
- **Two funds never look alike**: cathedral-building giving (pefamagina.com/build) vs tithes &
  offering are visually distinct, and the building one is never called general giving.

## References

| File | Read when |
|---|---|
| `references/design-standard.md` | before the first render: palettes, type, logo, hierarchy, icons, footer |
| `references/workflow.md` | building the generator, rendering, Canva stage |
| `references/export-handover.md` | sizes per platform, PNG vs JPG, print PDF, naming, zip, WhatsApp |
| `references/qr-codes.md` | any slide or print item with a QR code |
| `references/checks-and-lessons.md` | before showing anything, and before handover |

## Scripts

- `scripts/render.sh in.html out.png W H [scale]`: screenshot with headless Chromium
  (`$CHROME`, Playwright's Chromium, or a system Chromium).
- `scripts/qr.py`: make QR codes (level H, SVG + PNG) and verify every one decodes to the
  exact URL. First run creates its own venv (`segno`, `zxing-cpp`, `pillow`) in
  `scripts/.venv` (override with `CMD_VENV`).
