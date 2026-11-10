#!/usr/bin/env bash
# Reproduce P0 multi-keyview ArtMesh, geometry, HTML and quality gates.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${KOMA_P14_PYTHON:-python3}"
if [[ -z "${KOMA_P14_PYTHON:-}" && -x ../../../r1999-vision-venv/bin/python ]]; then
  PYTHON="$(cd ../../../r1999-vision-venv/bin && pwd)/python"
fi
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  if [[ -d ../../../browser/node_modules/playwright ]]; then
    export NODE_PATH="$(cd ../../../browser/node_modules && pwd)${NODE_PATH:+:$NODE_PATH}"
  fi
fi
ANGLES="$("$PYTHON" -c 'print(",".join(str(2.5*x) for x in range(37)))')"
"$PYTHON" scripts/p15_07_geometry_bridge.py --angles 65,77.5 --mode benchmark
"$PYTHON" scripts/p15_07_semantic_keyframes.py --angles "$ANGLES" \
  --out private-assets/p15-07-semantic-preview --mode ink-owner
"$PYTHON" scripts/p15_07_wholekey_preview.py --angles "$ANGLES" \
  --out private-assets/p15-07-wholekey-preview
node --check review/p15-07-view.js
node --check scripts/capture_p15_07.cjs
node scripts/capture_p15_07.cjs
"$PYTHON" scripts/p15_07_review_qa.py
"$PYTHON" scripts/p15_07_package.py
"$PYTHON" -m unittest discover -s tests -p 'test_p15_07_view_pipeline.py' -v
