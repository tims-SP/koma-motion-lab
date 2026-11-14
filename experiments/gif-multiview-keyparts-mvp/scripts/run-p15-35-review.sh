#!/usr/bin/env bash
# Recreate all P15-35 depth partitions, front-hair UV scene, real browser, archive.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${KOMA_P15_PYTHON:-/tmp/koma-see-through-client-venv/bin/python}"
if [[ ! -x "$PY" ]]; then PY=python3; fi
"$PY" scripts/p15_35_depth_mount.py
"$PY" scripts/p15_35_review.py
node --check scripts/p15_35_browser.cjs
node scripts/p15_35_browser.cjs
"$PY" -m unittest scripts/test_p15_35_depth_mount.py -v
"$PY" scripts/p15_35_package.py
