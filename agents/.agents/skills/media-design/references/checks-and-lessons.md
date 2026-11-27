# Checks and lessons

## Before showing a render

- [ ] The brand file was read, and every brand value in the piece comes from it.
- [ ] Every fact matches the source: names, the event name, account details, links, dates, times.
- [ ] Palette: one family; the accent does one job; no glow on type, tags or badges.
- [ ] Margins ≥ 10% at the sides; footer clear of the bottom; nothing in the app-interface zones on 9:16.
- [ ] The hierarchy reads in order: logo → tag → headline → category → rows → closing → footer.
- [ ] No large dead area while text is cramped elsewhere.
- [ ] No one-word last lines; no lines touching icons; text over a photo has a veil behind it.
- [ ] Zoomed crops (3×) of icons, the logo, small text and photo edges look clean.
- [ ] Handles and URLs are written exactly as the brand file gives them.
- [ ] Two payment destinations, if shown, can't be mistaken for each other.
- [ ] QR codes decoded from the rendered piece, and from the degraded copy.

## Before handover

- [ ] Every size rendered at 2× and downsampled to the exact px; names per `export-handover.md`.
- [ ] Print PDF: right page size, vector text (`pdffonts`), a 300 dpi crop checked.
- [ ] Canva (if used): the audit passes apart from explained artefacts; one project; page
      titles read back after a reload; test imports trashed (tell the user); sources kept
      until the user agrees to trash them.
- [ ] Zip listed (`unzip -l`) and its size stated; advice given on sending files as documents.
- [ ] Open questions stated plainly (placeholders, wording you couldn't verify).
- [ ] New lasting decisions written into the brand file.

## Lessons (each one was a rejected render)

1. **The picture must say what the piece is about.** A stock picture of the organisation's
   building on a general notice was rejected. Use a subject that fits the message.
2. **No gimmicks.** Fake interface elements (a REC dot, a LIVE tag) were removed on sight.
3. **Dead space is wasted space.** A large empty area above cramped text: move the headline
   into it. Don't fill it with decoration.
4. **Boxed callouts with a coloured side bar look dated.** Use icon rows.
5. **A hero image that dominates steals the show.** Make it smaller, move it aside, dim it,
   and put it behind the words.
6. **Words carry the page.** Overlay the text on the scene and let it lead.
7. **An event's colour isn't the everyday colour.** Offer the everyday palette for general
   pieces, but show both: users sometimes want the event accent back once they see the
   plain version. Don't assume either way.
8. **Thin outline icons are weak.** Use solid badge icons.
9. **Body font matters more than expected.** When the user points at a reference they
   like, match the *kind* of face (geometric, humanist, condensed), using the brand's own.
10. **"Not shiny".** Remove glows from tags and accent headlines.
11. **Handles and URLs in lowercase**, inside a thin outline pill.
12. **Margins.** Users ask for more edge padding, rarely for less. Start at 10%.
13. **One Canva project with titled pages**, not a separate design per size.
14. **Verify before changing.** When the user says something "feels off" (fonts, colour,
    alignment), check with evidence first, then report what you checked.
15. **Photos of people: never retouch or tone-shift, only cut out cleanly.** A cut with a
    rough or uneven edge is also rejected; take the time on hair and shoulders.
16. **Two payment destinations must not look alike.** When there are two different funds or
    accounts, make them visually distinct and clearly labelled so they can't be confused.
17. **Printed links are paths, not fragments.** A `#section` link breaks in QR tools and
    can't be typed reliably.
18. **Brand facts live in the brand file.** A value remembered from an earlier piece or
    another project is a guess until the file confirms it.

## Process lessons

- Read attached screenshots closely: they point at the exact element to change.
- Keep every intermediate as `vN.html`; users sometimes want to go back.
- On long tool runs, send the user a one-line status every few steps.
- Ask only for what you can't verify, and ask it all in one message.
