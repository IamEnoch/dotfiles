# Canva web app steps (browser tools)

The tool names below (`preview_open`, `preview_evaluate`, `preview_act`, `preview_resize`, `preview_snapshot`) are those of one agent browser; with another, use its equivalents for open, run script, click/upload, resize and snapshot. The steps were last verified in late 2026. Canva's UI changes, so if a button isn't found, take a snapshot, find the new label, and update this file.

Open a tab with `preview_open` on `https://www.canva.com/`. The user is already signed in; never sign out. If Canva shows a login page, stop and ask the user to sign in.

## Import a PPTX (or PDF)

1. Open the upload dialog by running this with `preview_evaluate` on the home page:

```js
new Promise(r=>{let n=0;const iv=setInterval(()=>{const b=document.querySelector('button[aria-label="Create a design"]');
if(b||++n>20){clearInterval(iv);if(b)b.click();setTimeout(()=>{const up=[...document.querySelectorAll('button')].find(x=>x.innerText.trim()==='Upload');
if(up)up.click();setTimeout(()=>r({create:!!b,upload:!!up,inputs:document.querySelectorAll('input[type=file][multiple]').length}),1500)},1500)}},500)})
```

2. Send the file with `preview_act`, using action `upload`, locator `input[type=file][multiple]`, and `paths: ["/abs/path/build/<name>.pptx"]`.
3. Wait for the editor. The URL contains `/design/<ID>/`. Poll `location.href` for up to about 90 s. Conversion of a 12-page document takes 20–60 s.
4. Record the design ID and edit URL in `canva.json`. Rename the design with the title field, or ask Codex for `update_title`.

Canva may open the design inside an iframe wrapper. Every script below therefore searches `document` and the same-origin iframes.

## Export a PDF (for `cv audit`)

1. Wait until the editor has loaded: a `Share` button is present, and inside the iframe "Loading finished" shows.
2. Run this with `preview_evaluate`:

```js
new Promise(r=>{const docs=[document,...[...document.querySelectorAll('iframe')].map(f=>{try{return f.contentDocument}catch(e){return null}}).filter(Boolean)];
const d=docs.find(x=>[...x.querySelectorAll('button,[role=menuitem]')].some(b=>(b.innerText||'').trim()==='Share'));if(!d)return r('noshare');
const click=t=>{const b=[...d.querySelectorAll('button,[role=menuitem],[role=button]')].find(x=>x.innerText&&x.innerText.trim()===t);if(b)b.click();return !!b};
click('Share');setTimeout(()=>{click('Download');setTimeout(()=>{const ft=d.querySelector("[aria-label='File type']");if(!ft)return r('noft');ft.click();
setTimeout(()=>{const o=[...d.querySelectorAll('[role=option]')].find(o=>/^PDF/.test(o.innerText.trim()));if(o)o.click();
setTimeout(()=>{const dl=[...d.querySelectorAll('button')].filter(x=>x.innerText.trim()==='Download').pop();dl.click();r('clicked')},1200)},1000)},2000)},1500)})
```

   `^PDF` picks the first PDF option, which is "PDF Standard". For print files, pick "PDF Print". When asked, tick "Crop marks and bleed" and keep all pages.
3. Get the signed download link (it expires in minutes) and fetch it:

```js
new Promise(r=>{const t0=Date.now();const iv=setInterval(()=>{const docs=[document,...[...document.querySelectorAll('iframe')].map(f=>{try{return f.contentDocument}catch(e){return null}}).filter(Boolean)];
const a=docs.flatMap(d=>[...d.querySelectorAll('a')]).find(x=>/export-download\.canva\.com/.test(x.href));if(a||Date.now()-t0>15000){clearInterval(iv);r(a?a.href:null)}},1000)})
```

```bash
curl --fail --location -o build/canva-export.pdf '<href>'
pdfinfo build/canva-export.pdf   # page count, and Producer: Canva
```

## Move a test design to Trash

Open the design's edit URL. Check that the title is not the keeper's: abort if it matches the title of the design the user is keeping. Then run this:

```js
new Promise(r=>{const docs=[document,...[...document.querySelectorAll('iframe')].map(f=>{try{return f.contentDocument}catch(e){return null}}).filter(Boolean)];
for(const d of docs){const f=[...d.querySelectorAll('button,[role=menuitem]')].find(x=>(x.innerText||'').trim()==='File');
if(f){f.click();setTimeout(()=>{const m=[...d.querySelectorAll('[role=menuitem],button')].find(x=>(x.innerText||'').trim()==='Move to Trash');
if(!m)return r('nomenu');m.click();setTimeout(()=>{const dlg=d.querySelector('[role=dialog],[role=alertdialog]');
const b=dlg&&[...dlg.querySelectorAll('button')].find(x=>/Move to Trash|Delete/.test(x.innerText));if(b)b.click();r({title:document.title,confirmed:!!b})},1200)},1200);return}}r('nofile')})
```

Trash keeps designs for 30 days. Tell the user what you trashed.

## Editor fixes (the "editor" route)

For font family, letter-spacing, decimal sizes, or partial-text styling:
1. Select the element by clicking at its position. Canva units come from `sync-plan.md`; convert them with `units_per_mm` and the on-screen page scale.
2. Use the toolbar's font, size and spacing controls.
3. Re-export and run `cv audit`. The editor's size box isn't reliable right after an edit, so trust the export instead.

## Hidden preview tabs (exports stuck on "Preparing")

A preview tab running in the background pauses `requestAnimationFrame` and slows timers, so a
script that waits for the export can time out. Start the export with
`preview_evaluate(awaitPromise:false)`. Then wake the tab with `preview_resize` (change the width
by 1 px) and poll for the `a[href*="export-download.canva.com"]` link in a separate call.
Filter that link by the design ID, because older links stay on the page.

## Several sizes in one project

PPTX import is one slide size per design, so import each size separately. To combine them,
have a Codex child with the Canva connector call `canva_merge_designs` (`insert_pages` /
`delete_pages`). Mixed page sizes are kept. Merge into a new design and leave the audited
sources unchanged until the user agrees to trash them.

## Page titles (connector can't set them)

In the editor, the page thumbnail strip has one `input[aria-label="Page title"]` per page. Each
is only 8 px wide until it is focused. For each page:
1. Read the input's x position.
2. Click x+4 twice with `preview_act`. The first click selects the page, the second focuses
   the input.
3. Check `document.activeElement` is that input. Set its value with the native
   `HTMLInputElement.prototype` value setter, then dispatch an `input` event.
4. `preview_act press Enter`.

Reload the design and read all the titles back before reporting.
