#!/usr/bin/env bash
# render.sh in.html out.png|out.pdf [W H scale]
#   out.png: screenshot the HTML master at W x H CSS px (default 1080 x 1350), scale = device pixel ratio.
#   out.pdf: print it to PDF using the page size in the HTML's own @page rule (W, H and scale are ignored).
# TRANSPARENT=1 gives a PNG with a transparent background.
# Chromium: $CHROME, else Playwright's (~/.cache/ms-playwright), else chromium/google-chrome on PATH.
set -eu
usage() { sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; }
case "${1:-}" in -h|--help) usage; exit 0 ;; esac
[ $# -ge 2 ] || { usage >&2; exit 2; }
in=$1; out=$2; W=${3:-1080}; H=${4:-1350}; S=${5:-1}
[ -f "$in" ] || { echo "not found: $in" >&2; exit 1; }
CH=${CHROME:-}
if [ -z "$CH" ]; then
  CH=$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome 2>/dev/null | sort -V | tail -1 || true)
fi
if [ -z "$CH" ]; then
  for n in chromium chromium-browser google-chrome google-chrome-stable; do
    if command -v "$n" >/dev/null 2>&1; then CH=$(command -v "$n"); break; fi
  done
fi
[ -n "$CH" ] || { echo "No Chromium: set CHROME=/path/to/chrome or run 'npx playwright install chromium'" >&2; exit 1; }
abs=$(cd "$(dirname "$in")" && pwd)/$(basename "$in")
common="--headless=new --no-sandbox --hide-scrollbars --disable-gpu --allow-file-access-from-files --virtual-time-budget=4000"
case "$out" in
  *.pdf)
    # shellcheck disable=SC2086
    "$CH" $common --no-pdf-header-footer --print-to-pdf="$out" "file://$abs" 2>/dev/null ;;
  *)
    # shellcheck disable=SC2086
    "$CH" $common ${TRANSPARENT:+--default-background-color=00000000} \
      --force-device-scale-factor="$S" --window-size="$W,$H" --screenshot="$out" "file://$abs" 2>/dev/null ;;
esac
[ -s "$out" ] || { echo "render failed: $out was not written" >&2; exit 1; }
echo "$out"
