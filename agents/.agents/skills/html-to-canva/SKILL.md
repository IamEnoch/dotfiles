---
name: html-to-canva
description: Replicate an HTML print design (booklet, programme, invitation card, letter, poster) in Canva as an editable design that matches the HTML to the millimetre, and keep Canva in sync as the HTML changes. Covers linting the HTML for Canva-safety, compiling it to a Canva-importable PPTX, importing and exporting through the Canva web app, auditing Canva's PDF against the HTML, calibrating, planning connector edits from HTML diffs, and freezing. Use this whenever the user wants an HTML design "in Canva", "moved to Canva", "synced/updated in Canva", wants Canva to match the HTML, asks why Canva looks different from the HTML, or is about to start or finish the Canva phase of a design, even if they don't name this skill.
---

# HTML → Canva

The HTML is the master; Canva is a build target, the way a compiler output is. Nobody edits
Canva by hand until the design is frozen. Every Canva change starts as an HTML change, is
compiled, applied, and then verified against the HTML by measurement, not by eye.

This exists because the first booklet import took ~25 test imports: Canva's PDF importer
re-flowed text (3 mm drift, lost spaces, fake justification, dropped italics), soft fades
became black boxes, SemiBold and variable fonts silently fell back, PPTX imports came in as
A1, and every later HTML change meant starting over. The scripts here encode the route that
worked (baked background + one explicit PPTX text box per block, calibrated) and add a sync
step so later changes don't need a full re-import. Read `references/canva-limits.md` before
improvising anything the scripts don't cover; it lists every trap we already hit.

## Who does what

- **Scripts (you, locally):** `scripts/cv <command>`. It creates its own virtualenv on first run (python-pptx, pymupdf, fonttools, pillow) and finds Playwright's Chromium (or `$CHROME`).
- **Canva web app (you, browser tools):** import the PPTX, export PDFs, trash test designs. Use the exact steps in `references/browser-steps.md`.
- **Canva connector (Codex child task):** reading element inventories and applying edits. In this setup only Codex has the Canva connector, so delegate with the briefs in `references/codex-briefs.md`. The connector has no export, so exports always go through the browser.

## Requirements (once per machine)

- **Python 3.10+.** `scripts/cv` creates its own virtualenv on first use, in `.venv/` next to
  `SKILL.md`, and installs `python-pptx pymupdf fonttools pillow` into it. To keep the venv
  elsewhere (for example when the skill lives in a read-only or synced folder), set
  `CV_VENV=/path/to/venv`. To rebuild it, delete the folder and run any `cv` command.
  The `.gitignore` keeps `.venv/` and `__pycache__/` out of version control.
- **Chromium**: `$CHROME`, else Playwright's (`npx playwright install chromium`, found in
  `~/.cache/ms-playwright/`), else `chromium`/`google-chrome` on `PATH`.
- **Optional**: `poppler-utils` (`pdffonts`, `pdftoppm`) for checking exports by hand.
- **The fonts** the design uses, as static TTF files. Paths in `canva.json` are relative to the
  workdir, so a project stays portable.

## Setup (once per design)

```bash
scripts/cv init path/to/design.html path/to/workdir      # writes workdir/canva.json
```

Then complete `canva.json` (all paths relative to it):

