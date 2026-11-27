"""Compile the HTML master into a Canva-importable PPTX.

Per page: one 300 dpi baked background (everything except live text and live photos),
live photos as separate pictures, and one explicit text box per block/line with exact
line breaks, line pitch, letter-spacing and the exact Canva font face name.

Outputs in <work>/build/:
  reference.pdf        static-font print of the master (the layout authority for audits)
  bg/pN.jpg            baked backgrounds          img/pN_k.png  rendered live photos
  extract.json         raw geometry from the browser
  boxes.json           the manifest: one entry per PPTX text box (ids, text, mm geometry, style)
  images.json          the live photos with ids and hashes
  <name>.pptx          import this into Canva
"""
import json, os, re, shutil, statistics, subprocess
import cvlib
from cvlib import PX2MM

SEED = json.load(open(os.path.join(cvlib.HERE, '..', 'data', 'calibration-seed.json')))


# ---------------------------------------------------------------- html stages
def print_page(cfg):
    src = open(cfg.html, encoding='utf-8').read()
    # Canva output is the print version: apply the master's print-only rules (e.g. draft flags hidden
    # with @media print) to extraction and baking too, and drop screen-only rules.
    src = re.sub(r'@media\s+print\b', '@media all', src)
    src = re.sub(r'@media\s+screen\b', '@media not all', src)
    src = cvlib.static_font_html(cfg, src)
    W, H = cfg.page_w, cfg.page_h
    src = cvlib.inject_head(src, f'<style id="cv-print">@page {{ size:{W}mm {H}mm; margin:0; }} @media print {{ html,body {{ margin:0 !important; padding:0 !important; background:none !important; }} {cfg.page_sel} {{ margin:0 !important; box-shadow:none !important; break-after:page; page-break-after:always; }} }}</style>')
    src = cvlib.inject_head(src, cvlib.isolate_script(cfg))
    return src


def bake_backgrounds(cfg, src, n_pages):
    live = json.dumps(', '.join(cfg.live_images))
    sel = cfg.page_sel
    css = f'''<style id="cv-bake">
/* hide only glyph paint: 'color' stays, so currentColor borders, rules and icons still bake */
{sel}, {sel} *, {sel} *::before, {sel} *::after, {sel} *::first-letter {{ -webkit-text-fill-color:transparent !important; text-decoration-color:transparent !important; }}
{sel} *::marker {{ color:transparent !important; }}
{cfg.bake_css}
</style>'''
    # live photos: bake only their drop-shadow, never the pixels (they go in as separate pictures)
    js = '''<script>document.addEventListener('DOMContentLoaded',()=>{const L=%s;if(!L)return;
const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.setAttribute('width','0');svg.setAttribute('height','0');svg.style.position='absolute';document.body.appendChild(svg);
document.querySelectorAll(L).forEach((e,i)=>{const f=getComputedStyle(e).filter;
const m=f&&f.match(/drop-shadow\\((rgba?\\(([^)]*)\\))\\s+(-?[\\d.]+)px\\s+(-?[\\d.]+)px\\s+([\\d.]+)px\\)/);
if(!m){e.style.setProperty('object-position','-99999px -99999px','important');return;}
const c=m[2].split(',').map(x=>parseFloat(x));const a=c.length>3?c[3]:1;const fl=document.createElementNS(ns,'filter');fl.id='cvsh'+i;
for(const [k,v] of [['x','-60%%'],['y','-60%%'],['width','220%%'],['height','220%%'],['color-interpolation-filters','sRGB']])fl.setAttribute(k,v);
fl.innerHTML=`<feGaussianBlur in="SourceAlpha" stdDeviation="${parseFloat(m[5])/2}"/><feOffset dx="${m[3]}" dy="${m[4]}" result="o"/><feFlood flood-color="rgb(${c[0]},${c[1]},${c[2]})" flood-opacity="${a}"/><feComposite in2="o" operator="in"/>`;
svg.appendChild(fl);e.style.setProperty('filter',`url(#cvsh${i})`,'important');});});</script>''' % live
    page = cvlib.write_beside_master(cfg, 'bake', cvlib.inject_head(src, css + js))
    bgdir = os.path.join(cfg.build, 'bg'); os.makedirs(bgdir, exist_ok=True)
    try:
        procs = []
        for i in range(1, n_pages + 1):
            procs.append(cvlib.screenshot(cfg, page, os.path.join(bgdir, f'p{i}.png'), i))
            if len(procs) >= 6:
                [p.wait() for p in procs]; procs = []
        [p.wait() for p in procs]
    finally:
        os.remove(page)
    from PIL import Image
    W, H = round(cfg.page_w / 25.4 * 300), round(cfg.page_h / 25.4 * 300)
    for i in range(1, n_pages + 1):
        png = os.path.join(bgdir, f'p{i}.png')
        im = Image.open(png).convert('RGB')
        if im.size != (W, H):
            im = im.resize((W, H), Image.LANCZOS)
        im.save(os.path.join(bgdir, f'p{i}.jpg'), quality=93, dpi=(300, 300))
        os.remove(png)


