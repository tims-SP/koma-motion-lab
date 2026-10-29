#!/usr/bin/env python3
"""GODOT-007 canonical-camera local facial-motion ROI gate.

Requires ffmpeg/ffprobe and Python stdlib. Only valid for 301003_x at 1920x1080,
camera GODOT003_SWEEP_ZOOM=1, SHIFT_Y=210, GODOT004_HIRES=1.
Never compare ROI coordinates across different zooms or reframings.
Does NOT establish official Live2D Cubism parity.
"""
import argparse
import json
import subprocess
from pathlib import Path

W, H = 1920, 1080
ROIS = {"mouth": (935, 183, 995, 217), "left_eye": (955, 142, 1008, 196)}
CASES = {
    "mouth_open": ("mouth", 5, 25, 1.0, 40),
    "mouth_form": ("mouth", 5, 25, 1.0, 40),
    "left_eye_open": ("left_eye", 5, 25, 1.0, 40),
    "face_idle": ("mouth", 0, 40, 1.0, 40),
}

def frame(path, n):
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"select=eq(n\\,{n})",
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        timeout=40)
    assert len(raw) == W * H * 3, f"invalid resolution or missing frame {path}:{n}"
    return memoryview(raw)

def metrics(a, b, bounds):
    x1, y1, x2, y2 = bounds
    total = changed = 0
    for y in range(y1, y2):
        off, stop = (y*W+x1)*3, (y*W+x2)*3
        aa, bb = a[off:stop], b[off:stop]
        for k in range(0, len(aa), 3):
            ds = [abs(aa[k+t]-bb[k+t]) for t in (0,1,2)]
            total += sum(ds)
            changed += max(ds) > 10
    return round(total / ((x2-x1)*(y2-y1)*3), 5), changed

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in CASES:
        p.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = {"profile":"301003_x 1920x1080 fullbody zoom=1 shift_y=210",
              "limitations":"model-specific ROIs; not official Cubism parity"}
    failures = []
    for name, (roi, i, j, min_mae, min_pixels) in CASES.items():
        path = getattr(args, name)
        meta = json.loads(subprocess.check_output(
            ["ffprobe","-v","error","-select_streams","v:0",
             "-show_entries","stream=width,height,nb_frames,avg_frame_rate",
             "-of","json",str(path)],timeout=30))["streams"][0]
        assert (meta["width"],meta["height"]) == (W,H), (name,meta)
        mae, pixels = metrics(frame(path,i), frame(path,j), ROIS[roi])
        passed = mae >= min_mae and pixels >= min_pixels
        result[name] = {"frames":meta.get("nb_frames"),"roi":roi,
                        "bounds":ROIS[roi],"sample_frames":[i,j],
                        "mae_rgb_255":mae,"changed_pixels_gt10":pixels,
                        "passed":passed}
        if not passed: failures.append(name)
        print(name, "PASS" if passed else "FAIL", mae, pixels, flush=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    if failures:
        raise SystemExit("Facial ROI gate failed: " + ", ".join(failures))

if __name__ == "__main__":
    main()
