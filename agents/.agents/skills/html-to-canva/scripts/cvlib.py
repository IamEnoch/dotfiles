"""Shared helpers for the html-to-canva pipeline: config, Chromium, fonts, files."""
import glob, hashlib, html as htmlmod, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PX2MM = 25.4 / 96          # CSS px -> mm
MM_PER_PT = 25.4 / 72


# ---------------------------------------------------------------- config
class Config:
    """canva.json lives in the work dir; every relative path in it is relative to that dir."""

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.dir = os.path.dirname(self.path)
        self.raw = json.load(open(self.path))
        r = self.raw
        self.name = r.get('name', 'design')
        self.html = self.abs(r['html'])
        pg = r.get('page', {})
        self.page_sel = pg.get('selector', 'section.page')
        self.page_w = float(pg.get('width_mm', 210))
        self.page_h = float(pg.get('height_mm', 297))
        self.fonts = r.get('fonts', {})
        self.live_images = r.get('live_images', [])
        self.bake_css = r.get('bake_css', '')
        self.bake_glyphs = r.get('bake_glyphs', [])
        self.split_lines = r.get('split_lines', [])
        self.blocked_weights = r.get('blocked_weights', [600])
        self.canva = r.get('canva', {})
        self.build = os.path.join(self.dir, 'build')
        self.synced = os.path.join(self.dir, 'synced')

    def abs(self, p):
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(self.dir, p))

    def save(self):
        json.dump(self.raw, open(self.path, 'w'), indent=2)

    # font faces: key "400", "400i", "700" ...
    def face_file(self, alias, weight, italic):
        f = self.fonts.get(alias)
        if not f:
            return None
        k = f"{int(weight)}{'i' if italic else ''}"
        p = f.get('faces', {}).get(k)
        return self.abs(p) if p else None

    def nearest_face(self, alias, weight, italic):
        """Exact face, else the nearest weight of the same style (for metrics only)."""
        p = self.face_file(alias, weight, italic)
        if p:
            return p
        faces = self.fonts.get(alias, {}).get('faces', {})
        cands = [(abs(int(re.sub(r'\D', '', k)) - int(weight)), v) for k, v in faces.items() if k.endswith('i') == bool(italic)]
        cands = cands or [(abs(int(re.sub(r'\D', '', k)) - int(weight)), v) for k, v in faces.items()]
        return self.abs(min(cands)[1]) if cands else None

    def canva_font(self, alias, weight, italic):
        """Name + bold flag exactly as Canva lists the face. Canva lists each weight as its own
        family ("Montserrat Medium"); Regular is the plain name; Bold is the plain name + bold flag."""
        f = self.fonts.get(alias, {})
        fam = f.get('canva', alias)
        if f.get('single_face'):
            return fam, False
        w = int(weight)
        names = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: '', 500: 'Medium', 600: 'SemiBold', 700: '', 800: 'ExtraBold', 900: 'Black'}
        names.update({int(k): v for k, v in f.get('weight_names', {}).items()})
        if w == 700:
            return fam, True
        n = names.get(w, '')
        return (f'{fam} {n}' if n else fam), False


def load_config(path=None):
    path = path or os.environ.get('CANVA_CONFIG') or 'canva.json'
    if os.path.isdir(path):
        path = os.path.join(path, 'canva.json')
    if not os.path.exists(path):
        sys.exit(f'config not found: {path}  (run: cv.py init <master.html> <workdir>)')
    return Config(path)


# ---------------------------------------------------------------- chromium
def chrome():
    env = os.environ.get('CHROME')
    if env and os.path.exists(env):
        return env
    pats = [os.path.expanduser('~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome'),
            os.path.expanduser('~/.cache/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium')]
    for p in pats:
        hits = sorted(glob.glob(p))
        if hits:
            return hits[-1]
    for n in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable'):
        if shutil.which(n):
            return shutil.which(n)
    sys.exit('No Chromium found. Set CHROME=/path/to/chrome or install playwright chromium.')


BASE_FLAGS = ['--headless=new', '--no-sandbox', '--hide-scrollbars', '--disable-gpu', '--allow-file-access-from-files']


def page_px(cfg):
    return round(cfg.page_w / PX2MM), round(cfg.page_h / PX2MM)


