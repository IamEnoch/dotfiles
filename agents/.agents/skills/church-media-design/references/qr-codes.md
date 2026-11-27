# QR codes

## Rules

- **Error correction H** (30%). Survives projector blur, stream compression, moiré from
  phone-at-TV, and a small logo in the centre (≤ 15% of the area, only with H).
- **Quiet zone 4 modules** of pure light colour around the code. Dark navy around the quiet
  zone is fine; inside it is not.
- **Colours**: dark modules on light (navy `#061a33`/`#0D3A5E` on white or champagne-hi).
  Never invert (light on dark), never use gold modules on navy, never gradients.
- **Short URLs** (fewer modules = bigger modules): `https://pefamagina.com/build?utm_source=projection`.
  Never a `#fragment` link: fragments are dropped by some scanners and printers' QR tools,
  and the site's printed links are path-based by decision (`/build`, `/dedication`).
- **UTM per channel**: `utm_source=projection` | `livestream` | `print` | `whatsapp`, so each
  screen's scans can be counted. One code per channel; never reuse a projection code on the stream.
- **Printed link under every code** in plain text without `https://` (pefamagina.com/build).
- **Size**:
  - Projection (screen read from up to ~20 m): the code ≥ 25% of slide height (≥ 270 px of 1080); best 360–420 px.
  - Livestream full card: ≥ 300 px at 1080p. A lower-third/corner code should be ≥ 220 px
    (≈ 20% of the height) or it won't scan off a TV.
  - Print A4: ≥ 30 mm.
- **Render crisp**: SVG, or PNG at integer pixels per module (no resampling, `image-rendering:
  pixelated` if scaled in HTML).

## Make and verify

```bash
scripts/qr.py make out/build-projection "https://pefamagina.com/build?utm_source=projection"
#   -> out/build-projection.svg, .png (10 px/module, border 4, level H) and the decode check
scripts/qr.py verify render.png "https://pefamagina.com/build?utm_source=projection" ...
#   decodes every QR in a rendered slide; fails unless each expected URL is found exactly
```

Run `verify` on the **final rendered slide** (not just the code image), and again on a
degraded copy (`--degrade`: downscale to 640 px wide, blur, JPEG q40), which stands in for a
phone reading a TV. Report the decoded strings in the handover.
