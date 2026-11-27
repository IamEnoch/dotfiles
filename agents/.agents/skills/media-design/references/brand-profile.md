# Brand profile

The skill holds the method; the **brand file** holds everything that belongs to one
organisation or project. One Markdown file per project, read before any design work.

## Contents
- Finding it
- When there is none
- Keeping it current
- What the scripts read
- Template

## Finding it

Look in this order and use the first hit:

1. `BRAND.md` in the project root (the working directory, or the repository root);
2. `brand/BRAND.md`;
3. the same two names in each parent folder, up to the repository root.

Read the whole file. If the piece needs something the file doesn't cover (a new platform, a
second account, a new event name), ask, then add the answer to the file.

## When there is none

Don't start designing on guesses. Ask the user for the key items in one message, with what
you could already verify filled in (a website's CSS often gives the colours and fonts; say
where each value came from):

1. the name and short name, exactly as written;
2. the main colours (hex) and which one is the accent;
3. the fonts for headlines and body text;
4. where the logo files are, and any usage rules;
5. the website, social handles, and the links to print;
6. payment or donation details, if any piece will show them;
7. which platforms and sizes the pieces go to;
8. anything that must never be done.

Then create `BRAND.md` in the project root from the template below. Leave a section in place
with `To confirm` for anything still unknown, and never fill a gap with an invented value.
Tell the user where the file is. It is a project file: commit it only when the user asks.

## Keeping it current

- A decision made in a review round that will hold for later pieces ("lowercase handles",
  "the accent is for events only") goes into the brand file the same day.
- Date the entries that can expire (event names, campaign links, account numbers).
- When the user corrects a brand fact, fix the file first, then the artwork.

## What the scripts read

Only two optional colour tokens, from the Colours table: `qr-dark` and `qr-light`, six-digit
hex. `scripts/qr.py` uses them when `--dark/--light` aren't given. Everything else in the file
is for you to read.

## Template

Copy from the next line to the end of this document. Replace every `<…>`; delete the example
rows; keep all ten headings.

```markdown
# Brand profile: <Organisation>

Last reviewed: <YYYY-MM-DD>. Source of truth for all designed pieces of this project.

## 1. Name

| Item | Value |
|---|---|
| Full name | <Organisation Full Name> |
| Short name | <Short Name> |
| Written as | <exact capitalisation, punctuation, what never to abbreviate> |
| Location / tagline | <optional line that may sit under the name> |
| Current event or campaign names | <"Exact Name" (dates); names that are no longer used> |

## 2. Colours

One table per palette family if there is more than one (for example a website family and a
social-graphics family), with the rule for when each is used.

| Token | Hex | Use |
|---|---|---|
| primary | `#000000` | <page background, text on accent> |
| primary-hi | `#000000` | <lighter step> |
| accent | `#000000` | <the one job it does: label fill, link, key number> |
| text-on-dark | `#FFFFFF` | <body on dark> |
| paper | `#FFFFFF` | <light background> |
| qr-dark | `#000000` | QR modules (read by `qr.py`) |
| qr-light | `#FFFFFF` | QR background and quiet zone (read by `qr.py`) |

Rules: <which colours never meet; event colour vs everyday colour; third-party marks keep
their own colours and are never used as a theme colour>.

## 3. Fonts

| Role | Font, weight | Where to get it | Notes |
|---|---|---|---|
| Headline | <Family 700> | <URL or path to the static font file; licence> | <caps? italic?> |
| Label / kicker | <Family 700> | <…> | <letter-spacing> |
| Body | <Family 400/500> | <…> | <size at 1080 wide, line height> |
| Handles and URLs | <Family 500> | <…> | <lowercase?> |

Rules: <weights to avoid; fallbacks; which faces are for print only>.

## 4. Logo

| File | Path | Use on |
|---|---|---|
| Full logo, colour | `<path>` | light backgrounds |
| Full logo, reverse | `<path>` | dark backgrounds |
| Emblem only | `<path>` | small corners, lower-thirds, avatars |

Rules: <position and size (for example top-left, 8–9% of the width tall); clear space;
never recolour, stretch or outline; what sits behind it on a busy area>.

## 5. Photos

- Where the organisation's own photos are: `<path>`.
- People: <cut out only, never retouched or tone-shifted; consent rules>.
- Scenes and stock: <allowed sources and licences; subjects to prefer or avoid; tint and veil>.
- Law or policy to cite on filming or consent notices: <name of the applicable law>.

## 6. Tone and wording

- Voice: <plain, warm, formal…>; language(s): <…>.
- Fixed wordings: <the exact event name; titles and honorifics; phrases never used>.
- Capitalisation: <headlines in caps? handles and URLs in lowercase?>.
- People's names and titles: <where the checked list is>.

## 7. Links, QR codes and UTM

| Purpose | Printed as | QR target |
|---|---|---|
| Website | `example.org` | `https://example.org/?utm_source=<placement>` |
| <Donate / pay / register> | `example.org/give` | `https://example.org/give?utm_source=<placement>` |
| <Event page> | `example.org/event` | `https://example.org/event?utm_source=<placement>` |

- Social handles: `@example` on <platforms>; exceptions: <…>.
- `utm_source` values in use: `print`, `projection`, `livestream`, `social`, `whatsapp`, <…>.
- Rules: no `#fragment` links in print or QR codes; <reserved paths; link shorteners allowed or not>.

## 8. Payment or donation details

One block per destination. Different funds, accounts or purposes stay visually distinct and
clearly labelled wherever they appear together.

| Destination (label as shown) | Method | Details | Link | Colour cue | Status |
|---|---|---|---|---|---|
| <Project fund> | <mobile money / bank / card> | <Business no. 000000 · Account 0000000 · Account name> | `example.org/give` | <token> | confirmed <date> |
| <General account> | <…> | To confirm | <…> | <a different token> | to confirm |

Rules: <what each destination may and may not be called; which is shown by default>.

## 9. Platforms and sizes

| # | Placement | Size | Notes |
|---|---|---|---|
| 1 | <WhatsApp Status> | 1080×1920 | |
| 2 | <Instagram feed> | 1080×1350 | |
| 3 | <Venue screens> | 1920×1080 | <viewing distance> |
| 4 | <Print> | A4 | <printer limits> |

File naming and zip name: <pattern, for example `<SHORT-NAME>-<PIECE>.zip`>.

## 10. Never

- <for example: never use the accent colour for body text>
- <never show two payment destinations in the same style>
- <never change a handle, name or number without asking>
```
