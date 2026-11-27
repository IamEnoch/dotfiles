# Workflow details

## Contents
- Folder layout
- The generator pattern
- Rendering
- Review loop
- Canva stage

## Folder layout

One folder per piece in the site repo's `output/` (assets are git-ignored there):

```
output/<area>/<piece>/
  gen.py               # generator: presets → notice-<size>.html (+ --canva variants)
  rows.part.html ...   # optional shared fragments
  camera.jpg, logo-white.svg, headline-4x.png
  notice-vN.html       # snapshots of approved/abandoned steps
  canva-<size>/        # html-to-canva workdirs (canva.json, build/, synced/)
  export/              # final files, CAPS names
  <PIECE>.zip
```

## The generator pattern

Write the design once as a Python f-string template. Each size is a preset dict:

```python
P = {
 '4x5': dict(W=1080,H=1350,M=108, ph=(-120,0,1420), fade=(40,58,70), logo=(88,92),
             tag=(272,30), hl=(132,336), sub=(670,30), row=(23,64,730,924),
             close=(1098,21), foot=(1226,22)),
 '9x16': ..., '1x1': ..., 'a4': dict(W=1080,H=1527,...),   # A4 ratio 1:1.414
}
```

- All coordinates absolute px; derived values scale from the headline size (`k = hs/132`).
- `--canva` flag: wrap in `<section class="page">`, replace transformed text (skewed
  headline) with a 4× transparent PNG (`headline-4x.png`, rendered with
  `--default-background-color=00000000 --force-device-scale-factor=4`).
- Add `@page{size:{W}px {H}px;margin:0}` + `print-color-adjust:exact` so the same file prints.
- A working example from the media notice is in the site repo:
  `output/social-poster/media-notice/gen.py`.

## Rendering

`scripts/render.sh in.html out.png W H 2` then downsample to 1× with Lanczos (sharper type than
a 1× render). JPG when needed: Pillow `quality=95, subsampling=0`.

Look at each render: full view, then crops of icons, edges, small text at 3×. Diff Canva
variants against the live-text version (`ImageChops.difference`) to catch drift.

## Review loop

- The user reacts in short messages with screenshots of the problem area; each message is one
  change. Apply it and re-render, saving the previous state as `notice-vN.html`.
- When they say a direction is "solid", keep the structure and change only what they name.
- Write decisions to memory immediately (what was rejected and why).

## Canva

Use the **html-to-canva** skill. Rules learned on the media notice:

1. `cv init <canva-html> canva-<size>` per size; set `page.width_mm/height_mm` = px × 25.4/96;
   fonts: Anton (if live), Archivo Narrow 700 (`single_face:false`), Montserrat 500/500i/700.
2. `cv lint` → 0 errors, then `cv build`.
3. Import each PPTX via the browser steps (Create a design → Upload). Custom px slides keep
   their exact size (1080×1350 etc.).
4. Export PDF → `cv audit`. Expected false alarm: `archivonarrow → archivonarrowbold` (same
   file). First import is typically 0.5–1.4 mm low on Montserrat paragraphs → `cv calibrate`
   → `cv build --skip-bg` → trash the test import → re-import → audit passes → `cv accept`.
5. One project: a Codex child (Canva connector) merges the per-size designs with
   `canva_merge_designs` into a new design, pages in platform order. Don't modify the sources.
6. Page titles: connector can't. In the editor, the thumbnail strip has `input[aria-label="Page
   title"]` (8 px wide until focused). Click its x+4 twice (first click selects the page), set
   value with the native `HTMLInputElement` value setter + `input` event, then press Enter via
   the browser tool. Reload and read all titles back.
7. Hidden preview tabs pause timers: start exports with `awaitPromise:false`, then wake the
   tab with `preview_resize` (±1 px) and poll for the `export-download.canva.com` link.
8. Font verification: `pdffonts` on Canva's PDF (family names), plus a Codex connector read
   (weights/styles; family comes back as ids only).

Run independent Codex children in parallel (e.g. merge + font check) when the user asks for
subagents.
