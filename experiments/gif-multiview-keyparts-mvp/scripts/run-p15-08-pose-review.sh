#!/usr/bin/env bash
# Reproduce P0 55-degree source-art pose, alpha, Chromium, and artifact QA.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${KOMA_P14_PYTHON:-python3}"
if [[ -z "${KOMA_P14_PYTHON:-}" && -x ../../../r1999-vision-venv/bin/python ]];then
  PY="$(cd ../../../r1999-vision-venv/bin && pwd)/python"
fi
MATTE_PY="${KOMA_P15_MATTE_PYTHON:-python3}"
if [[ -z "${KOMA_P15_MATTE_PYTHON:-}" && -x ../../../p14-rembg-venv/bin/python ]];then
  MATTE_PY="$(cd ../../../p14-rembg-venv/bin && pwd)/python"
fi
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1;then
  if [[ -d ../../../browser/node_modules/playwright ]];then
    export NODE_PATH="$(cd ../../../browser/node_modules && pwd)${NODE_PATH:+:$NODE_PATH}"
  fi
fi
DATA=private-assets/p15-08-yaw055
for version in v1 v2;do
  test -s "$DATA/yaw055-qwen2511-$version.png"
  if [[ ! -s "$DATA/yaw055-rgba-$version.png" ]];then
    "$MATTE_PY" scripts/p14_background_matte.py \
      --input "$DATA/yaw055-qwen2511-$version.png" \
      --output "$DATA/yaw055-rgba-$version.png"
  fi
done
"$PY" scripts/p15_08_pose_qa.py
node --check review/p15-08-mid-angle.js
node --check scripts/capture_p15_08.cjs
node scripts/capture_p15_08.cjs
"$PY" scripts/p15_08_pose_qa.py
"$PY" scripts/p15_08_package.py
"$PY" -m unittest discover -s tests -p test_p15_08_source_qa.py -v
