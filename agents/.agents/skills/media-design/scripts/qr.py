#!/usr/bin/env python3
"""QR codes for designed pieces: make (level H, quiet zone 4) and verify by decoding.

  qr.py make  OUT_BASENAME URL [--px 10] [--dark RRGGBB] [--light RRGGBB] [--brand BRAND.md]
      -> OUT.svg and OUT.png (a whole number of px per module), then decodes OUT.png as a check
  qr.py verify IMAGE URL [URL ...] [--degrade]
      -> decodes every QR code in IMAGE (e.g. a rendered slide); exit 1 unless each URL is found.
         --degrade also tests a copy scaled to 640 px wide, blurred and saved as JPEG q40
         (a stand-in for a phone pointed at a TV or projector).

Colours: --dark/--light win. Otherwise the tokens `qr-dark` and `qr-light` are read from the
Colours table of a brand file (--brand, else BRAND.md or brand/BRAND.md in the current
folder or a parent). With neither, black on white.

Runs itself inside scripts/.venv (segno, zxing-cpp, pillow), created on first use;
set MEDIA_DESIGN_VENV to keep the venv somewhere else.
"""
import os, re, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VENV = os.environ.get('MEDIA_DESIGN_VENV', os.path.join(HERE, '.venv'))
PY = os.path.join(VENV, 'bin', 'python')
PACKAGES = ['segno', 'zxing-cpp', 'pillow']

def ensure_venv():
    if os.path.realpath(sys.prefix) == os.path.realpath(VENV):
        return
    if not os.path.exists(PY):
        print(f'setting up {VENV} ({", ".join(PACKAGES)})...', file=sys.stderr)
        subprocess.check_call([sys.executable, '-m', 'venv', VENV])
        subprocess.check_call([PY, '-m', 'pip', 'install', '-q'] + PACKAGES)
    os.execv(PY, [PY, os.path.abspath(__file__)] + sys.argv[1:])

def opt(args, name, default):
    if name in args:
        i = args.index(name)
        if i + 1 >= len(args):
            sys.exit(f'{name} needs a value')
        v = args[i + 1]; del args[i:i + 2]; return v
    return default

def find_brand(start='.'):
    d = os.path.abspath(start)
    while True:
        for rel in ('BRAND.md', os.path.join('brand', 'BRAND.md')):
            p = os.path.join(d, rel)
            if os.path.isfile(p):
                return p
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent

def brand_tokens(path):
    """`| qr-dark | #0A0A0A | ... |` rows of a brand file -> {'qr-dark': '0A0A0A', ...}"""
    out = {}
    for line in open(path, encoding='utf-8'):
        m = re.match(r'\s*\|\s*`?(qr-dark|qr-light)`?\s*\|\s*`?#?([0-9a-fA-F]{6})`?\s*\|', line)
        if m:
            out.setdefault(m.group(1), m.group(2))
    return out

def hexcol(v, name):
    v = v.lstrip('#')
    if not re.fullmatch(r'[0-9a-fA-F]{6}', v):
        sys.exit(f'{name}: expected a six-digit hex colour, got {v!r}')
    return '#' + v

def decode(img):
    import zxingcpp
    return [r.text for r in zxingcpp.read_barcodes(img) if r.format == zxingcpp.BarcodeFormat.QRCode]

def make(args):
    px = int(opt(args, '--px', '10'))
    dark, light, brand = opt(args, '--dark', None), opt(args, '--light', None), opt(args, '--brand', None)
    if len(args) != 2:
        sys.exit(__doc__)
    out, url = args
    if '#' in url:
        sys.exit('refusing a #fragment URL: use a path (see references/qr-codes.md)')
    source = 'arguments'
    if dark is None or light is None:
        brand = brand or find_brand()
        if brand and not os.path.isfile(brand):
            sys.exit(f'brand file not found: {brand}')
        tok = brand_tokens(brand) if brand else {}
        source = f'{brand}' if tok else 'default black on white'
        dark = dark or tok.get('qr-dark', '000000')
        light = light or tok.get('qr-light', 'ffffff')
    dark, light = hexcol(dark, '--dark'), hexcol(light, '--light')
    import segno
    from PIL import Image
    q = segno.make(url, error='h', micro=False)
    q.save(out + '.svg', scale=1, border=4, dark=dark, light=light)
    q.save(out + '.png', scale=px, border=4, dark=dark, light=light)
    got = decode(Image.open(out + '.png'))
    ok = got == [url]
    print(f"{'OK ' if ok else 'FAIL'} {out}.png  v{q.version}-H  {q.symbol_size(scale=px, border=4)[0]}px  "
          f"{dark} on {light} ({source})  -> {got}")
    sys.exit(0 if ok else 1)

def verify(args):
    from PIL import Image, ImageFilter
    import io
    degrade = '--degrade' in args
    if degrade: args.remove('--degrade')
    if len(args) < 2:
        sys.exit(__doc__)
    path, urls = args[0], args[1:]
    im = Image.open(path).convert('RGB')
    tests = [('full', im)]
    if degrade:
        w = 640; d = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))
        b = io.BytesIO(); d.save(b, 'JPEG', quality=40); b.seek(0); tests.append(('degraded-640px', Image.open(b)))
    bad = 0
    for name, img in tests:
        got = decode(img)
        missing = [u for u in urls if u not in got]
        print(f"{'OK ' if not missing else 'FAIL'} {path} [{name}] decoded={got}" + (f' missing={missing}' if missing else ''))
        bad += bool(missing)
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] in ('-h', '--help'):
        print(__doc__); sys.exit(0)
    if not a or a[0] not in ('make', 'verify'):
        sys.exit(__doc__)
    ensure_venv()
    {'make': make, 'verify': verify}[a[0]](a[1:])
