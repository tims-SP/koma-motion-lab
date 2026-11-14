#!/usr/bin/env bash
# Verify original P0 source hashes and independent holdout art requirements.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="$(printenv KOMA_P14_PYTHON || echo python3)"
DESIGN="$(printenv KOMA_P0_DESIGN_ROOT || echo /root/koma-p0-designs)"
"$PYTHON" -m py_compile scripts/p15_holdout_source_gate.py
"$PYTHON" scripts/p15_holdout_source_gate.py \
  --root private-assets \
  --design "$DESIGN" \
  --out evidence/p15-06-source-readiness.json \
  --contract metadata/p15-holdout-generation-contract.json
"$PYTHON" -m unittest discover -s tests -p 'test_p15_holdout_source_gate.py' -v
