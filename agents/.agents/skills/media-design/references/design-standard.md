# Design standard

General rules. Where a rule needs a value that belongs to one organisation (a hex code, a
font, a logo file, a handle), the value comes from the project's brand file
(`brand-profile.md`). If the brand file says otherwise, the brand file wins.

## Contents
- Palette
- Typography
- Logo
- Layout, hierarchy and margins
- Photos and scenes
- Icons, labels, footer
- Screens: projection, venue displays, streams
- Payment and call-to-action panels

## Palette

- **One palette family per piece.** If the brand has two (say, a website family and a
  bolder social-graphics family), pick one and don't mix their accents.
- **Dark base, light text, one accent** is the default for social and screen pieces: it
  holds a photo behind the words and survives recompression. Print pieces may flip to a
  light base to save ink.
- **The accent does one job** per piece: the label fill, the second headline line, the key
  number, the link. If it is everywhere, it marks nothing.
- **Event colour vs everyday colour.** A colour introduced for one event or campaign isn't
  automatically right for everyday pieces. When it's unclear, show both and let the user choose.
- **Third-party marks** (a payment provider, a social network) keep their own colours and
  are used only as marks, never as a theme colour.
- **Contrast**: body text at least 4.5:1; anything read from across a room at least 7:1.

## Typography

| Role | Guideline at 1080 px wide |
|---|---|
| Headline | a display or condensed face, often caps; about 0.1 of the width tall (≈130 px); two lines at most |
| Label / kicker | bold caps with letter-spacing .12–.14em |
| Body | a clean sans at medium weight, 23–25 px, line height 1.5–1.55; bold for names and lead-ins; italic for a closing line |
| Handles and URLs | medium weight, **lowercase** |

- Use a **static font file per weight**. Variable fonts are dropped by Canva, and the
  `html-to-canva` lint enforces this.
- Avoid SemiBold (600) in anything going to Canva; use 500 or 700.
- `text-wrap: pretty` on paragraphs, and reword to remove one-word last lines.
- When the user says the type "feels off", check with evidence (`pdffonts`, a font read from
  Canva) before changing anything, then report what you checked.

## Logo

- Full logo top-left by default, the reverse or white version on dark, about 8–9% of the
  width tall (≈92 px at 1080). Emblem only for small corners and lower-thirds.
- Never recolour, stretch or outline it, and never put it on a busy area without a veil behind it.
- Use the vector file when there is one.

## Layout, hierarchy and margins

Reading order, top to bottom: logo → label tag → headline (two lines, the second in the
accent) → category line → message rows → closing line → footer.

- Side margins 10% of the width (108 px at 1080; a square can go to about 84 px). Keep the
  footer at least 75 px clear of the bottom.
- The headline takes the dark, empty part of the scene. Never leave a large dead area while
  text is cramped elsewhere: move the text into the space instead of adding decoration.
- Set the message as **rows**: an icon badge plus a short paragraph, not a box or a side bar.
- Closing line: one sentence, italic, in a quiet secondary colour.
- 9:16 for short-video apps: keep the bottom ~330 px and the right ~120 px free of key
  content, because the app's interface covers them.

## Photos and scenes

- **People**: cut out only, never retouched or tone-shifted. Edge: a smooth outline with
  about a 3 px soft ramp at final size, even all the way round.
- **Subject**: choose a picture that says what the piece is about (a camera for a filming
  notice, a plate for a menu), not a generic picture of the building.
- **Scenes** (an object, a building, a crowd): a large, dim, tinted full-bleed background
  with a side-to-side veil in the base colour (about .88 → .15) and a bottom fade to the
  solid base behind the text. The subject sits to one side and may run off the edge. It
  must not compete with the words.
- **Stock**: only sources whose licence allows the use; note the photo id and the source.
- **Grain**: an SVG fractal-noise overlay at about 10% opacity (soft-light or overlay)
  unifies the photo and the flat colour.

## Icons, labels, footer

- **Icons**: solid filled glyphs in the base colour inside a solid accent circle (64 px at
  1080), with a soft dark drop shadow and no glow. Thin outline icons read as weak.
- **Label tag**: accent fill, base-colour bold caps, a small radius, no glow.
- **Footer**: a socials pill (a thin outline at about 28% white, fully rounded, dark fill)
  with the platform glyphs and the handle in lowercase on one side; the website in lowercase
  in the accent colour on the other. No rule line above it.

## Screens: projection, venue displays, streams

- 16:9, 1920×1080. A screen read from 10–30 m needs body text of at least 44 px, key
  numbers (an account number, a time, a room) of at least 90 px, about 25 words per slide
  at most, and contrast of at least 7:1.
- Stream or webinar: a full-screen card at 1920×1080, plus a **transparent PNG**
  lower-third or corner overlay kept inside the 5% title-safe area and no taller than a
  quarter of the frame. Viewers may watch on a TV and scan with a phone, so a QR code on
  the full card should be at least 300 px.
- Conference and title slides follow the same sizes: one idea per slide, the speaker's
  name and title exact.

## Payment and call-to-action panels

- Each destination (fund, account, purpose) gets its own colour cue and its own label. On
  a combined slide use separated panels with distinct headers.
- Label a destination only with its own name; never fold a specific fund into a general one.
- Show the number, the account name and the printed link together, with the QR code beside
  them, so one panel is enough to act on.
