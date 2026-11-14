#!/usr/bin/env bash
# Regenerate P15-36 pose-registered original RGB keyparts and HTML QA.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${KOMA_P15_PYTHON:-/tmp/koma-see-through-client-venv/bin/python}"
if [[ ! -x "$PY" ]]; then PY=python3; fi
"$PY" scripts/p15_36_cel_keyparts.py
"$PY" scripts/p15_36_qwen_local_repair.py
"$PY" scripts/p15_36_review.py
node --check scripts/p15_36_browser.cjs
node scripts/p15_36_browser.cjs
"$PY" -m unittest scripts/test_p15_36_paint_source.py -v
"$PY" scripts/p15_36_package.py
