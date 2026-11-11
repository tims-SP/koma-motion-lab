#!/usr/bin/env bash
# P15-37 registered P0 keypart art, nine pose HTML, Chromium and source QA.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${KOMA_P15_PYTHON:-/tmp/koma-see-through-client-venv/bin/python}"
if [[ ! -x "$PY" ]]; then PY=python3; fi
"$PY" scripts/p15_37_temporal_paint_vdd.py
"$PY" scripts/p15_37_review.py
node --check scripts/p15_37_browser.cjs
node scripts/p15_37_browser.cjs
"$PY" -m unittest scripts/test_p15_37_temporal_art.py -v
"$PY" scripts/p15_37_package.py
