#!/usr/bin/env python3
"""Validate and repair only Cubism motion3 Meta counts in temporary CI inputs.

Preserves curves, segments, timing, interpolation, user data and all other fields.
Never alters or commits the upstream game assets.
"""
import hashlib
import json
from pathlib import Path
import sys

def motion_counts(doc):
    curves = doc.get("Curves", [])
    total_points = 0
    total_segments = 0
    for curve_no, curve in enumerate(curves):
        values = curve.get("Segments", [])
        if len(values) < 5:
            raise ValueError(f"Curve {curve_no}: missing initial point or segment")
        pos = 2
        points = 1
        segments = 0
        while pos < len(values):
            kind = values[pos]
            if type(kind) not in (int, float) or int(kind) != kind:
                raise ValueError(f"Curve {curve_no}: invalid segment discriminator {kind}")
            if kind == 1:  # cubic Bezier: type + 3 time/value pairs
                needed, added = 7, 3
            elif kind in (0, 2, 3):  # linear / stepped / inverse-stepped
                needed, added = 3, 1
            else:
                raise ValueError(f"Curve {curve_no}: unknown segment type {kind}")
            if pos + needed > len(values):
                raise ValueError(f"Curve {curve_no}: truncated segment")
            pos += needed
            points += added
            segments += 1
        if pos != len(values):
            raise ValueError(f"Curve {curve_no}: segments did not terminate")
        total_points += points
        total_segments += segments
    return len(curves), total_segments, total_points

def repair(path):
    before = path.read_bytes()
    doc = json.loads(before)
    pre_curves = json.dumps(doc["Curves"], sort_keys=True, separators=(",", ":"))
    n,segments,points = motion_counts(doc)
    meta = doc["Meta"]
    old = {k: meta.get(k) for k in ("CurveCount", "TotalSegmentCount", "TotalPointCount")}
    new = dict(CurveCount=n, TotalSegmentCount=segments, TotalPointCount=points)
    for key,value in new.items():
        meta[key] = value
    assert json.dumps(doc["Curves"], sort_keys=True, separators=(",", ":")) == pre_curves
    # Count-only repair. Re-emit JSON without changing its numeric values.
    path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    return {"path":str(path), "original_sha256":hashlib.sha256(before).hexdigest(),
            "normalized_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "original_meta":old, "verified_meta":new,
            "curves_and_segments_unchanged":True}

def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: normalize_motion.py path.motion3.json ...")
    results = [repair(Path(p)) for p in sys.argv[1:]]
    print(json.dumps({"status":"NORMALIZED_METADATA_ONLY","files":results},indent=2))

if __name__ == "__main__":
    main()
