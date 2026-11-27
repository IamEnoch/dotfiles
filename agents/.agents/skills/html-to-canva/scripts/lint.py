"""Canva-safety lint: everything that would break or drift in Canva, caught while still in HTML."""
import json, os, re
import cvlib

SAFE = set(range(0x20, 0x7F)) | set(range(0xA0, 0x180)) | set(range(0x2010, 0x2040)) | {0x2122, 0x20AC, 0xFB01, 0xFB02}


def rgba_alpha(c):
    m = re.match(r'rgba?\(([^)]*)\)', c or '')
    if not m:
        return 1.0
    v = [x.strip() for x in m.group(1).replace('/', ',').split(',')]
    return float(v[3]) if len(v) > 3 else 1.0


def run(cfg, write=True):
    os.makedirs(cfg.build, exist_ok=True)
    src = open(cfg.html, encoding='utf-8').read()
    src = cvlib.static_font_html(cfg, src)
    src = cvlib.inject_body_end(src, f'<script>window.__CV={json.dumps({"page": cfg.page_sel, "live": cfg.live_images})};</script>'
                                     f'<script src="file://{cvlib.HERE}/inspect.js"></script>')
    probe = cvlib.write_beside_master(cfg, 'inspect', src)
    try:
        d = cvlib.dump_attr(probe, 'inspect')
    finally:
        os.remove(probe)

    errors, warns, infos = [], [], []
    E = lambda m: errors.append(m)
    W = lambda m: warns.append(m)
    I = lambda m: infos.append(m)

    # pages
    n = len(d['pages'])
    if not n:
        E(f'No pages match selector `{cfg.page_sel}`.')
    for i, p in enumerate(d['pages']):
        if abs(p['w'] - cfg.page_w) > 0.5 or abs(p['h'] - cfg.page_h) > 0.5:
            E(f'Page {i + 1} is {p["w"]:.1f} x {p["h"]:.1f} mm, config says {cfg.page_w} x {cfg.page_h} mm.')

    # fonts
    faces_used = {}
    for t in d['text']:
        faces_used.setdefault((t['family'], t['weight'], t['italic']), []).append(t)
    for (fam, w, it), items in sorted(faces_used.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        ex = items[0]
        where = f'p{ex["page"]} {ex["el"]} "{ex["text"][:40]}"' + (f' (+{len(items) - 1} more)' if len(items) > 1 else '')
        label = f'{fam} {w}{" italic" if it else ""}'
        if fam not in cfg.fonts:
            E(f'Font family `{fam}` is not in canva.json fonts, so it has no Canva name. {where}')
            continue
        canva_fam = cfg.fonts[fam].get('canva', fam)
        blocked = cfg.fonts[fam].get('blocked_weights', cfg.blocked_weights)
        if w in blocked:
            E(f'{label}: weight {w} does not survive Canva import for {canva_fam} (it falls back). Use another weight in the HTML. {where}')
        path = cfg.face_file(fam, w, it)
        if not path:
            E(f'{label}: no static face file in canva.json (key "{w}{"i" if it else ""}"). Chrome would synthesise it; Canva will not. {where}')
            continue
        if not os.path.exists(path):
            E(f'{label}: face file missing: {path}')
            continue
        m = cvlib.font_metrics(path)
        if m['variable']:
            E(f'{label}: {os.path.basename(path)} is a variable font; Canva drops variable fonts. Use a static instance.')
        if it and not m['italic_bit']:
            W(f'{label}: {os.path.basename(path)} is not flagged italic in its tables; Canva may drop the italic.')
        chars = set(''.join(x['chars'] for x in items))
        miss = sorted(c for c in chars if ord(c) not in m['cmap'] and c not in cfg.bake_glyphs and not c.isspace())
        if miss:
            E(f'{label}: glyphs missing from the font: {" ".join(miss)} - Canva substitutes another font (seen: Noto Sans). Bake them or change the character. {where}')
        risky = sorted(c for c in chars if ord(c) not in SAFE and c not in cfg.bake_glyphs and not c.isspace())
        if risky:
            W(f'{label}: uncommon glyphs {" ".join(risky)} - Canva\'s copy of {canva_fam} may lack them; check after import or add to bake_glyphs.')

    # text treatments that cannot stay live
    for t in d['text']:
        where = f'p{t["page"]} {t["el"]} "{t["text"][:40]}"'
        if t['clip']:
            E(f'Gradient/clipped text (background-clip:text) becomes flat colour in Canva. {where}')
        if t['writing'] not in ('horizontal-tb', ''):
            E(f'Vertical writing-mode is not supported. {where}')
        if t['transform'] not in ('none', '') and not re.match(r'matrix\(1, 0, 0, 1,', t['transform']):
            W(f'Rotated/skewed/scaled text is placed unrotated. {where}')
        if rgba_alpha(t['color']) < 1 or t['opacity'] < 1:
            W(f'Semi-transparent text: transparency is dropped; mix the colour against its background instead. {where}')
        if t['blend'] != 'normal':
            W(f'mix-blend-mode on text is dropped. {where}')
        if t['variation'] not in ('normal', ''):
            W(f'font-variation-settings on text is ignored by Canva. {where}')
        if t['features'] not in ('normal', ''):
            I(f'font-feature-settings ({t["features"]}) may not carry over. {where}')
        if t['shadow']:
            I(f'Text shadow will be baked into the page background (it will not follow the text if moved in Canva). {where}')

    # images
    for im in d['images']:
        if not im['ok']:
            E(f'Image failed to load: p{im["page"]} {im["el"]} {im["src"]}')
        elif im['live']:
            ppi = im['nw'] / (im['w'] / 25.4) if im['w'] else 0
            if ppi < 200:
                W(f'Live photo p{im["page"]} {im["el"]} is {ppi:.0f} ppi at print size (aim for 300).')
    if cfg.live_images and not d.get('liveMatched'):
        W('live_images selectors match nothing; every photo will be baked into the background.')
    baked = [im for im in d['images'] if not im['live']]
    I(f'{len(d["text"])} text elements, {d["tagged"]} under data-cv ids, {d["untagged"]} with path ids.')
    I(f'{len([i for i in d["images"] if i["live"]])} live photos (swappable in Canva); {len(baked)} <img> + {d["bgimages"]} CSS backgrounds baked.')
    if d['effects']:
        I('Baked into the background image (fine, but not editable in Canva): ' + ', '.join(f'{k} x{v}' for k, v in sorted(d['effects'].items())))
    I('Fractional font sizes import fine via PPTX; later connector edits accept whole numbers only.')

    rep = [f'# Canva lint: {cfg.name}', '', f'Master: `{cfg.html}`  |  pages: {n}', '',
           f'**{len(errors)} errors, {len(warns)} warnings**', '']
    for title, items in (('Errors (fix before import)', errors), ('Warnings', warns), ('Notes', infos)):
        if items:
            rep += [f'## {title}', ''] + [f'- {x}' for x in dict.fromkeys(items)] + ['']
    text = '\n'.join(rep)
    if write:
        open(os.path.join(cfg.build, 'lint-report.md'), 'w').write(text)
    return errors, warns, infos, text
