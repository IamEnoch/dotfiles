# Connector briefs for Codex

Only Codex has the Canva connector here (`mcp__codex_apps__canva_*`), so connector work goes through `delegate_task` to a Codex child. A fresh brief each time; the child knows nothing else. Fill the `<…>` parts. Every brief keeps the same guard rails, because a half-applied transaction or an edit on the wrong design is expensive to undo:

> One transaction per page. Read the page first, match every target element, and only then apply. If any operation errors, cancel the transaction and report; never commit a partial page. After each commit, re-read the page in a new transaction (cancel it) and report the measured result. Never touch pages, designs or elements not named here. Do not delete designs. Do not change fonts, text or sizes unless the operation says so.

## A. Inventory and units (after an import)

```
Canva design <DESIGN_ID> (<EDIT_URL>). Read-only.
For every page: start an editing transaction, list all elements (id, type, left, top, width, height,
text for text elements), then cancel the transaction. Report the page width/height in Canva units.
Write the result as JSON to <WORKDIR>/build/canva-inventory.json:
{"page_units":[w,h],"pages":[{"page":1,"page_id":"…","elements":[{"id":"…","type":"TEXT","left":…,"top":…,"width":…,"height":…,"text":"…"}]}]}
Report: page count, element counts per page, page size in units.
```

Then set `canva.units_per_mm` = page width units / page width mm.

## B. Apply a sync plan (route "connector")

```
Canva design <DESIGN_ID>. Apply the edits in <WORKDIR>/build/sync-plan.json, pages <N,…> only
(the pages whose "route" is "connector").
Coordinates are Canva units of this design (units_per_mm = <U>).

For each page: start a transaction and list elements. Match each op's "find" to exactly one element:
  text ops: the TEXT element whose text equals find.text (whitespace-normalised) and whose left/top
  are nearest to find.left/find.top (within 15 units); image ops: the image nearest find.left/top.
  If an op matches zero or several elements, cancel the page and report it; don't guess.
Then apply in this order: replace_text, format_text, resize_element (text: width only, never
height), position_element (always after a resize, because resizing moves the box), delete_element.
replace_background / replace_photo: upload the file with create_upload_url (one raw POST of the bytes,
Content-Type application/octet-stream), then update_fill on the matched image (the background
is the full-page image at 0,0).
Commit the page, re-read it, and report per op: element id, done/failed, final left/top/width.
```

Afterwards: export via the browser, `cv audit`, then `cv accept` only if it passes.

## C. Page re-import (route "reimport")

```
Canva designs: main <MAIN_ID>; freshly imported <NEW_ID> (contains page(s) <k…> rebuilt from the HTML,
in the same order). Goal: main has the rebuilt page(s) in place of its page(s) <N…>; all other pages untouched.
1. copy_design main → keep as a backup copy titled "<title> (backup before page <N> sync)". Report its id.
2. If the connector can merge/insert pages (merge_designs or equivalent): insert NEW page k after
   main page N, then delete the old page N. If it cannot, stop and report which tools exist.
3. Re-read main: page count must be unchanged, and page N's text must match NEW page k's text.
```

If the connector can't move pages, fall back to rebuilding the whole design from the PPTX. The calibration file makes that a single import plus an audit.

## D. True A4 from an A1 import (only if the user wants a real A4 page size)

```
Source <A1_ID> read-only. 1) Resize a copy to custom 793.7008 x 1122.5197 px (A4 @ 96 dpi); report the new id
and the returned page size. 2) s = new page width / source page width. For every page and every element
(match by element id; the copy keeps ids): text → resize_element width = src.width*s (NO height),
then position_element left = src.left*s, top = src.top*s; images → resize width and height *s, then position.
Full-page backgrounds: 0,0 and the page size. Commit per page, re-read, and report the max residuals in px
(left, top, width; image height) per page.
```

Known issue: the resize can shrink some text to about 75%, and the connector can't set fractional sizes. Fix those boxes in the editor (see browser-steps.md), then export and run `cv audit`.
