"""Verify a Canva export against the HTML reference, and measure per-box calibration.

audit:      every text run of reference.pdf is found in the Canva PDF and compared for
            position (mm), font, size and colour; plus page count/aspect and a pixel diff
            per page with side-by-side images.
calibrate:  for every manifest box, where Canva put its first glyph vs where it belongs;
            accumulated into <work>/calib.json, which the next build subtracts.
Both scale the Canva PDF to the reference page width, so Canva's A1-sized PPTX imports compare directly.
"""
import collections, json, os, re, statistics as st
import cvlib

MM = 72 / 25.4


def _font(name):
    n = re.sub(r'^[A-Z]{6}\+', '', name)
    n = re.sub(r'(?i)[-_ ]?(regular|roman)$', '', n)
    return re.sub(r'[^a-z0-9]', '', n.lower())


def chars(page, k):
    out = []
    for b in page.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                for c in s['chars']:
                    out.append(dict(c=c['c'], x=c['origin'][0] / MM * k, y=c['origin'][1] / MM * k, font=s['font'], size=s['size'] * k, color=s['color'], span=id(s)))
    return out


def _flat(cc):
    keep = [c for c in cc if not c['c'].isspace() and c['c'] not in '‐-­']
    big, idx = '', []
    for k, c in enumerate(keep):
        t = {'ﬁ': 'fi', 'ﬂ': 'fl'}.get(c['c'], c['c'])
        big += t; idx += [k] * len(t)
    return keep, big, idx


