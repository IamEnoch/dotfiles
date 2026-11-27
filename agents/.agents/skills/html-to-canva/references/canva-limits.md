# What Canva does to an imported design (measured, Nov 2026)

Everything here was observed on real imports of the PEFA booklet (A4, 12 pages, about 450 text
boxes) and the invitation cards. When something new turns up, add it here with the evidence.

## Import route: PPTX, not PDF

**PDF import (abandoned after five variants):**
- Canva merges each left-aligned column of text into one text box and re-flows it.
- Lines of different sizes drift by up to 3 mm, spaces get lost ("InsupportofPEFA"), some lines come out falsely justified, and italics are dropped.
- Splitting blocks with a tiny rotation (≤0.035°) to stop the merging helped, but never fully worked.

**PPTX import works.** It needs one explicit text box per block (or per line, for blocks that mix sizes), set as follows:
- word-wrap off and autosize off;
- an exact line pitch;
- exact letter-spacing (`spc`);
- the exact Canva font face name on every run.

Canva keeps those boxes in place. After calibration, all 456 boxes landed within 0.00 mm of where they belong.

## Page size

- **A PPTX import becomes "A1 (Portrait)".** That's 2245.98 × 3176.46 units for an A4 slide: the same layout scaled by 2.828, and it prints correctly at A4.
- **Resize to A4:**
  - Magic Resize is a paid feature. The free trial's resize credits are used up on this account.
  - The connector's resize is not uniform: elements move by up to 13 mm.
  - After resizing, every element must be repositioned at the exact scale: text gets its width only, images get width and height.
  - In one case the resize also shrank the text to 75%, so some boxes needed sizes reset in the editor.
- **Page units:** the connector accepts whole pixels only, so 793.70 × 1122.52 came back as 793 × 1122.

- **Pages near the A-series ratio snap to A-series on PPTX import.** A 7 x 5 in slide (ratio 1.40) came in as A5 landscape (794 x 559) and was cropped (Nov 2026). Resize needs paid credits, and `merge_designs` keeps each page's size, so neither fixes it.
- **For a true 7 x 5 in page, use a PDF import** (it keeps the page size) with a baked background and live text. Canva merges lines that sit close together, even with tiny rotations or reordering, and sets them to one even pitch. What worked: import those lines spread far apart, then move each to its true place with the connector using relative `position_element` offsets. Final audit: 0 issues on all 3 pages.

## Fonts

- **Canva lists each weight as its own family** ("Montserrat Medium", "Cormorant Garamond Light"):
  - Regular is the plain name.
  - Bold is the plain name plus the bold flag.
  - A PPTX run must name the face exactly that way, or Canva substitutes a font.
- **SemiBold (600) did not survive import** for Montserrat or Cormorant Garamond; it fell back. The booklet moved every SemiBold to Bold in the HTML too, so the two still match. Lint blocks weight 600 by default.
- **Variable fonts are dropped** (they arrive as Type 3 or get substituted). Use a static instance per weight; Cinzel needed a static Bold made for it.
- **Fonts with non-standard internal names lose their italics.** The booklet's Cormorant italics had odd name tables, so Canva dropped the italic. Use files whose OS/2 and head tables flag them as italic.
- **Missing glyphs mean substitution.** When a character isn't in Canva's copy of a font, Canva sets it in Noto Sans. U+25C6 ◆ in Montserrat was the case we hit: bake decorative glyphs into the background.
- **Missing glyphs show up as an unnamed Type3 font** in Canva's PDF export; the audit reports it as `type3-unnamed (page N)`. The fix: `bake_glyphs` plus a `bake_css` rule that makes the glyph visible in the background bake, e.g. `.depts span::before { -webkit-text-fill-color: currentcolor !important; }` for a `::before` bullet.
- **Kerning pairs are ignored** (Canva sets "Yo" wider than Chromium does). That's harmless: under 0.5 mm on a short word, and the audit judges widths in mm, not just by ratio.
- **Fractional point sizes** import fine via PPTX. The connector's `format_text.font_size` accepts integers only, and its unit isn't documented. The editor accepts decimals.

## Line pitch

Canva's line spacing for an exact-spacing PPTX paragraph comes out slightly shorter than the value written: about 0.09 mm per line for Montserrat 8.7 pt with a 4.58 mm pitch (2 %). In a 19-line paragraph the last line ends up 1.6 mm high. A box offset can't fix it. `cv calibrate` fits the drift per box (dy against line index) and stores a third `calib.json` value: pitch error in mm per line. The builder then writes the line spacing as `LH − error`. Booklet result: page 3 went from 30 flagged lines to 0 in one round.

## Effects

- **Soft masks become solid black boxes on import:** gradient fades, `text-shadow`, filter shadows, `mask-image`. Bake every effect into the page background image. Photo drop-shadows are baked on their own, through a shadow-only SVG filter, so the photo stays live and swappable.
- **Semi-transparent text colour:** the PPTX path writes solid RGB, so alpha is lost. Mix the colour against its background in the HTML instead.
- **Cut-out PNGs with real alpha** (people photos) import correctly as live images.

## Connector (Codex: `mcp__codex_apps__canva_*`)

- **Editing works in transactions:** `start_editing_transaction` → `perform_editing_operations` → `commit_editing_transaction`, or `cancel_editing_transaction`. A read is a transaction that you cancel.
- **The 10 operations:**

  | Operation | Notes |
  |---|---|
  | `update_title` | |
  | `replace_text` | whole element; replaces per-run styling |
  | `find_and_replace_text` | |
  | `format_text` | colour, integer `font_size`, normal/italic, normal/bold, `line_height`, start/center/end align; whole element only |
  | `position_element` | |
  | `resize_element` | text: width only; height is refused ("vertical resize not supported") |
  | `delete_element` | |
  | `insert_fill` | image from an uploaded `asset_id` |
  | `update_fill` | |
  | `update_autofill_field` | |

- **What the connector can't do:**
  - insert new text;
  - set the font family or letter-spacing;
  - format a range of characters;
  - split an element;
  - change z-order;
  - export a design;
  - return any font information when listing elements.
- **Uploads:** `create_upload_url`, then one raw POST of the file bytes (`Content-Type: application/octet-stream`). The URL is single-use; get a fresh one each time.
- **Other tools:** `copy_design` (whole design or selected pages, into a new design), `create_folder`, `fetch` (text content only), `get_assets`.
- **Element ids and positions** come back from the transaction listing. Text from the PDF importer came back fragmented (whitespace-only elements, times split from their labels). PPTX imports keep one element per box.

## Account and housekeeping

- The account is on the free plan, so Pro-only fonts and Resize aren't available.
- Every test import creates a design. Move test designs to Trash as you go (File → Move to Trash), and never trash a design whose title shows it's the keeper.
- Canva's "PDF Print" download gives higher-resolution images and offers bleed and crop marks. For audits, the standard "PDF" export is enough.
