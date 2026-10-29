#!/usr/bin/env python3
"""GODOT-007: model-free ROI positive + negative control."""
import importlib.util
from pathlib import Path

source = Path(__file__).resolve().parents[1] / "scripts/godot_007_facial_roi_gate.py"
spec = importlib.util.spec_from_file_location("gate", source)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

assert (gate.W, gate.H) == (1920, 1080)
assert gate.ROIS["mouth"][1] > gate.ROIS["left_eye"][1]
a = bytearray(gate.W * gate.H * 3)
b = bytearray(a)
# Perturb exactly 200 pixels at mouth y=201..210, outside the eye ROI.
for y in range(201,211):
    for x in range(950,970):
        j = (y*gate.W+x)*3
        b[j:j+3] = bytes((40,40,40))
mouth_mae, mouth_pixels = gate.metrics(memoryview(a),memoryview(b),gate.ROIS["mouth"])
eye_mae, eye_pixels = gate.metrics(memoryview(a),memoryview(b),gate.ROIS["left_eye"])
assert mouth_mae > 1 and mouth_pixels == 200, (mouth_mae,mouth_pixels)
assert eye_mae == 0 and eye_pixels == 0, (eye_mae,eye_pixels)
print("GODOT007_CANONICAL_ROI_SYNTHETIC_POSITIVE_AND_NEGATIVE_PASS")
