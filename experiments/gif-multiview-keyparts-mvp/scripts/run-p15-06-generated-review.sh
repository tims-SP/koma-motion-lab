#!/usr/bin/env bash
# Reproduce P0 candidate keyview ArtMesh, native RGBA and Chromium source checks.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${KOMA_P14_PYTHON:-python3}"
if [[ -z "${KOMA_P14_PYTHON:-}" && -x ../../../r1999-vision-venv/bin/python ]]; then
  PYTHON="$(cd ../../../r1999-vision-venv/bin && pwd)/python"
fi
MATTE_PY="${KOMA_P15_MATTE_PYTHON:-python3}"
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  if [[ -d ../../../browser/node_modules/playwright ]]; then
    export NODE_PATH="$(realpath ../../../browser/node_modules)${NODE_PATH:+:$NODE_PATH}"
  fi
fi
DATA=private-assets/p15-independent-candidates
for view in yaw065 yaw077p5; do
  test -s "$DATA/$view-qwen2511-v2.png"
  test -s "$DATA/$view-qwen2511-v2.provenance.json"
  if [ ! -f "$DATA/$view-source-rgba.png" ]; then
    "$MATTE_PY" scripts/p14_background_matte.py \
      --input "$DATA/$view-qwen2511-v2.png" \
      --output "$DATA/$view-source-rgba.png"
  fi
done
"$PYTHON" scripts/p15_generated_semantics.py \
  --root private-assets --angle 65 --out "$DATA/yaw065-artmesh"
"$PYTHON" scripts/p15_generated_semantics.py \
  --root private-assets --angle 77.5 --out "$DATA/yaw077p5-artmesh"
for entry in "65:65022:yaw065" "77.5:77522:yaw077p5"; do
  IFS=: read -r angle seed view <<<"$entry"
  "$PYTHON" scripts/p15_holdout_import.py --root private-assets \
    --contract metadata/p15-holdout-generation-contract.json \
    --yaw "$angle" --parts "$DATA/$view-artmesh/layers" \
    --painting "$DATA/$view-source-rgba.png" \
    --out "$DATA/$view-artmesh/ingest-qa.json" \
    --source-kind independent-painting \
    --source-producer Qwen-Image-Edit-2511 --source-seed "$seed"
done
"$PYTHON" scripts/p15_inpainted_underpaint.py --root private-assets \
  --angle 77.5 --psd "$DATA/seethrough/yaw077p5-layers.psd" \
  --out "$DATA/yaw077p5-inpainted"
"$PYTHON" scripts/p15_06_generated_acceptance.py
node --check review/p15-06-keyview-art.js
node --check scripts/capture_p15_06.cjs
node scripts/capture_p15_06.cjs
"$PYTHON" scripts/p15_06_generated_acceptance.py
"$PYTHON" -m unittest discover -s tests -p 'test_p15_06_generated_art.py' -v
