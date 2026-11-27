// Lint probe: collects everything the Canva-safety rules need, per text-bearing element.
// Config arrives as window.__CV = {page, live}. Writes JSON into body[data-inspect].
(async () => { try {
  await document.fonts.ready;
  await new Promise(r => setTimeout(r, 300));
  const CFG = window.__CV || { page: 'section.page', live: [] };
  const pages = [...document.querySelectorAll(CFG.page)];
  const MM = 96 / 25.4;
  const out = { pages: pages.map(p => { const r = p.getBoundingClientRect(); return { w: r.width / MM, h: r.height / MM }; }), text: [], images: [], bgimages: 0, effects: {}, untagged: 0, tagged: 0 };
  const live = new Set(CFG.live && CFG.live.length ? [...document.querySelectorAll(CFG.live.join(', '))] : []);
  const pageOf = el => pages.indexOf(el.closest(CFG.page));
  const desc = el => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (el.classList.length) s += '.' + [...el.classList].slice(0, 3).join('.');
    return s;
  };
  const hidden = cs => cs.display === 'none' || cs.visibility === 'hidden';
  const effect = (k) => { out.effects[k] = (out.effects[k] || 0) + 1; };
  const record = (el, cs, text, pseudo) => {
    const pi = pageOf(el); if (pi < 0) return;
    const fam = cs.fontFamily.split(',')[0].replace(/["']/g, '').trim();
    out.text.push({
      page: pi + 1, el: desc(el) + (pseudo || ''), text: text.slice(0, 80), chars: [...new Set([...text])].join(''),
      family: fam, weight: parseInt(cs.fontWeight), italic: cs.fontStyle !== 'normal', size: parseFloat(cs.fontSize),
      color: cs.color, fill: cs.webkitTextFillColor, opacity: parseFloat(cs.opacity),
      shadow: cs.textShadow !== 'none', clip: (cs.backgroundClip || cs.webkitBackgroundClip || '').includes('text'),
      transform: cs.transform, writing: cs.writingMode, blend: cs.mixBlendMode, filter: cs.filter,
      synthesis: cs.fontSynthesis, variation: cs.fontVariationSettings, features: cs.fontFeatureSettings,
    });
  };
  for (const pg of pages) {
    const w = document.createTreeWalker(pg, NodeFilter.SHOW_TEXT);
    const seen = new Set(); let n;
    while ((n = w.nextNode())) {
      const el = n.parentElement;
      if (!n.data.trim() || el.closest('svg') || seen.has(el)) continue;
      const cs = getComputedStyle(el); if (hidden(cs)) continue;
      seen.add(el);
      const own = [...el.childNodes].filter(c => c.nodeType === 3).map(c => c.data).join('');
      record(el, cs, own.trim() || el.textContent.trim());
      if (el.closest('[data-cv]')) out.tagged++; else out.untagged++;
    }
    for (const el of pg.querySelectorAll('*')) {
      if (el.closest('svg')) continue;
      for (const ps of ['::before', '::after', '::first-letter']) {
        const cs = getComputedStyle(el, ps);
        if (ps === '::first-letter') { if (!el.classList.contains('dropcap') && cs.float === 'none' && cs.fontSize === getComputedStyle(el).fontSize) continue; }
        else if (!cs.content || cs.content === 'none' || cs.content === 'normal' || !/["\w]/.test(cs.content.replace(/^""$/, ''))) continue;
        const txt = ps === '::first-letter' ? (el.textContent.trim()[0] || '') : cs.content.replace(/^"|"$/g, '');
        if (!txt.trim() || txt === '""') continue;
        record(el, cs, txt, ps);
      }
      const cs = getComputedStyle(el);
      if (cs.backgroundImage && cs.backgroundImage.includes('url(')) out.bgimages++;
      if (cs.backgroundImage && cs.backgroundImage.includes('gradient')) effect('gradient');
      if (cs.maskImage && cs.maskImage !== 'none') effect('mask');
      if (cs.webkitMaskImage && cs.webkitMaskImage !== 'none') effect('mask');
      if (cs.mixBlendMode !== 'normal') effect('blend');
      if (cs.filter !== 'none' && !live.has(el)) effect('filter');
      if (cs.boxShadow !== 'none') effect('box-shadow');
      if (parseFloat(cs.opacity) < 1) effect('opacity');
      if (cs.backdropFilter && cs.backdropFilter !== 'none') effect('backdrop-filter');
    }
    for (const im of pg.querySelectorAll('img')) {
      const r = im.getBoundingClientRect(); if (!r.width) continue;
      out.images.push({ page: pageOf(im) + 1, el: desc(im), src: im.getAttribute('src'), live: live.has(im), w: r.width / MM, h: r.height / MM, nw: im.naturalWidth, nh: im.naturalHeight, ok: im.complete && im.naturalWidth > 0 });
    }
  }
  out.liveMatched = live.size;
  document.body.dataset.inspect = JSON.stringify(out);
} catch (e) { document.body.dataset.inspect = JSON.stringify({ ERROR: String(e), stack: String(e.stack).slice(0, 800) }); } })();
