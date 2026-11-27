# Workflow details

## Contents
- Folder layout
- The generator pattern
- Rendering
- Review loop
- Canva stage

## Folder layout

One folder per piece, wherever the project keeps design output (ask if it isn't obvious; in
a code repository, check whether that folder is git-ignored before assuming it's tracked):

```
<output>/<piece>/
  gen.py               # generator: presets → <piece>-<size>.html (+ --canva variants)
  rows.part.html ...   # optional shared fragments
  hero.jpg, logo.svg, headline-4x.png
  <piece>-vN.html      # snapshots of approved or abandoned steps
  canva-<size>/        # html-to-canva workdirs (canva.json, build/, synced/)
  export/              # final files, numbered names
  <PIECE>.zip
```

## The generator pattern

Write the design once as a template (a Python f-string works well). Each size is a preset:

```python
P = {
 '4x5': dict(W=1080, H=1350, M=108, logo=(88, 92), tag=(272, 30), hl=(132, 336),
             sub=(670, 30), row=(23, 64, 730, 924), close=(1098, 21), foot=(1226, 22)),
 '9x16': ..., '1x1': ..., 'a4': dict(W=1080, H=1527, ...),   # A4 ratio 1:1.414
}
```

- All coordinates are absolute px; derived values scale from the headline size (`k = hs/132`).
- Colours, fonts, the logo path, handles and links are read from the brand file or defined
  once at the top of the generator. Never scatter them through the template.
- A `--canva` flag wraps each page in `<section class="page">` and replaces transformed text
  (a skewed headline, for example) with a 4× transparent PNG, rendered with
  `TRANSPARENT=1 scripts/render.sh headline.html headline-4x.png W H 4`.
- Add `@page{size:{W}px {H}px;margin:0}` and `print-color-adjust:exact` so the same file prints.

## Rendering

`scripts/render.sh in.html out.png W H 2`, then downsample to 1× with Lanczos (sharper type
than a 1× render). JPG when needed: Pillow `quality=95, subsampling=0`.

Look at each render: the full view, then crops of icons, edges and small text at 3×. Diff a
Canva variant against the live-text version (`ImageChops.difference`) to catch drift.

## Review loop

- Users tend to react in short messages, often with a screenshot of the problem area. Read
  the screenshot closely; it points at the exact element. Each message is one change. Apply
  it and re-render, saving the previous state as `<piece>-vN.html`.
- When they call a direction "solid", keep the structure and change only what they name.
- Write decisions down at once (what was rejected and why). Lasting ones go into the brand file.
- On a long run of tool calls, send a one-line status every few steps.

## Canva stage

Use the **`html-to-canva`** skill; it owns the commands, the browser steps and the list of
Canva's limits. Use it when the user wants an editable Canva copy, and only after the HTML
direction is approved. What this skill adds for multi-size pieces:

1. One workdir per size: `cv init <canva-html> canva-<size>`. Set `page.width_mm/height_mm`
   = px × 25.4 / 96, and map every font to the name Canva lists.
2. `cv lint` → 0 errors, then `cv build`. Import each file; custom px pages keep their size.
3. Export a PDF → `cv audit`. A first import usually sits a little low or high on paragraph
   text → `cv calibrate` → `cv build --skip-bg` → trash the test import → re-import → the
   audit passes → `cv accept`.
4. **One project, titled pages.** Merge the per-size designs into one new multi-page design
   in platform order, and title each page (`<Placement> · <W>×<H>`). Leave the audited
   sources untouched until the user agrees to trash them. The merge and page-title steps
   are in `html-to-canva`'s `references/browser-steps.md`.
5. Check fonts with evidence: `pdffonts` on Canva's PDF, plus a read of weights and styles.
6. Tell the user what you trashed, and never trash a design you didn't create as a test.