def audit(cfg, canva_pdf, tol=0.5, out_dir=None):
    import pymupdf as fitz
    ref = fitz.open(os.path.join(cfg.build, 'reference.pdf'))
    cv = fitz.open(canva_pdf)
    out_dir = out_dir or os.path.join(cfg.build, 'audit')
    os.makedirs(out_dir, exist_ok=True)
    rep, fails, stats = [], 0, collections.defaultdict(list)
    if len(ref) != len(cv):
        rep.append(f'**FAIL: page count** reference {len(ref)} vs Canva {len(cv)}'); fails += 1
    for pi in range(min(len(ref), len(cv))):
        R, C = ref[pi].rect, cv[pi].rect
        if abs(R.width / R.height - C.width / C.height) > 0.002:
            rep.append(f'**FAIL: page {pi + 1} aspect** reference {R.width:.0f}x{R.height:.0f}pt vs Canva {C.width:.0f}x{C.height:.0f}pt'); fails += 1
        k_ref = cfg.page_w / (R.width / MM)
        k_cv = cfg.page_w / (C.width / MM)
        rc = chars(ref[pi], k_ref)
        keep, big, idx = _flat(chars(cv[pi], k_cv))
        runs, cur = [], None
        for c in rc:
            if cur and c['span'] == cur[0]['span']: cur.append(c)
            else: cur = [c]; runs.append(cur)
        bad = []
        for r in runs:
            cs = [c for c in r if not c['c'].isspace() and c['c'] not in '‐-­']
            s = ''.join({'ﬁ': 'fi', 'ﬂ': 'fl'}.get(c['c'], c['c']) for c in cs)
            label = ''.join(c['c'] for c in r).strip()[:60]
            if len(s) < 2:
                continue
            f0 = cs[0]
            occ = [m.start() for m in re.finditer(re.escape(s), big)]
            if not occ:
                bad.append(('high', f'MISSING "{label}" ({_font(f0["font"])} {f0["size"]:.1f}pt) at x{f0["x"]:.0f} y{f0["y"]:.0f}mm')); continue
            o = min(occ, key=lambda o: (keep[idx[o]]['x'] - f0['x']) ** 2 + (keep[idx[o]]['y'] - f0['y']) ** 2)
            g, gl = keep[idx[o]], keep[idx[o + len(s) - 1]]
            dx, dy = g['x'] - f0['x'], g['y'] - f0['y']
            notes, sev = [], 'low'
            if abs(dx) > 40 or abs(dy) > 40:
                bad.append(('high', f'FAR {dx:+.0f},{dy:+.0f}mm (matched elsewhere?) "{label}"')); continue
            stats[(_font(f0['font']), round(f0['size'], 1))].append(dy)
            if abs(dx) > tol or abs(dy) > tol:
                notes.append(f'moved dx{dx:+.2f} dy{dy:+.2f}mm'); sev = 'high' if max(abs(dx), abs(dy)) > 1.5 else 'medium'
            if _font(f0['font']) != _font(g['font']):
                notes.append(f'FONT {_font(f0["font"])} -> {_font(g["font"])}'); sev = 'high'
            if abs(g['size'] - f0['size']) > 0.15:
                notes.append(f'size {f0["size"]:.2f} -> {g["size"]:.2f}pt'); sev = 'high'
            if g['color'] != f0['color']:
                notes.append(f'colour #{f0["color"]:06x} -> #{g["color"]:06x}')
            wr, wc = cs[-1]['x'] - f0['x'], gl['x'] - g['x']
            # short words: Canva ignores kerning pairs (e.g. 'Yo'), so judge by absolute width, not ratio alone
            if wr > 5 and abs(wc / wr - 1) > 0.03 and abs(wc - wr) > tol:
                notes.append(f'width x{wc / wr:.3f}'); sev = 'high' if sev != 'high' and abs(wc / wr - 1) > 0.06 else sev
            if notes:
                bad.append((sev, f'{"; ".join(notes)}  "{label}" ({_font(f0["font"])} {f0["size"]:.1f}pt) @x{f0["x"]:.0f} y{f0["y"]:.0f}'))
        # pixels
        diff = side_by_side(ref[pi], cv[pi], os.path.join(out_dir, f'compare-p{pi + 1:02d}.jpg'))
        hi = sum(1 for s, _ in bad if s == 'high')
        fails += hi
        rep.append(f'## Page {pi + 1}: {len(bad)} issues ({hi} high) · pixel diff {diff:.2f}%')
        rep += [f'- [{s}] {t}' for s, t in sorted(bad, key=lambda x: ('high', 'medium', 'low').index(x[0]))]
        rep.append('')
    # an unnamed Type3 font is Canva's fallback for a glyph its copy of the font lacks (e.g. a ◆ the font has no glyph for)
    fname = lambda f, pi: _font(f[3]) or f'type3-unnamed (page {pi + 1})'
    fonts_ref = {fname(f, pi) for pi, p in enumerate(ref) for f in p.get_fonts()}
    fonts_cv = {fname(f, pi) for pi, p in enumerate(cv) for f in p.get_fonts()}
    extra = sorted(fonts_cv - fonts_ref)
    fails += len(extra)
    head = [f'# Canva audit: {cfg.name}', '', f'Reference: `build/reference.pdf` · Canva export: `{canva_pdf}` · tolerance {tol} mm', '',
            f'**Result: {"PASS" if not fails else f"FAIL ({fails} high-severity)"}**', '']
    if extra:
        head += [f'**Fonts in the Canva export that the reference does not use (substitution; add the glyphs to bake_glyphs):** {", ".join(extra)}', '']
    tail = ['## Vertical offset by font/size (median dy mm, n)', ''] + \
           [f'- {k[0]} {k[1]}pt: {st.median(v):+.2f} (n={len(v)})' for k, v in sorted(stats.items()) if v]
    text = '\n'.join(head + rep + tail)
    open(os.path.join(out_dir, 'audit-report.md'), 'w').write(text)
    return fails, text


def side_by_side(rp, cp, out, dpi=60):
    import pymupdf as fitz
    from PIL import Image, ImageChops, ImageDraw
    def img(p):
        z = dpi / 72
        pm = p.get_pixmap(matrix=fitz.Matrix(z, z))
        return Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
    a = img(rp)
    b = img(cp).resize(a.size, Image.LANCZOS)
    d = ImageChops.difference(a, b).convert('L')
    pct = sum(1 for v in d.getdata() if v > 40) / (a.width * a.height) * 100
    hl = Image.new('RGB', a.size, 'white'); hl.paste((220, 30, 30), mask=d.point(lambda v: 255 if v > 40 else 0))
    sheet = Image.new('RGB', (a.width * 3 + 40, a.height + 30), 'white')
    for i, (im, t) in enumerate(((a, 'HTML reference'), (b, 'Canva export'), (Image.blend(a, hl, 0.6), 'differences'))):
        sheet.paste(im, (i * (a.width + 20), 30)); ImageDraw.Draw(sheet).text((i * (a.width + 20) + 4, 8), t, fill='black')
    sheet.save(out, quality=85)
    return pct


