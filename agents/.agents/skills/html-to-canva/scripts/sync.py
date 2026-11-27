"""Diff the current build against what is in Canva (the synced/ snapshot) and plan the edits.

Matching is by content first, then by id, so inserting a paragraph does not make every later
box look "changed":  1) same page + identical text + same id or unique text  -> same box (maybe moved)
                     2) same id                                              -> edited text
                     3) same page, similar text, nearby                      -> edited text
                     4) the rest                                             -> added / removed
Each page then gets a route:
  connector  every change is something the Canva connector can apply (text, move, width, delete,
             colour/bold/italic/whole-number size, background or photo swap)
  editor     tiny changes the connector cannot express (font family, letter-spacing, fractional
             size, mixed-style text edits): do them in the Canva editor by hand
  reimport   new text boxes or many changes: rebuild just that page from the PPTX
"""
import difflib, json, os, shutil
import cvlib

MOVE_TOL = 0.15   # mm


def _load(d):
    return (json.load(open(os.path.join(d, 'boxes.json'))), json.load(open(os.path.join(d, 'images.json'))),
            json.load(open(os.path.join(d, 'state.json'))))


def match(old, new):
    pairs, used_o, used_n = [], set(), set()
    by_page = lambda L: {p: [b for b in L if b['page'] == p] for p in {b['page'] for b in L}}
    O, N = by_page(old), by_page(new)
    for p in set(O) | set(N):
        os_, ns = O.get(p, []), N.get(p, [])
        fam = lambda b: b['sig'].split('|')[0]
        dist = lambda o, n: abs(o['box']['left'] - n['box']['left']) + abs(o['box']['top'] - n['box']['top'])
        take = lambda o, n: (pairs.append((o, n)), used_o.add(o['id']), used_n.add(n['id']))
        # 1a. same id, same text
        oid = {o['id']: o for o in os_}
        for n in ns:
            o = oid.get(n['id'])
            if o and o['text'] == n['text']: take(o, n)
        # 1b. identical text that is unique on BOTH sides, same font family, not across the page
        cnt_o = {}; cnt_n = {}
        for o in os_: cnt_o[o['text']] = cnt_o.get(o['text'], 0) + 1
        for n in ns: cnt_n[n['text']] = cnt_n.get(n['text'], 0) + 1
        for n in ns:
            if n['id'] in used_n or cnt_n[n['text']] != 1 or cnt_o.get(n['text']) != 1: continue
            o = next(o for o in os_ if o['text'] == n['text'])
            if o['id'] not in used_o and fam(o) == fam(n) and dist(o, n) < 60: take(o, n)
        # 2. same id: edited text (or restyled) in place
        for n in ns:
            if n['id'] in used_n: continue
            o = oid.get(n['id'])
            if o and o['id'] not in used_o: take(o, n)
        # 3. similar text, same family, nearby (short strings must be very close)
        for n in ns:
            if n['id'] in used_n: continue
            best, score = None, 0
            for o in os_:
                if o['id'] in used_o or fam(o) != fam(n): continue
                r = difflib.SequenceMatcher(None, o['text'], n['text']).ratio()
                d = dist(o, n)
                if len(n['text']) < 8 and d > 5: continue
                sc = r - d / 100
                if r > 0.55 and sc > score: best, score = o, sc
            if best: take(best, n)
    removed = [o for o in old if o['id'] not in used_o]
    added = [n for n in new if n['id'] not in used_n]
    return pairs, removed, added


