#!/usr/bin/env bash
# P15-04 P0 facial landmark and one-to-one ink tracing from SHA-verified assets.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="$(printenv KOMA_P14_PYTHON || echo python3)"
"$PYTHON" -m unittest discover -s tests -p 'test_p15_anatomical_strokes.py' -v
"$PYTHON" scripts/p15_anatomical_strokes.py \
  --root private-assets \
  --out evidence/p15-facial-correspondence-qa.json \
  --preview private-assets/p15-facial-strokes/face-strokes-contact.jpg
node --check review/p15-facial-strokes.js
node --check scripts/capture_p15_facial.cjs
node scripts/capture_p15_facial.cjs
"$PYTHON" scripts/verify_p15_facial.py