def screenshot(cfg, html_path, out_png, page_no, scale=3.125, budget=8000):
    w, h = page_px(cfg)
    return subprocess.Popen([chrome(), *BASE_FLAGS, f'--force-device-scale-factor={scale}', f'--window-size={w},{h}',
                             f'--virtual-time-budget={budget}', f'--screenshot={out_png}',
                             f'file://{html_path}?cvpage={page_no}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def print_pdf(html_path, out_pdf, budget=10000):
    subprocess.run([chrome(), *BASE_FLAGS, '--no-pdf-header-footer', f'--virtual-time-budget={budget}',
                    f'--print-to-pdf={out_pdf}', f'file://{html_path}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def dump_attr(html_path, attr, budget=15000):
    """Load a page that writes JSON into <body data-ATTR>, return the parsed JSON."""
    out = subprocess.run([chrome(), *BASE_FLAGS, f'--virtual-time-budget={budget}', '--dump-dom', f'file://{html_path}'],
                         capture_output=True, text=True).stdout
    m = re.search(rf'data-{attr}="([^"]*)"', out)
    if not m:
        sys.exit(f'page script produced no data-{attr} (did fonts/images fail to load?)')
    d = json.loads(htmlmod.unescape(m.group(1)))
    if isinstance(d, dict) and d.get('ERROR'):
        sys.exit(f"page script error: {d['ERROR']}\n{d.get('stack', '')}")
    return d


# ---------------------------------------------------------------- html transforms
FACE_RE = re.compile(r'@font-face\s*\{[^}]*\}', re.S)


def static_font_html(cfg, src):
    """Replace every @font-face of a configured family with the configured static faces
    (Canva drops variable fonts, and the PPTX must name the exact static face)."""
    aliases = set(cfg.fonts)

    def keep(m):
        fam = re.search(r'font-family\s*:\s*["\']?([^;"\']+)', m.group(0))
        return '' if fam and fam.group(1).strip() in aliases else m.group(0)
    src = FACE_RE.sub(keep, src)
    faces = []
    for alias, f in cfg.fonts.items():
        for k, p in f.get('faces', {}).items():
            w = re.sub(r'\D', '', k) or '400'
            st = 'italic' if k.endswith('i') else 'normal'
            faces.append(f"@font-face {{ font-family:'{alias}'; src:url('file://{cfg.abs(p)}'); font-weight:{w}; font-style:{st}; }}")
    return inject_head(src, '<style id="cv-fonts">\n' + '\n'.join(faces) + '\n</style>', first=True)


def inject_head(src, block, first=False):
    if first:
        m = re.search(r'<head[^>]*>', src, re.I)
        return src[:m.end()] + block + src[m.end():] if m else block + src
    i = src.lower().rfind('</head>')
    return src[:i] + block + src[i:] if i >= 0 else block + src


def inject_body_end(src, block):
    i = src.lower().rfind('</body>')
    return src[:i] + block + src[i:] if i >= 0 else src + block


def isolate_script(cfg):
    """?cvpage=N shows only page N at the window's top-left (for per-page screenshots)."""
    sel = json.dumps(cfg.page_sel)
    return f'''<script>(()=>{{const n=+new URLSearchParams(location.search).get('cvpage');if(!n)return;
const S={sel};const st=document.createElement('style');
st.textContent=`html,body{{margin:0!important;padding:0!important;background:transparent!important;overflow:hidden!important}}`;
document.head.appendChild(st);
const go=()=>{{const ps=[...document.querySelectorAll(S)];ps.forEach((p,i)=>{{if(i!==n-1)p.style.setProperty('display','none','important')}});
const p=ps[n-1];if(!p)return;p.style.setProperty('margin','0','important');p.style.setProperty('box-shadow','none','important');
let e=p.parentElement;while(e&&e!==document.body){{e.style.setProperty('transform','none','important');e.style.setProperty('margin','0','important');e.style.setProperty('padding','0','important');e=e.parentElement;}}
const r=p.getBoundingClientRect();window.scrollTo(r.left+scrollX,r.top+scrollY);}};
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',go):go();}})();</script>'''


def write_beside_master(cfg, suffix, src):
    """Derived pages are written next to the master so its relative URLs keep working."""
    stem = os.path.splitext(os.path.basename(cfg.html))[0]
    p = os.path.join(os.path.dirname(cfg.html), f'_cv_{stem}.{suffix}.html')
    open(p, 'w', encoding='utf-8').write(src)
    return p


# ---------------------------------------------------------------- fonts
_metrics = {}


def font_metrics(path):
    """Vertical metrics as Chrome uses them (hhea unless USE_TYPO_METRICS), per em."""
    if path in _metrics:
        return _metrics[path]
    from fontTools.ttLib import TTFont
    t = TTFont(path, lazy=True)
    upm = t['head'].unitsPerEm
    h, o = t['hhea'], t['OS/2']
    typo = bool(o.fsSelection & (1 << 7))
    asc, desc = (o.sTypoAscender, -o.sTypoDescender) if typo else (h.ascent, -h.descent)
    cmap = t.getBestCmap() or {}
    space = t['hmtx'][cmap[32]][0] / upm if 32 in cmap else 0.25
    nm = t['name']
    _metrics[path] = dict(asc=asc / upm, desc=desc / upm, space=space, cmap=set(cmap),
                          variable='fvar' in t, italic_bit=bool(o.fsSelection & 1) or bool(t['head'].macStyle & 2),
                          family=nm.getDebugName(16) or nm.getDebugName(1), sub=nm.getDebugName(17) or nm.getDebugName(2),
                          ps=nm.getDebugName(6))
    return _metrics[path]


def sha(path):
    return hashlib.sha1(open(path, 'rb').read()).hexdigest()[:16] if os.path.exists(path) else None


def norm_text(s):
    return re.sub(r'[\s\-‐­]', '', s or '').replace('ﬁ', 'fi').replace('ﬂ', 'fl')
