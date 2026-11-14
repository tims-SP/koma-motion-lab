#!/usr/bin/env bash
# Reproduce P15-09 P0 anchor geometry, angle sequence, Chromium and acceptance.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${KOMA_P14_PYTHON:-python3}"
if [[ -z "${KOMA_P14_PYTHON:-}" && -x ../../../r1999-vision-venv/bin/python ]]; then
  PYTHON="$(cd ../../../r1999-vision-venv/bin && pwd)/python"
fi
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  if [[ -d ../../../browser/node_modules/playwright ]];then
    export NODE_PATH="$(cd ../../../browser/node_modules && pwd)${NODE_PATH:+:$NODE_PATH}"
  fi
fi
"$PYTHON" scripts/p15_09_anchor_pose.py
"$PYTHON" scripts/p15_09_midarc.py
node --check review/p15-09-midarc.js
node --check scripts/capture_p15_09.cjs
node scripts/capture_p15_09.cjs
"$PYTHON" -m unittest discover -s tests -p test_p15_09_anchor_midarc.py -v
"$PYTHON" scripts/p15_09_package.py
