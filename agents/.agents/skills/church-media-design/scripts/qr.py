#!/usr/bin/env python3
"""QR codes for church media: make (level H, quiet zone 4) and verify by decoding.

  qr.py make  OUT_BASENAME URL [--px 10] [--dark 061a33] [--light ffffff]
      -> OUT.svg and OUT.png (integer px per module), then decodes OUT.png as a check
  qr.py verify IMAGE URL [URL ...] [--degrade]
      -> decodes every QR in IMAGE (e.g. a rendered slide); exit 1 unless each URL is found.
         --degrade also tests a copy scaled to 640 px wide, blurred and saved as JPEG q40
         (a stand-in for a phone pointed at a TV or projector).

Runs itself inside scripts/.venv (segno, zxing-cpp, pillow), created on first use;
override the location with CMD_VENV.
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
VENV = os.environ.get('CMD_VENV', os.path.join(HERE, '.venv'))
PY = os.path.join(VENV, 'bin', 'python')

def ensure_venv():
    if os.path.realpath(sys.prefix) == os.path.realpath(VENV):
        return
    if not os.path.exists(PY):
        print(f'setting up {VENV} (segno, zxing-cpp, pillow)...', file=sys.stderr)
        subprocess.check_call([sys.executable, '-m', 'venv', VENV])
        subprocess.check_call([PY, '-m', 'pip', 'install', '-q', 'segno', 'zxing-cpp', 'pillow'])
    os.execv(PY, [PY, os.path.abspath(__file__)] + sys.argv[1:])

def opt(args, name, default):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default

def decode(img):
    import zxingcpp
    return [r.text for r in zxingcpp.read_barcodes(img) if r.format == zxingcpp.BarcodeFormat.QRCode]

def make(args):
    import segno
    from PIL import Image
    px = int(opt(args, '--px', '10')); dark = '#' + opt(args, '--dark', '061a33'); light = '#' + opt(args, '--light', 'ffffff')
    out, url = args
    if '#' in url:
        sys.exit('refusing a #fragment URL: use a path (see references/qr-codes.md)')
    q = segno.make(url, error='h', micro=False)
    q.save(out + '.svg', scale=1, border=4, dark=dark, light=light)
    q.save(out + '.png', scale=px, border=4, dark=dark, light=light)
    got = decode(Image.open(out + '.png'))
    ok = got == [url]
    print(f"{'OK ' if ok else 'FAIL'} {out}.png  v{q.version}-H  {q.symbol_size(scale=px, border=4)[0]}px  -> {got}")
    sys.exit(0 if ok else 1)

def verify(args):
    from PIL import Image, ImageFilter
    import io
    degrade = '--degrade' in args
    if degrade: args.remove('--degrade')
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
    ensure_venv()
    a = sys.argv[1:]
    if not a or a[0] not in ('make', 'verify'):
        sys.exit(__doc__)
    {'make': make, 'verify': verify}[a[0]](a[1:])
