#!/usr/bin/env bash
# Repeat local P14 visual engineering review using the private image workspace.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
PYTHON="$(printenv KOMA_P14_PYTHON || echo python3)"
NODE="$(printenv KOMA_P14_NODE || echo node)"
"$PYTHON" -m py_compile scripts/p14_*.py scripts/verify_p14_evidence.py
"$NODE" --check scripts/capture_p14_painted.cjs
"$NODE" --check review/p14-painted-view.js
"$PYTHON" -m unittest discover -s tests -p 'test_verify_p14_evidence.py' -v
"$NODE" scripts/capture_p14_painted.cjs
"$PYTHON" scripts/p14_quality_assessment.py \
  --root private-assets \
  --out private-assets/p14-authored-candidates/p14-quality
"$PYTHON" scripts/verify_p14_evidence.py \
  --root private-assets \
  --out evidence/p14-painted-view-qa.json
