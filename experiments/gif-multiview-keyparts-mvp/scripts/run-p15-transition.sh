#!/usr/bin/env bash
# Reproduce P15 stroke correspondence diagnostics from verified P0 private assets.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
PYTHON="$(printenv KOMA_P14_PYTHON || echo python3)"
"$PYTHON" -m unittest discover -s tests -p 'test_p15_flow_limit.py' -v
"$PYTHON" scripts/p14_keyview_vdd.py \
  --root private-assets --out private-assets/p15-source-coherent \
  --method source-coherent --angles 0,45,65,67.5,72.5,77.5,90
"$PYTHON" scripts/p14_keyview_vdd.py \
  --root private-assets --out private-assets/p15-flow-cap4 \
  --method smooth-ink --flow-limit-px-per-degree 4 \
  --angles 0,45,65,67.5,72.5,77.5,90
"$PYTHON" scripts/p15_transition_qa.py \
  --root private-assets --out evidence/p15-view-transition-qa.json \
  --preview private-assets/p15-flow-cap4/p15-stroke-occlusion-contact.jpg