def plan(cfg):
    if os.path.exists(os.path.join(cfg.dir, 'FROZEN')):
        raise SystemExit('Design is frozen: Canva is the master now. Edit in Canva, not in the HTML.')
    if not os.path.exists(os.path.join(cfg.synced, 'boxes.json')):
        raise SystemExit('Nothing synced yet: import build/<name>.pptx, verify it, then run `cv.py accept`.')
    old_b, old_i, old_s = _load(cfg.synced)
    new_b, new_i, new_s = _load(cfg.build)
    u = cfg.canva.get('units_per_mm')
    cu = (lambda v: round(v * u, 2)) if u else (lambda v: None)
    pages = {}
    P = lambda p: pages.setdefault(p, dict(page=p, ops=[], editor=[], reimport_reasons=[]))
    if old_s['pages'] != new_s['pages']:
        P(0)['reimport_reasons'].append(f"page count {old_s['pages']} -> {new_s['pages']}: rebuild the design (or add/delete pages by hand)")
    pairs, removed, added = match(old_b, new_b)
    def where(o):
        return dict(text=o['text'], left=cu(o['box']['left']), top=cu(o['box']['top']), left_mm=o['box']['left'], top_mm=o['box']['top'])
    for o, n in pairs:
        pg = P(n['page'])
        if n['page'] != o['page']:
            pg['reimport_reasons'].append(f'"{n["text"][:30]}" moved from page {o["page"]}')
            continue
        if o['text'] != n['text']:
            if o.get('mixed') or n.get('mixed'):
                pg['editor'].append(dict(kind='text', find=where(o), new_text=n['text'], why='box mixes styles; replace_text would flatten them'))
            else:
                pg['ops'].append(dict(op='replace_text', find=where(o), text=n['text']))
        if o['lines'] != n['lines'] and o['text'] != n['text']:
            pass  # line breaks are part of the text
        b0, b1 = o['box'], n['box']
        if abs(b0['left'] - b1['left']) > MOVE_TOL or abs(b0['top'] - b1['top']) > MOVE_TOL:
            pg['ops'].append(dict(op='position_element', find=where(o), left=cu(b1['left']), top=cu(b1['top']), left_mm=b1['left'], top_mm=b1['top']))
        if abs(b0['width'] - b1['width']) > MOVE_TOL:
            pg['ops'].append(dict(op='resize_element', find=where(o), width=cu(b1['width']), width_mm=b1['width'], note='text: width only (Canva refuses height)'))
        s0, s1 = o.get('style') or {}, n.get('style') or {}
        fmt = {}
        if s0.get('color') != s1.get('color'): fmt['color'] = '#' + str(s1.get('color'))
        if s0.get('bold') != s1.get('bold'): fmt['font_weight'] = 'bold' if s1.get('bold') else 'normal'
        if s0.get('italic') != s1.get('italic'): fmt['font_style'] = 'italic' if s1.get('italic') else 'normal'
        hard = []
        if s0.get('font') != s1.get('font'): hard.append(f"font {s0.get('font')} -> {s1.get('font')}")
        if s0.get('spacing') != s1.get('spacing'): hard.append(f"letter-spacing {s0.get('spacing')} -> {s1.get('spacing')}px")
        if s0.get('pt') != s1.get('pt'):
            if u and s1.get('pt') is not None and abs(s1['pt'] * u * cvlib.MM_PER_PT - round(s1['pt'] * u * cvlib.MM_PER_PT)) < 0.05:
                fmt['font_size'] = round(s1['pt'] * u * cvlib.MM_PER_PT)
            else:
                hard.append(f"size {s0.get('pt')} -> {s1.get('pt')}pt (connector takes whole Canva units only)")
        if (fmt or hard) and (o.get('mixed') or n.get('mixed')):
            hard.append('box mixes styles; whole-element formatting would flatten it')
            fmt = {}
        if fmt:
            pg['ops'].append(dict(op='format_text', find=where(o), formatting=fmt))
        if hard:
            pg['editor'].append(dict(kind='style', find=where(o), change='; '.join(hard)))
    for o in removed:
        P(o['page'])['ops'].append(dict(op='delete_element', find=where(o)))
    for n in added:
        P(n['page'])['reimport_reasons'].append(f'new text box "{n["text"][:40]}" (connector cannot create text)')
    # backgrounds
    for k, h in new_s['bg'].items():
        if old_s['bg'].get(k) != h:
            p = int(k[1:])
            P(p)['ops'].append(dict(op='replace_background', file=os.path.join(cfg.build, 'bg', f'{k}.jpg'),
                                    how='upload with create_upload_url, then update_fill on the full-page image at 0,0'))
    # live photos
    oi = {i['id']: i for i in old_i}
    for i in new_i:
        o = oi.pop(i['id'], None)
        if not o:
            P(i['page'])['reimport_reasons'].append(f'new live photo {i["id"]}'); continue
        if o['render_sha'] != i['render_sha']:
            P(i['page'])['ops'].append(dict(op='replace_photo', find=dict(left=cu(o['x']), top=cu(o['y']), left_mm=o['x'], top_mm=o['y']),
                                            file=os.path.join(cfg.dir, i['render']), how='upload, then update_fill on that image element'))
        if any(abs(o[k] - i[k]) > MOVE_TOL for k in ('x', 'y', 'w', 'h')):
            P(i['page'])['ops'].append(dict(op='position_resize_image', find=dict(left=cu(o['x']), top=cu(o['y'])),
                                            left=cu(i['x']), top=cu(i['y']), width=cu(i['w']), height=cu(i['h'])))
    for o in oi.values():
        P(o['page'])['ops'].append(dict(op='delete_element', find=dict(left=cu(o['x']), top=cu(o['y']), kind='image')))
    # routes
    total = {p: sum(1 for b in new_b if b['page'] == p) for p in range(1, new_s['pages'] + 1)}
    out = []
    for p in sorted(pages):
        pg = pages[p]
        if not (pg['ops'] or pg['editor'] or pg['reimport_reasons']):
            continue
        n_text = sum(1 for o in pg['ops'] if o['op'] in ('replace_text', 'position_element', 'delete_element'))
        if p and total.get(p) and n_text > 0.4 * total[p]:
            pg['reimport_reasons'].append(f'{n_text} of {total[p]} boxes change')
        pg['route'] = 'reimport' if pg['reimport_reasons'] else ('editor' if pg['editor'] else 'connector')
        out.append(pg)
    result = dict(design=cfg.canva, units_per_mm=u, pages=out,
                  summary={r: [p['page'] for p in out if p['route'] == r] for r in ('connector', 'editor', 'reimport')})
    json.dump(result, open(os.path.join(cfg.build, 'sync-plan.json'), 'w'), indent=1, ensure_ascii=False)
    open(os.path.join(cfg.build, 'sync-plan.md'), 'w').write(render(cfg, result))
    return result


