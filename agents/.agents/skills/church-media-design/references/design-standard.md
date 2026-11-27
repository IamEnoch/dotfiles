# Design standard

## Contents
- Brand facts
- Two palettes: event vs everyday
- Typography
- Logo
- Layout, hierarchy and margins
- Photos and scenes
- Icons, labels, footer
- Projection and livestream specifics

## Brand facts (check before every piece)

| Item | Value |
|---|---|
| Church | PEFA Magina Cathedral, Lari, Kiambu |
| Website | pefamagina.com (lowercase in artwork) |
| Handle | @pefamagina: Facebook, Instagram, YouTube. TikTok is @pefamaginacathedral, but the user chose @pefamagina on artwork; don't change it unasked |
| Event name (Nov 2026) | "Dedication & Consecration". Never "Opening" |
| Cathedral giving | pefamagina.com/build · M-Pesa Paybill 247247 · Account 4019079 · PEFA MAGINA CATHEDRAL. Building project only |
| Booklet | pefamagina.com/dedication/booklet |
| Logo files | `pefa-magina-opening-site/output/logo-assets/PEFA Magina Logo Assets/` (Full Logo: Colour / Reverse / All White, SVG + PNG; Emblem variants) |
| Data protection | Kenya's Data Protection Act 2019 (cite in filming/consent notices) |

## Two palettes: event vs everyday

Gold/yellow is the **event** colour of the Dedication & Consecration (28 Nov 2026), and
everyday pieces don't need it. The user still chose gold as the accent on the general media
notice once they had seen an all-blue version, so offer both when it's unclear.

**Social / "thumbnail" family** (the media notice, the YouTube thumbnail):

| Token | Hex | Use |
|---|---|---|
| navy | `#061a33` (bg), `#06213f` | page background, text on gold |
| cathedral blue | `#0a4a9a` tint at 70% *color* blend over photos; `#2EA8FF` azure, `#9ADBFF` ice | scene tint, secondary text (the closing line) |
| gold | `#FFCE3A` | tag fill, second headline line, separators, icon badges, website link |
| white | `#fff` | headline line 1, body |

**Site family** (pefamagina.com, booklet, giving/projection slides that sit next to the site):

| Token | Hex |
|---|---|
| navy | `#0D3A5E` (hi `#134870`, lo `#0A2F4D`, ink `#07243C`) |
| champagne | `#DCC796` (hi `#F1E3BC`), deep gold `#8E7040` (on light), `#D9C38F` (on dark) |
| logo blue | `#58BAE9` |
| paper/ice | `#F7F9FB`, `#EEF7FC` |
| M-Pesa green | `#39B54A`: only for an M-Pesa mark, never as a theme colour |

Use one family per piece. Never mix gold `#FFCE3A` with champagne `#DCC796`.

## Typography

| Role | Social family | Site family |
|---|---|---|
| Headline | **Anton**, caps, skewX(−7°), ~0.1 of width (132 px at 1080) | **Cormorant Garamond** 500–700, italic for warmth |
| Label / kicker | **Archivo Narrow Bold**, caps, letter-spacing .12–.14em | Montserrat 600→use 700 (SemiBold breaks in Canva), caps, tracking .14em |
| Body | **Montserrat Medium 500**, 23–25 px at 1080 wide, line-height 1.5–1.55; bold 700 for names/leads; Medium Italic for the closing line | Montserrat 400/500 |
| Handles/URL | Montserrat Medium, **lowercase** | same |

- Static TTF per weight (Canva drops variable fonts; html-to-canva lint enforces this).
- Avoid SemiBold 600 in anything going to Canva.
- `text-wrap: pretty` on paragraphs; reword to kill one-word last lines ("2019.").
- Site uses Montserrat, not Poppins (Poppins is the printed booklet's body face).

## Logo

- Full logo (Africa emblem + "PEFA MAGINA CATHEDRAL") top-left, reverse/white on dark,
  ~8–9% of width tall (92 px at 1080). Emblem-only for small corners and lower-thirds.
- Never recolour, stretch, outline or put it on a busy area without a veil behind it.

## Layout, hierarchy and margins

Order of reading, top to bottom: logo → label tag → headline (two lines, white then accent)
→ category line → message rows → closing line → footer.

- Side margins 108 px at 1080 wide (10%); square 84 px. Footer bottom ≥ 75 px clear.
- Headline gets the dark, empty part of the scene; never leave a large dead area *and*
  cramped text: move the text into the space instead of adding filler.
- Message as **rows**: icon badge + paragraph (Ruach style), not a box or a bar.
- Closing line: italic, ice blue, one sentence of thanks.
- 9:16 for TikTok: keep the bottom ~330 px and the right ~120 px free of key content (app UI).

## Photos and scenes

- People: cut-only (see SKILL.md). Edge: smooth signed-distance outline, ~3 px soft ramp.
- Scenes (camera, building, crowd): a large, dim, blue-tinted full-bleed background, with a
  left-to-right navy veil (.88→.15) and a bottom fade to solid navy behind the text. The
  subject sits right/top and may run off the edge; it must not "steal the show".
- Stock: Unsplash/Pexels licence only; note the photo id. The church's own exteriors are
  in `pefa-magina-opening-site/output/church-photos-2026-11-24/`.
- Grain: an SVG fractal-noise overlay at ~10% opacity (soft-light/overlay) unifies the photo and flat colour.

## Icons, labels, footer

- **Icons**: solid filled glyphs (Material-style) in navy inside a **solid gold circle**
  (64 px at 1080), with only a soft dark drop shadow and no glow. Not thin outline icons.
- **Label tag**: gold fill, navy Archivo Narrow Bold caps, radius 6, *no glow*.
- **Footer**: a socials pill (thin 1.5 px white 28% outline, fully rounded, dark fill) with
  FB · IG · YouTube · TikTok glyphs + `@pefamagina` lowercase on the left; `pefamagina.com`
  lowercase in the accent colour on the right. No rule line above it.

## Projection and livestream specifics

- 16:9 1920×1080. Projection is read from 10–30 m: body ≥ 44 px, numbers (Paybill/Account) ≥
  90 px, max ~25 words per slide, contrast ≥ 7:1.
- Livestream: full-screen card 1920×1080, plus a **transparent PNG** lower-third or corner
  overlay (keep it inside the 5% title-safe area, ≤ 1/4 of the frame height). Viewers may
  watch on a TV and scan with a phone, so the QR code should be ≥ 300 px on the full card.
- Each fund or item has its own colour cue and label; on a combined slide use separated
  panels with distinct headers.
