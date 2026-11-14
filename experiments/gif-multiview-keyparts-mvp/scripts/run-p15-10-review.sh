#!/usr/bin/env bash
# Reproduce P0 semantic keyview, 55–65 ArtMesh animation, browser and archive QA.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${KOMA_P14_PYTHON:-python3}"
if [[ -z "${KOMA_P14_PYTHON:-}" && -x ../../../r1999-vision-venv/bin/python ]]; then
  PY="$(cd ../../../r1999-vision-venv/bin && pwd)/python"
fi
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  if [[ -d ../../../browser/node_modules/playwright ]]; then
    export NODE_PATH="$(cd ../../../browser/node_modules && pwd)${NODE_PATH:+:$NODE_PATH}"
  fi
fi
"$PY" scripts/p15_09_anchor_pose.py
"$PY" scripts/p15_09_midarc.py
"$PY" scripts/p15_10_semantic_key55.py
"$PY" scripts/p15_10_semantic_arc.py
node --check review/p15-10-semantic.js
node --check scripts/capture_p15_10.cjs
node scripts/capture_p15_10.cjs
"$PY" -m unittest discover -s tests -p test_p15_10_semantic_layers.py -v
"$PY" scripts/p15_10_package.py