def extract(cfg, src):
    cv = json.dumps({'page': cfg.page_sel, 'live': cfg.live_images})
    src = cvlib.inject_body_end(src, f'<script>window.__CV={cv};</script><script src="file://{cvlib.HERE}/extract.js"></script>')
    page = cvlib.write_beside_master(cfg, 'extract', src)
    try:
        return cvlib.dump_attr(page, 'extract', budget=20000)
    finally:
        os.remove(page)


# ---------------------------------------------------------------- pptx
def render_photo(img, out):
    """The photo exactly as displayed (object-fit, object-position, border-radius), ~300 dpi."""
    from PIL import Image, ImageDraw
    src = Image.open(img['src']).convert('RGBA')
    rad0 = img.get('radius') or '0px'
    if img['fit'] not in ('cover', 'contain') and rad0 in ('0px', '0%'):
        # nothing to crop or mask: hand Canva the original pixels, never a resample (people photos stay HD)
        src.save(out)
        return
    scale = 12
    tw, th = max(1, round(img['w'] * scale)), max(1, round(img['h'] * scale))
    if img['fit'] == 'cover':
        s = max(tw / src.width, th / src.height)
        rw, rh = round(src.width * s), round(src.height * s)
        r = src.resize((rw, rh), Image.LANCZOS)
        pos = (img['pos'].split() + ['50%'])[:2]
        px, py = [float(v.strip('%')) / 100 if v.endswith('%') else 0.5 for v in pos]
        ox, oy = round((rw - tw) * px), round((rh - th) * py)
        o = r.crop((ox, oy, ox + tw, oy + th))
    elif img['fit'] == 'contain':
        s = min(tw / src.width, th / src.height)
        r = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
        o = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); o.paste(r, ((tw - r.width) // 2, (th - r.height) // 2))
    else:
        o = src.resize((tw, th), Image.LANCZOS)
    rad = img.get('radius') or '0px'
    if rad not in ('0px', '0%'):
        m = Image.new('L', (tw, th), 0); d = ImageDraw.Draw(m)
        if rad.endswith('%'):
            d.ellipse((0, 0, tw - 1, th - 1), fill=255)
        else:
            d.rounded_rectangle((0, 0, tw - 1, th - 1), radius=float(rad.split('px')[0]) * PX2MM * scale, fill=255)
        a = o.getchannel('A'); o.putalpha(Image.composite(a, Image.new('L', (tw, th), 0), m))
    o.save(out)


def runinfo(r):
    fam, w, st, px, color, ls, tt, op = r['key'].split('|')
    return fam, int(float(w)), st == 'italic', float(px), color, float(ls), float(op)


def build_pptx(cfg, D):
    from pptx import Presentation
    from pptx.util import Emu, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE, MSO_ANCHOR
    from pptx.oxml.ns import qn
    mm = lambda v: Emu(int(round(v * 36000)))
    calp = os.path.join(cfg.dir, 'calib.json')
    CAL = json.load(open(calp)) if os.path.exists(calp) else {}
    # per-signature medians from earlier measured boxes (fallback for boxes never measured)
    SIG = {}
    old = os.path.join(cfg.build, 'boxes.json')
    if CAL and os.path.exists(old):
        acc = {}
        for b in json.load(open(old)):
            if b['id'] in CAL:
                acc.setdefault(b['sig'], []).append(CAL[b['id']])
        SIG = {k: (statistics.median(v[0] for v in vs), statistics.median(v[1] for v in vs),
                   statistics.median((v[2] if len(v) > 2 else 0.0) for v in vs)) for k, vs in acc.items()}

    def face(fam, w, it):
        p = cfg.nearest_face(fam, w, it)
        return cvlib.font_metrics(p) if p else dict(asc=0.9, desc=0.25, space=0.25)

    def rgb(s):
        return RGBColor(*[int(float(x)) for x in re.findall(r'[\d.]+', s)[:3]])

    prs = Presentation()
    prs.slide_width, prs.slide_height = mm(cfg.page_w), mm(cfg.page_h)
    blank = prs.slide_layouts[6]
    imgdir = os.path.join(cfg.build, 'img'); os.makedirs(imgdir, exist_ok=True)
    split_keys = {cvlib.norm_text(k)[:20] for k in cfg.split_lines}
    bake = set(cfg.bake_glyphs)
    BOXES, IMAGES, seen_ids = [], [], {}

    for pi, page in enumerate(D['pages']):
        sl = prs.slides.add_slide(blank)
        sl.shapes.add_picture(os.path.join(cfg.build, 'bg', f'p{pi + 1}.jpg'), 0, 0, mm(cfg.page_w), mm(cfg.page_h))
        for k, im in enumerate(page['images']):
            fn = os.path.join(imgdir, f'p{pi + 1}_{k}.png')
            render_photo(im, fn)
            sl.shapes.add_picture(fn, mm(im['x']), mm(im['y']), mm(im['w']), mm(im['h']))
            IMAGES.append(dict(id=im.get('id') or f'p{pi + 1}/img{k}', page=pi + 1, src=im['src'], src_sha=cvlib.sha(im['src']),
                               render=os.path.relpath(fn, cfg.dir), render_sha=cvlib.sha(fn),
                               x=im['x'], y=im['y'], w=im['w'], h=im['h']))

        # 1. a left-aligned block whose lines start at different x (floats, hanging) -> one group per x
        groups = []
        for b in page['blocks']:
            if b['align'] in ('center', '-webkit-center', 'right', 'end') or len(b['lines']) < 2:
                groups.append(b); continue
            cur = None
            for ln in b['lines']:
                if cur is None or abs(ln['left'] - cur['lines'][-1]['left']) > 0.3:
                    cur = dict(b, lines=[], id=b['id'] + ('' if cur is None else f'#g{len([g for g in groups if g["id"].startswith(b["id"])]) + 1}'))
                    groups.append(cur)
                cur['lines'].append(ln)
        # 2. mixed-size blocks (and configured ones) -> one box per line: Canva re-spaces mixed leading
        split = []
        for b in groups:
            sizes = {r['key'].split('|')[3] for ln in b['lines'] for r in ln['runs'] if r['text'].strip()}
            first = cvlib.norm_text(''.join(r['text'] for r in b['lines'][0]['runs']))[:20]
            if len(b['lines']) > 1 and (len(sizes) > 1 or first in split_keys):
                split += [dict(b, lines=[ln], id=f"{b['id']}#L{k + 1}") for k, ln in enumerate(b['lines'])]
            else:
                split.append(b)

        # 3. a line whose runs have a real gap (margin/padding/tab stops) or change family/style/size -> one box per segment
        def segments(ln):
            segs = [[ln['runs'][0]]]
            last = ln['runs'][0] if ln['runs'][0]['text'].strip() else None
            for i in range(1, len(ln['runs'])):
                c = ln['runs'][i]
                if not c['text'].strip():
                    segs[-1].append(c); continue
                a = last if last is not None else ln['runs'][i - 1]
                last = c
                ex = 0.0
                if a.get('right') is not None and c.get('x') is not None:
                    fa, wa, ia, pxa, _, lsa, _ = runinfo(a)
                    nsp = (len(a['text']) - len(a['text'].rstrip())) + (len(c['text']) - len(c['text'].lstrip()))
                    natural = nsp * (face(fa, wa, ia)['space'] * pxa + lsa) * PX2MM
                    ex = (c['x'] - a['right']) - natural
                ka, kc = a['key'].split('|'), c['key'].split('|')
                style_change = ka[0] != kc[0] or ka[2] != kc[2] or abs(float(ka[3]) - float(kc[3])) > 0.01
                if abs(ex) > 0.3 or style_change: segs.append([c])
                else: segs[-1].append(c)
            return segs
        boxes = []
        for b in split:
            segd = [segments(ln) for ln in b['lines']]
            if any(len(sg) > 1 for sg in segd):
                for li, (ln, sg) in enumerate(zip(b['lines'], segd)):
                    for si, runs in enumerate(sg):
                        runs = [dict(r, text=(r['text'].lstrip() if k == 0 else r['text'])) for k, r in enumerate(runs)]
                        runs[-1] = dict(runs[-1], text=runs[-1]['text'].rstrip())
                        xs = [r['x'] for r in runs if r.get('x') is not None]; rs = [r['right'] for r in runs if r.get('right') is not None]
                        if not xs: continue
                        if bake and set(''.join(r['text'] for r in runs).strip()) <= bake: continue
                        suffix = (f'#L{li + 1}' if len(b['lines']) > 1 else '') + f'#S{si + 1}'
                        boxes.append(dict(b, align='left', id=b['id'] + suffix, lines=[dict(ln, left=min(xs), right=max(rs), runs=runs)]))
            else:
                if bake and set(''.join(r['text'] for ln in b['lines'] for r in ln['runs']).strip()) <= bake: continue
                boxes.append(b)

        for b in boxes:
            bid = b['id']
            if bid in seen_ids:
                seen_ids[bid] += 1; bid = f'{bid}~{seen_ids[bid]}'
            else:
                seen_ids[bid] = 1
            lines = b['lines']
            lh_px = float(b['lh'].replace('px', '')) if b['lh'].endswith('px') else None
            first = max(lines[0]['runs'], key=lambda r: float(r['key'].split('|')[3]))
            fam, w, it, px, *_ = runinfo(first)
            m = face(fam, w, it)
            S = px * PX2MM
            base1 = first['bottom'] - m['desc'] * S
            if len(lines) > 1:
                bases = []
                for ln in lines:
                    r0 = max(ln['runs'], key=lambda r: float(r['key'].split('|')[3]))
                    f0, w0, i0, p0, *_ = runinfo(r0)
                    bases.append(r0['bottom'] - face(f0, w0, i0)['desc'] * p0 * PX2MM)
                LH = sorted(bases[i + 1] - bases[i] for i in range(len(bases) - 1))[(len(bases) - 1) // 2]
            else:
                LH = (lh_px * PX2MM) if lh_px else (m['asc'] + m['desc']) * S * 1.2
                LH = max(LH, (m['asc'] + m['desc']) * S)
            sig = f'{fam}|{w}|{"italic" if it else "normal"}|{px:.2f}|{LH:.3f}'
            cname, cbold = cfg.canva_font(fam, w, it)
            cdp = 0.0
            if bid in CAL:
                cdx, cdy, *rest = CAL[bid]; csrc = 'measured'; cdp = rest[0] if rest else 0.0
            elif sig in SIG:
                cdx, cdy, cdp = SIG[sig]; csrc = 'style'
            else:
                k = f'{cname}|{"bold" if cbold else "regular"}|{"italic" if it else "normal"}'
                cdx, cdy = 0.0, SEED.get(k, SEED.get('*', 0.0)) * S; csrc = 'seed'
            if len(lines) < 3:
                cdp = 0.0
            LHset = LH - cdp          # line spacing written to the PPTX (corrected for Canva's pitch error)
            # CSS half-leading: Canva (a web renderer) lays out a line of height LH the same way
            top = base1 - m['asc'] * S - (LHset - (m['asc'] + m['desc']) * S) / 2
            top -= cdy
            left = min(l['left'] for l in lines); right = max(l['right'] for l in lines)
            cx = sum((l['left'] + l['right']) / 2 for l in lines) / len(lines)
            slack = 4.0
            width = right - left + slack
            if b['align'] in ('center', '-webkit-center'):
                x = cx - width / 2; al = PP_ALIGN.CENTER
            elif b['align'] in ('right', 'end'):
                x = right - width; al = PP_ALIGN.RIGHT
            else:
                x = left; al = PP_ALIGN.LEFT
            x -= cdx
            height = LHset * len(lines)
            tb = sl.shapes.add_textbox(mm(x), mm(top), mm(width), mm(height))
            tb.name = bid[:200]
            tf = tb.text_frame
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            tf.word_wrap = False
            tf.auto_size = MSO_AUTO_SIZE.NONE
            tf.vertical_anchor = MSO_ANCHOR.TOP
            p = tf.paragraphs[0]
            p.alignment = al
            p.line_spacing = Pt(LHset / 25.4 * 72)
            p.space_before = p.space_after = Pt(0)
            styles = set()
            for li, ln in enumerate(lines):
                if li:
                    p.add_line_break()
                for r in ln['runs']:
                    if not r['text']:
                        continue
                    fam_r, w_r, it_r, px_r, color, ls, op = runinfo(r)
                    name, bold = cfg.canva_font(fam_r, w_r, it_r)
                    run = p.add_run(); run.text = r['text']
                    f = run.font
                    f.name = name; f.bold = bold; f.italic = it_r
                    f.size = Pt(round(px_r * 0.75, 2))
                    f.color.rgb = rgb(color)
                    styles.add((name, bold, it_r, round(px_r * 0.75, 2), str(f.color.rgb), round(ls, 3)))
                    rPr = run._r.get_or_add_rPr()
                    spc = ls * 0.75
                    if abs(spc) > 0.005:
                        rPr.set('spc', str(int(round(spc * 100))))
                    for tag in ('a:latin', 'a:cs'):
                        el = rPr.find(qn(tag))
                        if el is None:
                            el = rPr.makeelement(qn(tag), {}); rPr.append(el)
                        el.set('typeface', name)
            fr = lines[0]['runs'][0]
            text = '\n'.join(''.join(r['text'] for r in ln['runs']) for ln in lines)
            st0 = sorted(styles)[0] if styles else None
            BOXES.append(dict(id=bid, page=pi + 1, text=text, key=cvlib.norm_text(text)[:30], sig=sig, align=b['align'],
                              x=fr['x'] if fr.get('x') is not None else left, base=base1,
                              box=dict(left=round(x, 3), top=round(top, 3), width=round(width, 3), height=round(height, 3)),
                              style=dict(font=st0[0], bold=st0[1], italic=st0[2], pt=st0[3], color=st0[4], spacing=st0[5]) if st0 else None,
                              mixed=len(styles) > 1, lines=len(lines), calib=csrc,
                              off=[round(cdx, 4), round(cdy, 4)] + ([round(cdp, 4)] if cdp else [])))
    out = os.path.join(cfg.build, f'{cfg.name}.pptx')
    prs.save(out)
    json.dump(BOXES, open(os.path.join(cfg.build, 'boxes.json'), 'w'), indent=0, ensure_ascii=False)
    json.dump(IMAGES, open(os.path.join(cfg.build, 'images.json'), 'w'), indent=0)
    return out, BOXES, IMAGES


def run(cfg, skip_bg=False):
    os.makedirs(cfg.build, exist_ok=True)
    src = print_page(cfg)
    pp = cvlib.write_beside_master(cfg, 'print', src)
    try:
        cvlib.print_pdf(pp, os.path.join(cfg.build, 'reference.pdf'))
    finally:
        os.remove(pp)
    D = extract(cfg, src)
    json.dump(D, open(os.path.join(cfg.build, 'extract.json'), 'w'))
    n = len(D['pages'])
    if not skip_bg or not os.path.exists(os.path.join(cfg.build, 'bg', 'p1.jpg')):
        bake_backgrounds(cfg, src, n)
    out, boxes, images = build_pptx(cfg, D)
    bg = {f'p{i}': cvlib.sha(os.path.join(cfg.build, 'bg', f'p{i}.jpg')) for i in range(1, n + 1)}
    json.dump(dict(pages=n, page_mm=[cfg.page_w, cfg.page_h], bg=bg, master=cfg.html, master_sha=cvlib.sha(cfg.html)),
              open(os.path.join(cfg.build, 'state.json'), 'w'), indent=1)
    calib = {k: sum(1 for b in boxes if b['calib'] == k) for k in ('measured', 'style', 'seed')}
    return out, n, len(boxes), len(images), calib