def _pitch_error(bx, keep, big, idx, dy0, min_lines=3):
    """Canva line pitch minus intended pitch (mm per line) for a multi-line box, or 0.0."""
    ls = bx['text'].split('\n')
    if len(ls) < min_lines:
        return 0.0
    LH = float(bx['sig'].split('|')[-1])
    pts = [(0, dy0)]
    for i in range(1, len(ls)):
        t = cvlib.norm_text(ls[i])[:12]
        if len(t) < 6:
            continue
        exp_y = bx['base'] + i * LH
        occ = [m.start() for m in re.finditer(re.escape(t), big)]
        occ = [o for o in occ if abs(keep[idx[o]]['y'] - exp_y) < 4]
        if not occ:
            continue
        o = min(occ, key=lambda o: abs(keep[idx[o]]['y'] - exp_y - dy0))
        pts.append((i, keep[idx[o]]['y'] - exp_y))
    if len(pts) < min_lines:
        return 0.0
    n = len(pts); mx = sum(p[0] for p in pts) / n; my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    slope = sum((p[0] - mx) * (p[1] - my) for p in pts) / sxx if sxx else 0.0
    return slope if abs(slope * (len(ls) - 1)) > 0.15 else 0.0


def calibrate(cfg, canva_pdf):
    import pymupdf as fitz
    B = json.load(open(os.path.join(cfg.build, 'boxes.json')))
    calp = os.path.join(cfg.dir, 'calib.json')
    CAL = json.load(open(calp)) if os.path.exists(calp) else {}
    cv = fitz.open(canva_pdf)
    pages = {}
    for pi, pg in enumerate(cv):
        keep, big, idx = _flat(chars(pg, cfg.page_w / (pg.rect.width / MM)))
        pages[pi + 1] = (keep, big, idx)
    errs, miss, pitch = [], [], []
    for bx in B:
        if bx['page'] not in pages:
            continue
        keep, big, idx = pages[bx['page']]
        t = bx['key'][:12]
        if not t:
            continue
        occ = [m.start() for m in re.finditer(re.escape(t), big)]
        if not occ:
            miss.append(f"{bx['id']} {t}"); continue
        o = min(occ, key=lambda o: (keep[idx[o]]['x'] - bx['x']) ** 2 + (keep[idx[o]]['y'] - bx['base']) ** 2)
        dx, dy = keep[idx[o]]['x'] - bx['x'], keep[idx[o]]['y'] - bx['base']
        if abs(dx) > 15 or abs(dy) > 15:
            miss.append(f"{bx['id']} far {t}"); continue
        errs.append((abs(dx) + abs(dy), bx['id'], t, dx, dy))
        # accumulate onto the offset this build actually applied (seed/style/measured), not onto 0:
        # a seed-calibrated box measured for the first time would otherwise lose its seed offset
        c = list(bx.get('off') or CAL.get(bx['id'], [0.0, 0.0]))
        c += [0.0] * (3 - len(c))
        # line pitch: Canva's line spacing for a long box can differ from the PPTX value by ~1-2 %,
        # which a box offset can't fix (the error grows down the box). Fit dy against line index.
        dp = _pitch_error(bx, keep, big, idx, dy)
        CAL[bx['id']] = [c[0] + dx, c[1] + dy] + ([c[2] + dp] if (dp or c[2]) else [])
        if dp:
            pitch.append((abs(dp), bx['id'], dp))
    json.dump(CAL, open(calp, 'w'), indent=0)
    if not errs:
        return f'no boxes measured; missing {len(miss)}'
    q = lambda v: sorted(v)[int(len(v) * .95)]
    ady, adx = [abs(e[4]) for e in errs], [abs(e[3]) for e in errs]
    lines = [f'boxes {len(B)} measured {len(errs)} missing {len(miss)}',
             f'|dy| median {st.median(ady):.2f}  p95 {q(ady):.2f}  max {max(ady):.2f} mm',
             f'|dx| median {st.median(adx):.2f}  p95 {q(adx):.2f}  max {max(adx):.2f} mm']
    lines += [f'  worst {e[1]} {e[2]!r} dx {e[3]:+.2f} dy {e[4]:+.2f}' for e in sorted(errs, reverse=True)[:8]]
    if pitch:
        lines.append(f'line pitch corrected on {len(pitch)} boxes; worst ' + ', '.join(f'{p[1]} {p[2]:+.3f} mm/line' for p in sorted(pitch, reverse=True)[:4]))
    if miss:
        lines.append('  not found: ' + '; '.join(miss[:12]))
    return '\n'.join(lines)
