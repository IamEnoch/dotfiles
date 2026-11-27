# Checks and lessons

## Before showing a render

- [ ] Every fact matches the source (names, event name, Paybill/account, links, dates, times).
- [ ] Palette: one family; accent used for one job; no glow on type, tags or badges.
- [ ] Margins ≥ 10% at the sides; footer clear of the bottom; nothing in the TikTok UI zones on 9:16.
- [ ] Hierarchy reads in order: logo → tag → headline → category → rows → closing → footer.
- [ ] No large dead area while text is cramped elsewhere.
- [ ] No one-word last lines; no lines touching icons; text over photos has a veil behind it.
- [ ] Zoomed crops (3×) of icons, logo, small text and photo edges look clean.
- [ ] Handles/URLs lowercase; `@pefamagina` unchanged.
- [ ] QR codes decoded from the rendered slide (and the degraded copy).

## Before handover

- [ ] Every size rendered at 2× → exact px; names per `export-handover.md`.
- [ ] Print PDF: A4, vector text (`pdffonts`), 300 dpi crop checked.
- [ ] Canva (if used): audit passes apart from the known artefact; one project; page titles
      read back after a reload; test imports trashed (tell the user); sources kept until the user OKs trashing.
- [ ] Zip listed (`unzip -l`) and size stated; WhatsApp-as-document advice given.
- [ ] Open questions stated plainly (placeholders, unverified wording).

## Lessons from the media notice (what the user rejected, in order)

1. **Event photo on a general notice.** The cathedral photo was rejected: use a subject that
   says what the notice is about (a camera for filming), like the references.
2. **HUD gimmicks.** The REC dot and LIVE tag: "no need for this".
3. **Dead space.** A big empty dark area above the text: "wasted space". Move the headline
   into it instead of adding decoration.
4. **Boxed callout with a gold side bar**: "old school". Use icon rows instead.
5. **Hero too dominant**: "stealing the show". Make it smaller, move it right, dim it, and
   put it behind the words.
6. **Words must carry the page** (Ruach): overlay text on the scene and let it lead.
7. **Gold is the event colour.** For everyday pieces, consider blue only. On the notice the user
   then asked for yellow back, so offer it as an option and don't assume.
8. **Thin outline icons are weak**: use solid badge icons.
9. **Fonts**: a Ruach-like geometric sans for body (Montserrat), not Poppins.
10. **"Not shiny"**: remove glows from the tag and the accent headline.
11. **Handles and URLs in lowercase**, inside a thin outline pill (Citizen TV reference).
12. **Margins**: the user asked twice for more edge padding. Start at 10%.
13. **One Canva project** with titled pages, not separate designs per size.
14. When the user says "fonts feel out", verify with evidence (`pdffonts`, connector read)
    before changing anything, then report what you checked.

## Process lessons

- Read the attached screenshots closely: they point at the exact element to change.
- Keep every intermediate as `vN.html`; the user sometimes wants to go back.
- Long tool runs: send the user a one-line status every few steps.
