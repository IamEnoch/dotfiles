---
name: media-design
description: Design standard and end-to-end procedure for any static visual deliverable, for any organisation in any field - posters, flyers, public and internal notices, announcements, event signage, menus, social posts, slides and title cards, projection and venue-screen graphics, livestream and webinar cards, lower-thirds and overlays, QR call-to-action and payment or donation cards, and print handouts. Covers brand profile → brief → HTML master → render → review loop → Canva (via the html-to-canva skill) → per-platform export set, print PDF, file naming and handover. Use this whenever the user asks for a poster, flyer, notice, announcement, slide, screen graphic, overlay, sign, social graphic or QR code, even if they only say "make one for the launch", "for the screens", "for the stream", "for WhatsApp/Instagram/TikTok" or "something to print", and even if they don't name this skill.
---

# Media design

A standard and a procedure for static visual pieces: a product-launch poster, a school notice,
a conference title slide, a charity appeal, a café menu, a webinar overlay. The aim is that the
first render already clears the basics (facts, hierarchy, margins, restraint, working QR
codes), so the user spends their review rounds on taste. Each rule below comes from a review
round where its absence was rejected. Apply them; don't rediscover them.

Everything that belongs to one organisation (name, colours, fonts, logo, links, payment
details, wording) lives in that project's **brand file**, never in this skill.

## Workflow (in order)

0. **Brand profile.** Look for `BRAND.md`, then `brand/BRAND.md`, in the project (then its
   parent folders). Read it fully before anything else. If there is none, ask the user for the
   key items and create one from the template in `references/brand-profile.md`. Never guess
   brand facts, and never carry them over from another project.
1. **Brief.** Get: purpose and audience; whether the piece is for *one event or campaign* or
   for *everyday use* (this can change the palette); every platform, screen and print size it
   goes to; the exact wording, numbers and links. Ask only for what you can't verify. Study
   the user's reference pieces for structure, not to copy.
2. **HTML master.** One generator script with one preset per size (positions per preset, same
   content). Fonts via `@font-face` to local static font files, absolute layout, real text.
   Details: `references/workflow.md`.
3. **Render and look.** `scripts/render.sh in.html out.png W H [scale]` (headless Chromium).
   Look at every render yourself at full size *and* zoomed (icons, edges, small text) before
   showing it. Fix what the checklist catches before the user sees it.
4. **Review loop with the user.** Show the PNG inline. One change per message they send; keep
   the previous version as `name-vN.html` so any step can be undone. Record decisions as they
   happen; lasting ones go into the brand file.
5. **Canva.** When the user wants the piece editable, "in Canva", or handed to a team that
   works in Canva, use the **`html-to-canva`** skill. It lints the HTML, compiles it to an
   importable file, audits Canva's export against the HTML by measurement, and calibrates.
   Start it only after the user has approved the HTML direction, because every later change
   costs a sync. A piece delivered only as PNG or PDF skips this stage.
   Details: `references/workflow.md` (Canva stage).
6. **Export set and handover.** Per-platform PNGs, a print PDF with vector text, numbered
   file names, one zip. Sizes, naming and lossless delivery: `references/export-handover.md`.

Slides, venue-screen graphics and stream cards follow the same path: mock-ups first (HTML +
PNG, a few variations, one recommended), Canva only after the user picks a direction.

## Non-negotiables

- **Photos of people are cut out only, never retouched or tone-shifted.** No brightness,
  colour, smoothing or object removal; only a meticulous cut with a soft, even edge (about a
  3 px ramp at final size).
- **Content carries the page.** A photo or scene is atmosphere *behind* the words (dimmed,
  tinted, veiled); the headline and the message sit on top and read first.
- **Restraint.** One accent colour doing one job; no glow or shine on type or badges; no
  boxed callouts with side bars; no gimmicks (fake REC/LIVE tags and the like) unless asked.
- **Generous margins.** At least 10% of the width at the sides on social sizes (108 px at
  1080), with the footer well clear of the bottom edge.
- **Facts are exact**: names, numbers, links, account details, dates and times. Never invent
  one. When a fact is missing, show a visible placeholder (`Account ______`) and say so.
- **QR codes**: error correction H, a 4-module quiet zone, test-decoded by machine before
  handover, never a `#fragment` link, a UTM tag per placement. `references/qr-codes.md`,
  `scripts/qr.py`.
- **Payment destinations never look alike.** When a design shows more than one payment
  destination or account, make them visually distinct and clearly labelled so they can't be
  confused, and never label one with another's name.

## References

| File | Read when |
|---|---|
| `references/brand-profile.md` | step 0: finding, reading or creating the brand file (template inside) |
| `references/design-standard.md` | before the first render: palette, type, logo, hierarchy, icons, footer, screens |
| `references/workflow.md` | building the generator, rendering, the review loop, the Canva stage |
| `references/export-handover.md` | sizes per platform, PNG vs JPG, print PDF, naming, zip, lossless delivery |
| `references/qr-codes.md` | any piece with a QR code |
| `references/checks-and-lessons.md` | before showing anything, and before handover |

## Scripts

Neither script holds a brand colour, URL or project path. Everything is an argument, an
environment variable, or read from the brand file.

- `scripts/render.sh in.html out.png|out.pdf [W H scale]`: screenshot (or print to PDF) with
  headless Chromium (`$CHROME`, else Playwright's Chromium, else one on `PATH`).
- `scripts/qr.py make|verify`: make level-H QR codes (SVG + PNG) and verify that every code
  decodes to the exact URL. Colours come from `--dark/--light`, else the brand file's
  `qr-dark` / `qr-light` tokens, else black on white. The first run creates its own venv
  (`segno`, `zxing-cpp`, `pillow`) in `scripts/.venv`; set `MEDIA_DESIGN_VENV` to put it elsewhere.
