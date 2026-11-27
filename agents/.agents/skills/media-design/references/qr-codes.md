# QR codes

## Rules

- **Error correction H** (30%). It survives projector blur, stream compression, moiré from
  a phone pointed at a TV, and a small logo in the centre (≤ 15% of the area, and only with H).
- **Quiet zone of 4 modules** in the pure light colour around the code. A dark page around
  the quiet zone is fine; dark inside it is not.
- **Colours**: dark modules on a light background (the brand file's `qr-dark` on `qr-light`,
  or black on white). Never inverted (light on dark), never a pale accent for the modules,
  never a gradient.
- **Short URLs** (fewer modules means bigger modules): `https://example.org/give?utm_source=projection`.
- **Never a `#fragment` link**, in a code or in print. Some scanners and printers' QR tools
  drop the fragment, and a printed `#` is hard to type. Use a path (`/give`, `/event`).
- **A UTM tag per placement**: `utm_source=projection` | `livestream` | `print` | `social`
  | `whatsapp`, so each placement's scans can be counted. One code per placement; never
  reuse the projection code on the stream. Use the values listed in the brand file.
- **The link in plain text under every code**, without `https://` (`example.org/give`), for
  people who can't scan.
- **Size**:
  - Projection or venue screen (read from up to ~20 m): the code at least 25% of the slide
    height (≥ 270 px of 1080); 360–420 px is best.
  - Stream or webinar full card: at least 300 px at 1080p. A lower-third or corner code
    needs at least 220 px (about 20% of the height) or it won't scan off a TV.
  - Print: at least 30 mm.
- **Render crisp**: SVG, or PNG at a whole number of pixels per module (no resampling;
  `image-rendering: pixelated` if it is scaled in HTML).

## Make and verify

```bash
scripts/qr.py make out/give-projection "https://example.org/give?utm_source=projection"
#   -> out/give-projection.svg and .png (10 px per module, border 4, level H), then decodes the PNG
scripts/qr.py verify render.png "https://example.org/give?utm_source=projection" [more URLs] --degrade
#   decodes every QR code in a rendered piece; fails unless each expected URL is found exactly
```

Options for `make`: `--px N` (pixels per module), `--dark RRGGBB`, `--light RRGGBB`,
`--brand path/to/BRAND.md`. Without colour options, the script looks for `BRAND.md` or
`brand/BRAND.md` from the current folder upwards and uses its `qr-dark` / `qr-light`
tokens; with no brand file it uses black on white. It refuses a URL containing `#`.

Run `verify` on the **final rendered piece**, not just the code image, and again with
`--degrade` (a copy scaled to 640 px wide, blurred and saved as JPEG quality 40), which
stands in for a phone reading a TV. Test-decode every code, and report the decoded strings
in the handover.
