#!/usr/bin/env bash
# render.sh in.html out.png [W H scale] — screenshot an HTML master with headless Chromium.
# Chromium: $CHROME, else Playwright's (~/.cache/ms-playwright), else chromium/google-chrome on PATH.
set -euo pipefail
in=${1:?in.html}; out=${2:?out.png}; W=${3:-1080}; H=${4:-1350}; S=${5:-1}
CH=${CHROME:-}
if [ -z "$CH" ]; then
  CH=$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome 2>/dev/null | sort -V | tail -1 || true)
fi
if [ -z "$CH" ]; then
  for n in chromium chromium-browser google-chrome google-chrome-stable; do command -v $n >/dev/null && CH=$(command -v $n) && break; done
fi
[ -n "$CH" ] || { echo "No Chromium: set CHROME=/path/to/chrome or 'npx playwright install chromium'" >&2; exit 1; }
abs=$(cd "$(dirname "$in")" && pwd)/$(basename "$in")
"$CH" --headless=new --no-sandbox --hide-scrollbars --disable-gpu --allow-file-access-from-files \
  ${TRANSPARENT:+--default-background-color=00000000} \
  --force-device-scale-factor="$S" --window-size="$W,$H" --virtual-time-budget=4000 \
  --screenshot="$out" "file://$abs" 2>/dev/null
echo "$out"
