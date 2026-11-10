#!/usr/bin/env bash
# Reproduce 57.5°/60° P0 source-candidate audit with real Chromium and RGB/RGBA SHA.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${KOMA_P14_PYTHON:-python3}"
if [[ -z "${KOMA_P14_PYTHON:-}" && -x ../../../r1999-vision-venv/bin/python ]]; then
  PYTHON="$(cd ../../../r1999-vision-venv/bin && pwd)/python"
fi
MATTE_PYTHON="${KOMA_MATTE_PYTHON:-}"
if [[ -z "$MATTE_PYTHON" && -x ../../../p14-rembg-venv/bin/python ]]; then
  MATTE_PYTHON="$(cd ../../../p14-rembg-venv/bin && pwd)/python"
fi
if [[ -z "$MATTE_PYTHON" ]]; then
  echo "A rembg isnet-anime Python environment is required." >&2
  exit 2
fi
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  if [[ -d ../../../browser/node_modules/playwright ]]; then
    export NODE_PATH="$(cd ../../../browser/node_modules && pwd)${NODE_PATH:+:$NODE_PATH}"
  fi
fi
"$PYTHON" scripts/p15_11_candidate_review.py
"$MATTE_PYTHON" - <<'PY'
from pathlib import Path
from rembg import new_session
from scripts.p14_background_matte import run
p = Path("private-assets/p15-11-generation")
session = new_session("isnet-anime", providers=["CPUExecutionProvider"])
for source in sorted(p.glob("yaw*.png")):
    qa = run(source, p / "rgba" / source.name, session)
    if qa["identityAndAngleApproval"] != "PENDING":
        raise AssertionError("RGBA source matte must not promote candidate pose")
PY
node --check scripts/capture_p15_11.cjs
node scripts/capture_p15_11.cjs
"$PYTHON" -m unittest discover -s tests -p test_p15_11_source_candidate.py -v
"$PYTHON" scripts/p15_11_package.py
