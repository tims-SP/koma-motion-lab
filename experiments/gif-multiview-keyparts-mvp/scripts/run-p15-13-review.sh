#!/usr/bin/env bash
# Reproduce P15-13 camera-guided ArtMesh channels, real browser and archive.
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
"$PY" scripts/p15_13_structural_condition.py
"$PY" scripts/p15_13_local_alignment.py
node --check scripts/capture_p15_13.cjs
node scripts/capture_p15_13.cjs
"$PY" -m unittest discover -s tests -p test_p15_13_structural_control.py -v
"$PY" scripts/p15_13_package.py
