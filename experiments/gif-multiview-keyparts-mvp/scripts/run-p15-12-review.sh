#!/usr/bin/env bash
# Reproduce P15-12 calibrated camera anchors, source QA and browser review.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${KOMA_P14_PYTHON:-python3}"
if [[ -z "${KOMA_P14_PYTHON:-}" && -x ../../../r1999-vision-venv/bin/python ]]; then
  PY="$(cd ../../../r1999-vision-venv/bin && pwd)/python"
fi
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  if [[ -d ../../../browser/node_modules/playwright ]];then
    export NODE_PATH="$(cd ../../../browser/node_modules && pwd)${NODE_PATH:+:$NODE_PATH}"
  fi
fi
"$PY" scripts/p15_12_camera_proxy.py
"$PY" scripts/p15_12_guided_qa.py
node --check scripts/capture_p15_12.cjs
node scripts/capture_p15_12.cjs
"$PY" -m unittest discover -s tests -p test_p15_12_camera_proxy.py -v
"$PY" scripts/p15_12_package.py