| key | what |
|---|---|
| `html` | the master HTML |
| `page` | `selector` for one printed page (`section.page`), `width_mm`, `height_mm` |
| `fonts` | per CSS family alias: `canva` = the family name Canva lists; `faces` = static font file per face key `"400"`, `"500i"`…; `single_face: true` for script fonts with one weight |
| `live_images` | CSS selectors of photos that must stay swappable in Canva; every other image/effect is baked |
| `bake_css` | extra CSS for the background render (e.g. keep a decorative glyph visible in the bake) |
| `bake_glyphs` | characters to bake rather than set live (e.g. `"◆"` when Canva's font copy lacks it) |
| `split_lines` | first words of blocks that should become one box per line |
| `canva` | `design_id`, `edit_url`, `units_per_mm` (Canva page width in units ÷ page width in mm) |

`init` flags variable fonts; give each used weight a static file (Canva drops variable fonts).
Run `cv status` any time to see what is built, synced, calibrated and frozen.

## The loop

### 1. Lint while still designing (cheap)

`cv lint` checks the rendered HTML, not the source. It runs in about 2 s, so run it after each HTML iteration in the Canva-bound phase. **Errors block the build:** unmapped fonts, missing static faces, variable fonts, weights that don't survive import (600 by default), glyphs the font lacks (Canva swaps in Noto Sans), gradient-clipped or vertical text, wrong page size. Warnings are about drift risk (semi-transparent text, transforms, uncommon glyphs). Fix in the HTML: the HTML must already look like what Canva can reproduce, so the two can match exactly.

Do not change content to satisfy lint without asking (e.g. a SemiBold → Bold swap is a design change; tell the user, as we did on the booklet).

### 2. Build and import

```bash
scripts/cv build            # add --skip-bg when only text changed (reuses the baked backgrounds)
```

This produces in `workdir/build/`: `reference.pdf` (the layout authority), `bg/pN.jpg`,
the `.pptx`, and the manifest `boxes.json` / `images.json` / `state.json`.
Import the `.pptx` through the Canva web app (`references/browser-steps.md`), name the
design, and record `design_id` / `edit_url` in `canva.json`.

The import lands as **A1** (2245.98 units wide for A4): the same layout ×2.828, which prints
correctly at A4. Keep it unless the user needs a true A4 page; resizing is a paid feature and
needs the reposition procedure in `references/codex-briefs.md`. Set `units_per_mm` to the
page width in Canva units ÷ page width in mm (A1 import of A4: 10.695; after A4 resize: 3.776).

### 3. Verify, calibrate, accept

Export the design as PDF from the browser, then:

```bash
scripts/cv audit canva-export.pdf        # exit 0 = pass; build/audit/ has the report + side-by-sides
scripts/cv calibrate canva-export.pdf    # only if boxes moved: records per-box offsets
scripts/cv build --skip-bg               # rebuild with the offsets, re-import, re-audit
scripts/cv accept                        # once the audit passes: build/ becomes the synced snapshot
```

Calibration is cumulative: each round adds the measured residual to the offset that build actually applied (seed, style or measured), and also corrects line pitch on boxes with 3 or more lines. Booklet history: the seed alone left 1–2 mm misses on big titles and long paragraphs; one calibrate round brought them to 0.00 mm. Expect 1–2 rounds and one import each.

Start with `data/calibration-seed.json` (per-font offsets measured on the booklet). New
fonts usually need one calibrate round. Look at the side-by-side images too: the audit
checks text exactly and the pixel diff catches missing art, but only eyes catch "looks wrong".
Trash failed test imports as you go, so the user's Canva doesn't fill with near-duplicates.

### 4. Sync later HTML changes (no full re-import)

```bash
scripts/cv build [--skip-bg]
scripts/cv plan              # build/sync-plan.md + .json, one route per changed page
```

Routes:
- **connector**: text replace, move, width, delete, colour/bold/italic, whole-number size, background or photo swap. Hand `sync-plan.json` to a Codex child with the "apply sync plan" brief.
- **editor**: font family, letter-spacing, fractional size, or editing a box with mixed styles. List them for the user, or do them in the Canva editor with the browser tools.
- **reimport**: new text boxes, a page that changes a lot, a page count change. Re-import just those pages ("page re-import" brief), or rebuild the design if most pages changed.

Then export, `cv audit`, and `cv accept` only on a pass. Never `accept` an unverified sync:
`synced/` must describe what is really in Canva, or the next plan will be wrong.

If the Canva design predates the manifest (imported before this skill, or hand-edited), there
is no trustworthy snapshot: re-import once, then sync from there.

### 5. Freeze

When the user approves the Canva version, `cv freeze`. From then on Canva is the master and
`plan` refuses to run. Say so plainly, so nobody keeps editing the HTML and expects it to flow
through.

## Reporting to the user

The user cares whether Canva matches and what they need to do, not about script names. Report
in plain words: what was imported or changed, the audit result (e.g. "all 413 text boxes within
0.5 mm, same fonts"), anything left for the editor, and the Canva link. Give exported PDFs as
absolute paths. Ask before deleting any Canva design that isn't a test import you made.

## Files

- `scripts/cv`: entry point (all commands: `cv --help`)
- `scripts/lint.py`, `build.py`, `audit.py`, `sync.py`, `cvlib.py`: the stages
- `scripts/extract.js`, `inspect.js`: run inside Chromium to read the rendered page
- `data/calibration-seed.json`: starting offsets per Canva font face
- `references/canva-limits.md`: what Canva and its importer/connector can and can't do (read before improvising)
- `references/browser-steps.md`: import, export and trash in the Canva web app
- `references/codex-briefs.md`: connector briefs for Codex (inventory, apply sync plan, page re-import, A4 resize)
