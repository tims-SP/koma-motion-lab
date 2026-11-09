#!/usr/bin/env bash
# Reproduce original-source and P14-real-asset importer fixtures for P15-06.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="$(printenv KOMA_P14_PYTHON || echo python3)"
"$PYTHON" scripts/p15_holdout_source_gate.py \
  --root private-assets --design "$(printenv KOMA_P0_DESIGN_ROOT || echo /root/koma-p0-designs)" \
  --out evidence/p15-06-source-readiness.json \
  --contract metadata/p15-holdout-generation-contract.json
"$PYTHON" scripts/p15_holdout_import.py \
  --root private-assets --contract metadata/p15-holdout-generation-contract.json \
  --yaw 67.5 --parts private-assets/p14-authored-candidates/yaw067p5-artmesh/layers \
  --painting private-assets/p14-authored-candidates/yaw067p5-artmesh/yaw067p5-painted-semantic-composite.png \
  --out evidence/p15-06-importer-fixture-67p5.json --source-kind registered-p14-fixture
"$PYTHON" scripts/p15_holdout_import.py \
  --root private-assets --contract metadata/p15-holdout-generation-contract.json \
  --yaw 72.5 --parts private-assets/p14-authored-candidates/yaw072p5-artmesh/layers \
  --painting private-assets/p14-authored-candidates/yaw072p5-artmesh/yaw072p5-p0-source-mapped-artmesh.png \
  --out evidence/p15-06-importer-fixture-72p5.json --source-kind registered-p14-fixture
"$PYTHON" -m unittest discover -s tests -p 'test_p15_holdout*.py' -v
