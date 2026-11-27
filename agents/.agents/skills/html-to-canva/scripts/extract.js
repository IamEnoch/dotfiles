// Extract every rendered text line (runs + exact geometry) and the live photos, for the PPTX build.
// Runs inside the static-font print page. Config arrives as window.__CV = {page, live}.
// Writes JSON into body[data-extract]. Every block gets a stable id: data-cv="..." on an
// element (or an ancestor) wins; otherwise the element's structural path inside its page.
(async () => { try {
  await document.fonts.ready;
  await new Promise(r => setTimeout(r, 300));
  const CFG = window.__CV || { page: 'section.page', live: [] };
  const PAGE = CFG.page;
  const SIZE = /^(width|height|inline-size|block-size|(min|max)-(width|height|inline-size|block-size))$/;
  const FOLLOW = /^(-webkit-text-fill-color|-webkit-text-stroke-color|text-emphasis-color|caret-color)$/;
  const pages = [...document.querySelectorAll(PAGE)];
  // stable ids, stamped before any restructuring
  const stamp = (el, id) => {
    el.dataset.cvp = el.dataset.cv ? '@' + el.dataset.cv : id;
    let k = 0;
    for (const c of el.children) { if (c.tagName.toLowerCase() === 'svg') continue; k++; stamp(c, el.dataset.cvp + '/' + c.tagName.toLowerCase() + k); }
  };
  pages.forEach((pg, i) => stamp(pg, 'p' + (i + 1)));
  // freeze computed styles so restructuring can't change selector matches
  const frozen = [...document.querySelectorAll(PAGE + ', ' + PAGE + ' *')].filter(e => !e.closest('svg') || e.tagName.toLowerCase() === 'svg')
    .map(e => [e, getComputedStyle(e)]).map(([e, cs]) => [e, [...cs].filter(p => !SIZE.test(p) && !FOLLOW.test(p)).map(p => [p, cs.getPropertyValue(p)])]);
  frozen.forEach(([e, props]) => {
    const fs = parseFloat((props.find(x => x[0] === 'font-size') || [0, '16px'])[1]);
    props.forEach(([p, v]) => { if (p === 'line-height' && /px$/.test(v)) v = String(parseFloat(v) / fs); e.style.setProperty(p, v, 'important'); });
  });
  const copyStyle = (cs, el) => {
    for (const p of cs) if (!SIZE.test(p)) el.style.setProperty(p, cs.getPropertyValue(p), 'important');
    el.style.setProperty('-webkit-text-fill-color', cs.getPropertyValue('color'), 'important');
  };
  const st = document.createElement('style');
  st.textContent = '.cvnb::before{content:none!important}.cvna::after{content:none!important}' +
    '.cvnf::first-letter{float:none!important;font:inherit!important;color:inherit!important;margin:0!important;padding:0!important;line-height:inherit!important;vertical-align:baseline!important}';
  const roman = n => ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'][n - 1] || String(n);
  const pseudoText = (el, cs) => {
    const c = cs.content; if (!c || c === 'none' || c === 'normal') return '';
    const qnone = (cs.quotes || '').trim() === 'none';
    const qs = ((cs.quotes || '').match(/"([^"]*)"/g) || []).map(s => s.slice(1, -1));
    let out = ''; const re = /"((?:[^"\\]|\\.)*)"|counter\(\s*([\w-]+)\s*(?:,\s*([\w-]+))?\)|open-quote|close-quote/g; let m;
    while ((m = re.exec(c))) {
      if (m[1] !== undefined) out += m[1].replace(/\\([0-9a-fA-F]{1,6})\s?/g, (_, h) => String.fromCodePoint(parseInt(h, 16))).replace(/\\(.)/g, '$1');
      else if (m[2]) { const sib = [...el.parentElement.children].filter(x => x.tagName === el.tagName); const n = sib.indexOf(el) + 1; out += m[3] === 'upper-roman' ? roman(n) : String(n); }
      else if (m[0] === 'open-quote') out += qnone ? '' : (qs[0] || '“'); else if (m[0] === 'close-quote') out += qnone ? '' : (qs[1] || '”');
    }
    return out;
  };
  // ALL text pseudo-elements become real spans (inline ones too: they must become runs)
  const pending = [];
  pages.forEach(pg => pg.querySelectorAll('*').forEach(el => {
    if (el.closest('svg')) return;
    for (const ps of ['::before', '::after']) {
      const cs = getComputedStyle(el, ps); if (cs.display === 'none') continue;
      const txt = pseudoText(el, cs); if (!txt.trim()) continue;
      const sp = document.createElement('cv-p'); copyStyle(cs, sp); sp.textContent = txt; pending.push([el, ps, sp]);
    }
  }));
  const caps = [];
  pages.forEach(pg => pg.querySelectorAll('.dropcap').forEach(el => {
    const cs = getComputedStyle(el, '::first-letter');
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode()) && !n.data.trim()) {}
    if (!n) return; const i = n.data.search(/\S/);
    const sp = document.createElement('cv-p'); copyStyle(cs, sp); sp.textContent = n.data[i]; caps.push([el, n, i, sp]);
  }));
  document.head.appendChild(st);
  pending.forEach(([el, ps, sp]) => { if (ps === '::before') { el.prepend(sp); el.classList.add('cvnb'); } else { el.append(sp); el.classList.add('cvna'); } });
  caps.forEach(([el, n, i, sp]) => { n.data = n.data.slice(0, i) + n.data.slice(i + 1); el.classList.add('cvnf'); el.insertBefore(sp, el.firstChild); });

  // leaves
  const isInline = el => { const d = getComputedStyle(el).display; return d === 'inline' || d === 'contents'; };
  const hidden = el => { const cs = getComputedStyle(el); return cs.display === 'none' || cs.visibility === 'hidden'; };
  const hasText = n => n.textContent.trim() !== '';
  function hasBlockDesc(el) { return [...el.querySelectorAll('*')].some(d => !d.closest('svg') && !isInline(d) && hasText(d)); }
  const blockKids = el => [...el.children].filter(c => !c.closest('svg') && c.tagName !== 'IMG' && !hidden(c) && hasText(c) && (!isInline(c) || hasBlockDesc(c)));
  const leaves = [];
  function walk(el) {
    if (el.closest('svg') || hidden(el) || !hasText(el)) return;
    const kids = blockKids(el);
    if (!kids.length) { leaves.push(el); return; }
    let run = [];
    const flush = () => { if (run.some(n => hasText(n))) { const sp = document.createElement('cv-b'); el.__cvt = (el.__cvt || 0) + 1; sp.dataset.cvp = (el.dataset.cvp || 'x') + '/t' + el.__cvt; sp.style.setProperty('display', 'block', 'important'); run[0].parentNode.insertBefore(sp, run[0]); run.forEach(n => sp.appendChild(n)); leaves.push(sp); } run = []; };
    [...el.childNodes].forEach(n => { if (n.nodeType === 3 || (n.nodeType === 1 && isInline(n) && !hasBlockDesc(n) && n.tagName !== 'BR')) run.push(n); else { flush(); if (n.nodeType === 1) walk(n); } });
    flush();
  }
  pages.forEach(pg => walk(pg));

  const MM = 96 / 25.4;
  const out = { pages: [] };
  const pr = pages.map(p => p.getBoundingClientRect());
  pages.forEach((p, i) => out.pages.push({ blocks: [], images: [], w: pr[i].width / MM, h: pr[i].height / MM }));
  const pageOf = el => pages.indexOf(el.closest(PAGE));
  const styleKey = e => { const cs = getComputedStyle(e); return [cs.fontFamily.split(',')[0].replace(/["']/g, ''), cs.fontWeight, cs.fontStyle, parseFloat(cs.fontSize), cs.color, cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing), cs.textTransform, cs.opacity].join('|'); };
  const tx = (t, tt) => tt === 'uppercase' ? t.toUpperCase() : tt === 'lowercase' ? t.toLowerCase() : t;

  for (const el of leaves) {
    const pi = pageOf(el); if (pi < 0) continue;
    const P = pr[pi];
    const ecs = getComputedStyle(el);
    const hyph = ecs.hyphens === 'auto';
    // chars
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const chars = []; let n; const r = document.createRange();
    while ((n = w.nextNode())) {
      if (n.parentElement.closest('svg') || hidden(n.parentElement)) continue;
      const pcs = getComputedStyle(n.parentElement);
      const key = styleKey(n.parentElement); const tt = pcs.textTransform;
      for (let i = 0; i < n.data.length; i++) {
        r.setStart(n, i); r.setEnd(n, i + 1);
        const rl = [...r.getClientRects()].filter(q => q.width > 0); const rc = rl.length ? rl[rl.length - 1] : r.getClientRects()[0];
        chars.push({ ch: n.data[i], rc, key, tt, el: n.parentElement });
      }
    }
    // lines
    const lines = []; let cur = null;
    for (const c of chars) {
      if (!c.rc || (c.rc.width === 0 && /\s/.test(c.ch))) { if (cur) cur.chars.push(c); continue; }
      if (/\s/.test(c.ch) && cur) { cur.chars.push(c); continue; }
      const mid = (c.rc.top + c.rc.bottom) / 2;
      if (!cur || mid > cur.bottom || mid < cur.top || (c.rc.left < cur.right - 1 && mid > cur.top + (cur.bottom - cur.top) * 0.75)) { cur = { top: c.rc.top, bottom: c.rc.bottom, right: c.rc.right, chars: [] }; lines.push(cur); }
      cur.chars.push(c); cur.top = Math.min(cur.top, c.rc.top); cur.bottom = Math.max(cur.bottom, c.rc.bottom); cur.right = Math.max(cur.right, c.rc.right);
    }
    // segments (a new column starts when a line is above the previous one)
    const segs = []; let seg = null;
    lines.forEach((l, k) => { if (!seg || l.top < lines[k - 1].top - 2) { seg = []; segs.push(seg); } seg.push(l); });
    const er = el.getBoundingClientRect();
    const leafId = (el.dataset.cvp || el.closest('[data-cvp]')?.dataset.cvp || ('p' + (pi + 1) + '/?'));
    for (const [si, sg] of segs.entries()) {
      const blk = { id: leafId + (segs.length > 1 ? '#s' + (si + 1) : ''), align: ecs.textAlign, lines: [], boxL: (er.left - P.left) / MM, boxR: (er.right - P.left) / MM, lh: ecs.lineHeight, tag: el.tagName + '.' + el.className };
      sg.forEach((l, k) => {
        let cs = l.chars;
        while (cs.length && /\s/.test(cs[0].ch)) cs = cs.slice(1);
        while (cs.length && /\s/.test(cs[cs.length - 1].ch)) cs = cs.slice(0, -1);
        if (!cs.length) return;
        // hyphenation: break inside a word (no whitespace between this line's end and the next line's start)
        const next = sg[k + 1] || (segs[segs.indexOf(sg) + 1] || [])[0];
        let hy = false;
        if (hyph && next) {
          const tail = l.chars.slice(l.chars.indexOf(cs[cs.length - 1]) + 1);
          const nf = next.chars.find(c => !/\s/.test(c.ch));
          hy = !tail.some(c => /\s/.test(c.ch)) && nf && /\p{L}/u.test(cs[cs.length - 1].ch) && /\p{L}/u.test(nf.ch);
        }
        const runs = []; let rr = null;
        for (const c of cs) {
          if (!rr || rr.key !== c.key || rr.el !== c.el) { rr = { key: c.key, el: c.el, text: '', x: null, top: 1e9, bottom: -1e9 }; runs.push(rr); }
          rr.text += tx(c.ch, c.tt);
          if (c.rc && c.rc.width > 0 && !/\s/.test(c.ch)) { if (rr.x === null) rr.x = (c.rc.left - P.left) / MM; rr.top = Math.min(rr.top, (c.rc.top - P.top) / MM); rr.bottom = Math.max(rr.bottom, (c.rc.bottom - P.top) / MM); rr.right = (c.rc.right - P.left) / MM; }
        }
        if (hy) runs[runs.length - 1].text += '-';
        const real = cs.filter(c => c.rc && c.rc.width > 0);
        blk.lines.push({ left: (real[0].rc.left - P.left) / MM, right: (Math.max(...real.map(c => c.rc.right)) - P.left) / MM, runs });
      });
      if (blk.lines.length) out.pages[pi].blocks.push(blk);
    }
  }
  // live photos
  const liveSel = (CFG.live || []).join(', ');
  if (liveSel) document.querySelectorAll(liveSel).forEach(im => {
    const pi = pageOf(im); if (pi < 0) return; const P = pr[pi]; const b = im.getBoundingClientRect(); const cs = getComputedStyle(im);
    if (im.tagName !== 'IMG') return;
    out.pages[pi].images.push({ id: im.dataset.cvp || '', src: im.src.startsWith('file://') ? decodeURIComponent(im.src.slice(7)) : im.getAttribute('src'), x: (b.left - P.left) / MM, y: (b.top - P.top) / MM, w: b.width / MM, h: b.height / MM,
      fit: cs.objectFit, pos: cs.objectPosition, radius: cs.borderRadius, nw: im.naturalWidth, nh: im.naturalHeight, filter: cs.filter });
  });
  document.body.dataset.extract = JSON.stringify(out, (k, v) => k === 'el' ? undefined : v);
} catch (e) { document.body.dataset.extract = JSON.stringify({ ERROR: String(e), stack: String(e.stack).slice(0, 800) }); } })();