def render(cfg, r):
    L = [f'# Sync plan: {cfg.name}', '',
         f"Canva design: {r['design'].get('design_id') or '(not set in canva.json)'} {r['design'].get('edit_url') or ''}",
         f"Units: {r['units_per_mm'] or 'UNKNOWN: set canva.units_per_mm (page width in Canva units / page width mm)'} Canva units per mm", '']
    if not r['pages']:
        return '\n'.join(L + ['**Canva is already up to date with the HTML.**'])
    s = r['summary']
    L += [f"- Connector (Codex can apply): pages {s['connector'] or 'none'}",
          f"- Editor (by hand in Canva): pages {s['editor'] or 'none'}",
          f"- Re-import page from PPTX: pages {s['reimport'] or 'none'}", '']
    for pg in r['pages']:
        L += [f"## Page {pg['page'] or '(whole design)'}: {pg['route']}", '']
        for x in pg['reimport_reasons']:
            L.append(f'- re-import because: {x}')
        for o in pg['ops']:
            f = o.get('find', {})
            loc = f'"{f.get("text", "")[:50]}" at ({f.get("left")}, {f.get("top")})' if f else ''
            rest = {k: v for k, v in o.items() if k not in ('op', 'find', 'how')}
            L.append(f"- `{o['op']}` {loc} -> {json.dumps(rest, ensure_ascii=False)}" + (f" ({o['how']})" if o.get('how') else ''))
        for e in pg['editor']:
            f = e['find']
            L.append(f"- EDITOR: \"{f['text'][:50]}\" ({f['left_mm']:.1f}, {f['top_mm']:.1f} mm): {e.get('change') or ('text -> ' + repr(e.get('new_text', '')[:80]))}" + (f" ({e['why']})" if e.get('why') else ''))
        L.append('')
    return '\n'.join(L)


def accept(cfg):
    """The build is now what Canva holds (after a verified import or sync)."""
    os.makedirs(cfg.synced, exist_ok=True)
    for f in ('boxes.json', 'images.json', 'state.json', 'reference.pdf'):
        shutil.copy2(os.path.join(cfg.build, f), os.path.join(cfg.synced, f))
    for d in ('bg', 'img'):
        if os.path.exists(os.path.join(cfg.synced, d)):
            shutil.rmtree(os.path.join(cfg.synced, d))
        shutil.copytree(os.path.join(cfg.build, d), os.path.join(cfg.synced, d))
