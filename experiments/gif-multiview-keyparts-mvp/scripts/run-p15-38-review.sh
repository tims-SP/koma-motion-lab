#!/usr/bin/env bash
# P15-38 original P0 45-65 registered ArtMesh arc, Chromium and archive.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${KOMA_P15_PYTHON:-/tmp/koma-see-through-client-venv/bin/python}"
if [[ ! -x "$PY" ]]; then PY=python3; fi
"$PY" scripts/p15_38_extend_p0_arc.py
"$PY" scripts/p15_38_review.py
node --check scripts/p15_38_browser.cjs
node scripts/p15_38_browser.cjs
"$PY" -m unittest scripts/test_p15_38_extended_arc.py -v
"$PY" scripts/p15_38_package.py
