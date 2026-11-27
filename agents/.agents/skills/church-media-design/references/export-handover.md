# Export set and handover

## Sizes per platform (checked Nov 2026)

The platforms' help pages could not be fetched. These figures come from 2025–26 guides
(Buffer, Sprout, Kapwing, Linearity, Chatarmin), which agree.

| # | Platform | Size | Ratio | Notes |
|---|---|---|---|---|
| 1 | WhatsApp Status | 1080×1920 | 9:16 | other ratios get black bars |
| 2 | WhatsApp Community / groups / chats | 1080×1350 | 4:5 | no official spec; 9:16 gets cut short in the chat preview, 4:5 shows whole |
| 3 | Instagram feed | 1080×1350 | 4:5 | profile grid crops to 3:4 centre, so keep ≥ 108 px side margins (1080×1440 is the newer native 3:4 if asked) |
| 4 | Facebook feed | 1080×1350 | 4:5 | |
| 5 | YouTube Community | 1080×1080 | 1:1 | portrait unverified |
| 6 | TikTok photo | 1080×1920 | 9:16 | keep bottom ~330 px and right ~120 px clear (UI) |
| — | YouTube thumbnail | 1280×720 | 16:9 | ≤ 2 MB |
| — | Projection / stream card | 1920×1080 | 16:9 | |
| — | Print | A4 210×297 mm | 1:1.414 | its own layout, not a stretched 4:5 |

Three layouts cover all six social pages: 9:16, 4:5, 1:1.

## PNG vs JPG

- **PNG** for text-led graphics (notices, slides): crisp type and hairlines; platforms
  recompress anyway, so start lossless. 1–1.6 MB each at 1080 wide.
- **JPG** (q95, 4:4:4) only for photo-led pieces or a hard size cap (YouTube thumbnail ≤ 2 MB).
- Render at 2×, downsample to the exact size.
- Canva's free plan exports PNG only at 1×, and JPG quality is a Pro setting. Make JPGs
  locally from the PNG.

## Print PDF

- A4 layout preset (W 1080, H 1527) printed by headless Chromium: `@page{size:A4;margin:0}`,
  `html,body{width:210mm;height:297mm}`, `.page{transform:scale(.734907);transform-origin:0 0}`
  (don't use `zoom`, it misplaces things). `--print-to-pdf --no-pdf-header-footer`.
- Keep text live (vector): check `pdffonts` lists Anton, Archivo Narrow, Montserrat ×3.
  Rasterise at 300 dpi and zoom into the headline and small text to check them.
- Note for the user: full-bleed navy, so print at "Actual size", and expect a thin white edge on
  office printers without borderless printing. ~15 MB is normal (photo + blends).

## File naming

Numbered, CAPS, platform first, size in brackets, so the media team knows where each goes:

```
1 WHATSAPP STATUS (1080x1920).png
2 WHATSAPP COMMUNITY (1080x1350).png
3 INSTAGRAM (1080x1350).png
4 FACEBOOK (1080x1350).png
5 YOUTUBE COMMUNITY (1080x1080).png
6 TIKTOK (1080x1920).png
7 PRINT A4 (PDF).pdf
```

Zip as `PEFA-MAGINA-<PIECE>.zip` next to the source folder (`zip -9`). Canva page titles use
the same words: `WhatsApp Status · 1080×1920`.

## Sending over WhatsApp without quality loss

Attach → **Document** (not Gallery/Photos, not the HD photo toggle): files arrive
byte-identical with their names. Send the files individually rather than the zip (phones open
zips poorly). Forward as documents too. Upload to each platform straight from the downloaded file.
