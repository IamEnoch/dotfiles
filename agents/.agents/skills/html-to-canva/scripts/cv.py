#!/usr/bin/env python3
"""html-to-canva: the HTML master is the source of truth; Canva is a build target.

  cv.py init <master.html> <workdir>   scaffold <workdir>/canva.json from the page's @font-face rules
  cv.py lint     [-c canva.json]       Canva-safety check of the master (exit 1 on errors)
  cv.py build    [-c ...] [--skip-bg]  reference.pdf + backgrounds + extract + PPTX + manifest
  cv.py audit    <canva.pdf> [--tol 0.5]   compare a Canva PDF export with build/reference.pdf
  cv.py calibrate <canva.pdf>          measure where Canva put each box -> calib.json (then rebuild)
  cv.py plan                           diff build/ against synced/ -> build/sync-plan.{json,md}
  cv.py accept                         record build/ as what Canva now holds (after a passing audit)
  cv.py freeze                         Canva becomes the master; plan refuses to run afterwards
  cv.py status                         what is built, synced, calibrated and frozen

-c defaults to $CANVA_CONFIG or ./canva.json (a directory containing canva.json also works).
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cvlib


def cmd_init(a):
    html = os.path.abspath(a.html)
    work = os.path.abspath(a.workdir)
    os.makedirs(work, exist_ok=True)
    cfgp = os.path.join(work, 'canva.json')
    if os.path.exists(cfgp) and not a.force:
        sys.exit(f'{cfgp} exists (use --force to overwrite)')
    src = open(html, encoding='utf-8').read()
    base = os.path.dirname(html)
    fonts, notes = {}, []
    for m in cvlib.FACE_RE.finditer(src):
        r = m.group(0)
        fam = re.search(r'font-family\s*:\s*["\']?([^;"\']+)', r)
        url = re.search(r'url\(\s*["\']?([^)"\']+)', r)
        if not fam or not url:
            continue
        fam = fam.group(1).strip()
        u = url.group(1)
        path = u[7:] if u.startswith('file://') else (u if os.path.isabs(u) else os.path.normpath(os.path.join(base, u)))
        wt = re.search(r'font-weight\s*:\s*([\d ]+)', r)
        weights = [int(x) for x in wt.group(1).split()] if wt else [400]
        italic = bool(re.search(r'font-style\s*:\s*italic', r))
        f = fonts.setdefault(fam, {'canva': None, 'faces': {}})
        if not os.path.exists(path):
            notes.append(f'{fam}: file not found {path}'); continue
        m_ = cvlib.font_metrics(path)
        f['canva'] = f['canva'] or re.sub(r'\s+(Light|Medium|SemiBold|Semibold|Bold|Italic|Regular|Thin|Black|ExtraBold|ExtraLight)\b.*$', '', m_['family'] or fam)
        if m_['variable'] or len(weights) > 1:
            notes.append(f'{fam}: {os.path.basename(path)} is variable ({weights}); add static faces per weight used')
            continue
        f['faces'][f'{weights[0]}{"i" if italic else ""}'] = os.path.relpath(path, work)
    for fam, f in fonts.items():
        # One declared face is only a hint: a one-weight script or display font is named as is in
        # Canva, while a text family with one weight in use still needs its weight name.
        if len(f['faces']) == 1 and list(f['faces']) == ['400']:
            f['single_face'] = True
            notes.append(f'{fam}: one Regular face found, set single_face=true; '
                         'set it to false if this family has more weights in Canva')
    cfg = {
        'name': os.path.splitext(os.path.basename(html))[0],
        'html': os.path.relpath(html, work),
        'page': {'selector': 'section.page', 'width_mm': 210, 'height_mm': 297},
        'fonts': fonts,
        'blocked_weights': [600],
        'live_images': [],
        'bake_css': '',
        'bake_glyphs': [],
        'split_lines': [],
        'canva': {'design_id': None, 'edit_url': None, 'units_per_mm': None},
    }
    json.dump(cfg, open(cfgp, 'w'), indent=2)
    print(f'wrote {cfgp}')
    print('check: page selector/size, the Canva name of each family, live_images (swappable photos)')
    for n in notes:
        print('  !', n)


def cmd_lint(a):
    import lint
    cfg = cvlib.load_config(a.config)
    e, w, i, text = lint.run(cfg)
    print(text)
    sys.exit(1 if e else 0)


def cmd_build(a):
    import build, lint
    cfg = cvlib.load_config(a.config)
    if not a.no_lint:
        e, w, i, text = lint.run(cfg)
        if e:
            print(text)
            sys.exit(f'\nlint found {len(e)} errors; fix them (or pass --no-lint to build anyway)')
        print(f'lint: 0 errors, {len(w)} warnings (build/lint-report.md)')
    out, n, nb, ni, cal = build.run(cfg, skip_bg=a.skip_bg)
    print(f'built {out}\n  {n} pages, {nb} text boxes, {ni} live photos; calibration: {cal}')


def cmd_audit(a):
    import audit
    cfg = cvlib.load_config(a.config)
    fails, text = audit.audit(cfg, os.path.abspath(a.pdf), tol=a.tol)
    print(text if a.verbose else '\n'.join(l for l in text.splitlines() if l.startswith(('#', '**', '- [high]'))))
    print(f'\nfull report + side-by-side images: {os.path.join(cfg.build, "audit")}')
    sys.exit(1 if fails else 0)


def cmd_calibrate(a):
    import audit
    cfg = cvlib.load_config(a.config)
    print(audit.calibrate(cfg, os.path.abspath(a.pdf)))
    print('calib.json updated: run `cv.py build --skip-bg` and re-import to apply')


def cmd_plan(a):
    import sync
    cfg = cvlib.load_config(a.config)
    sync.plan(cfg)
    print(open(os.path.join(cfg.build, 'sync-plan.md')).read())


def cmd_accept(a):
    import sync
    cfg = cvlib.load_config(a.config)
    sync.accept(cfg)
    print(f'synced/ now mirrors build/ (master sha {json.load(open(os.path.join(cfg.build, "state.json")))["master_sha"]})')


def cmd_freeze(a):
    cfg = cvlib.load_config(a.config)
    open(os.path.join(cfg.dir, 'FROZEN'), 'w').write('Canva is the master from here on. Edit in Canva.\n')
    print('frozen: Canva is now the master; HTML changes will no longer be planned for sync')


def cmd_status(a):
    cfg = cvlib.load_config(a.config)
    def st(d):
        p = os.path.join(d, 'state.json')
        return json.load(open(p)) if os.path.exists(p) else None
    b, s = st(cfg.build), st(cfg.synced)
    cur = cvlib.sha(cfg.html)
    cal = os.path.join(cfg.dir, 'calib.json')
    print(f'design   : {cfg.name}  ({cfg.html})')
    print(f'canva    : {cfg.canva.get("design_id") or "-"} {cfg.canva.get("edit_url") or ""}  units/mm={cfg.canva.get("units_per_mm")}')
    print(f'build    : {"none" if not b else ("current" if b["master_sha"] == cur else "STALE (master changed since build)")}')
    print(f'synced   : {"none (not imported/accepted yet)" if not s else ("same as build" if b and s["master_sha"] == b["master_sha"] else "behind build: run plan")}')
    print(f'calib    : {len(json.load(open(cal))) if os.path.exists(cal) else 0} measured boxes')
    print(f'frozen   : {os.path.exists(os.path.join(cfg.dir, "FROZEN"))}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('init'); p.add_argument('html'); p.add_argument('workdir'); p.add_argument('--force', action='store_true'); p.set_defaults(f=cmd_init)
    for name, fn in (('lint', cmd_lint), ('build', cmd_build), ('plan', cmd_plan), ('accept', cmd_accept), ('freeze', cmd_freeze), ('status', cmd_status)):
        p = sub.add_parser(name); p.add_argument('-c', '--config'); p.set_defaults(f=fn)
        if name == 'build':
            p.add_argument('--skip-bg', action='store_true', help='reuse build/bg (text-only changes)')
            p.add_argument('--no-lint', action='store_true')
    for name, fn in (('audit', cmd_audit), ('calibrate', cmd_calibrate)):
        p = sub.add_parser(name); p.add_argument('pdf'); p.add_argument('-c', '--config'); p.set_defaults(f=fn)
        if name == 'audit':
            p.add_argument('--tol', type=float, default=0.5); p.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
