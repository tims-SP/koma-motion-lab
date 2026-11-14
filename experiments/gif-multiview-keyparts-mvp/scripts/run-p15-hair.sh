#!/usr/bin/env bash
# Reproduce P0 multi-view hair strand identity and alpha/depth diagnostics.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="$(printenv KOMA_P14_PYTHON || echo python3)"
"$PYTHON" -m unittest discover -s tests -p 'test_p15_hair_occlusion.py' -v
"$PYTHON" scripts/p15_hair_occlusion.py \
  --root private-assets \
  --out evidence/p15-hair-correspondence-qa.json \
  --preview private-assets/p15-hair-occlusion/hair-strands-contact.jpg
node --check review/p15-hair-strands.js
node --check scripts/capture_p15_hair.cjs
node scripts/capture_p15_hair.cjs
"$PYTHON" scripts/verify_p15_hair.py
