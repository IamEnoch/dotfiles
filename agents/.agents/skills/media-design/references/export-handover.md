# Export set and handover

The brand file's "Platforms and sizes" section says which placements a project uses. This
page gives the default sizes and the mechanics.

## Default sizes per placement

Platform specs change. These figures were last checked in late 2026 against several
independent social-media size guides that agreed with each other, not against the
platforms' own help pages. Re-check a size when a platform changes its feed, and record the
date in the brand file.

| Placement | Size | Ratio | Notes |
|---|---|---|---|
| WhatsApp Status, Instagram/Facebook Story | 1080×1920 | 9:16 | other ratios get bars |
| WhatsApp groups and chats | 1080×1350 | 4:5 | no official spec; 9:16 is cut short in the chat preview, 4:5 shows whole |
| Instagram feed | 1080×1350 | 4:5 | the profile grid crops to 3:4 centre, so keep ≥ 108 px side margins (1080×1440 is the newer native 3:4 if asked) |
| Facebook feed, LinkedIn feed | 1080×1350 | 4:5 | |
| YouTube Community, square posts | 1080×1080 | 1:1 | |
| TikTok photo | 1080×1920 | 9:16 | keep the bottom ~330 px and the right ~120 px clear (interface) |
| YouTube thumbnail | 1280×720 | 16:9 | ≤ 2 MB |
| Slide, projection, venue screen, stream card | 1920×1080 | 16:9 | |
| Print | A4 210×297 mm (or the local standard) | 1:1.414 | its own layout, not a stretched 4:5 |

Three layouts (9:16, 4:5, 1:1) cover the usual social placements.

## PNG vs JPG

- **PNG** for text-led graphics (notices, slides, menus): crisp type and hairlines.
  Platforms recompress anyway, so start lossless. Expect 1–1.6 MB each at 1080 wide.
- **JPG** (quality 95, 4:4:4) only for photo-led pieces or a hard size cap.
- Render at 2× and downsample to the exact size.
- Canva's free plan exports PNG at 1× only, and JPG quality is a paid setting. Make JPGs
  locally from the PNG.

## Print PDF

- An A4 preset (W 1080, H 1527) printed by headless Chromium: `@page{size:A4;margin:0}`,
  `html,body{width:210mm;height:297mm}`, `.page{transform:scale(.734907);transform-origin:0 0}`.
  Don't use `zoom`; it misplaces things. `scripts/render.sh in.html out.pdf` does the printing.
- Keep text live (vector): `pdffonts out.pdf` must list every font of the design. Rasterise
  at 300 dpi and zoom into the headline and the small text.
- Tell the user: a full-bleed dark page should be printed at "Actual size", and an office
  printer without borderless printing leaves a thin white edge. A file of 10–15 MB is
  normal with a photo and blends.

## File naming

Numbered, placement first, size in brackets, so whoever posts them knows where each goes.
Use the pattern in the brand file if it gives one; otherwise:

```
1 WHATSAPP STATUS (1080x1920).png
2 WHATSAPP GROUPS (1080x1350).png
3 INSTAGRAM (1080x1350).png
4 FACEBOOK (1080x1350).png
5 YOUTUBE COMMUNITY (1080x1080).png
6 TIKTOK (1080x1920).png
7 PRINT A4 (PDF).pdf
```

Zip as `<SHORT-NAME>-<PIECE>.zip` next to the source folder (`zip -9`), and list it
(`unzip -l`). Canva page titles use the same words: `WhatsApp Status · 1080×1920`.

## Handover

State, in plain words: what is in the set and where (absolute paths), the decoded QR
strings, the Canva link if there is one, what was trashed, and every open question
(placeholders, wording you couldn't verify).

## Sending over a messaging app without quality loss

Attach as a **Document** or file, not as a photo (a photo attachment is recompressed, even
with an "HD" toggle). Files then arrive byte-identical with their names. Send the files one
by one, not the zip, because phones open zips poorly. Forward as documents too, and upload
to each platform straight from the downloaded file.
