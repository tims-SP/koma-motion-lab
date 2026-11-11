#!/usr/bin/env bash
# Reproduce source-linked P15-34 annotated ink samples and nine-frame Mesh QA.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${KOMA_P15_PYTHON:-/tmp/koma-see-through-client-venv/bin/python}"
if [[ ! -x "$PY" ]]; then PY=python3; fi
"$PY" scripts/p15_34_ink_landmarks.py
"$PY" scripts/p15_34_ink_mesh_vdd.py
"$PY" scripts/p15_34_review.py
node --check scripts/p15_34_browser.cjs
node scripts/p15_34_browser.cjs
"$PY" -m unittest scripts/test_p15_34_ink_mesh.py -v
"$PY" scripts/p15_34_package.py
