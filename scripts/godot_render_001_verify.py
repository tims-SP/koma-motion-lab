#!/usr/bin/env python3
"""Validate actual Godot movie frames and encoded MP4, not only exit status."""
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
import argparse
import glob
import json
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--directory", default="out/godot-render-001")
parser.add_argument("--expected", type=int, default=90)
args = parser.parse_args()
folder = Path(args.directory)
files = sorted(glob.glob(str(folder / "shot*.png")))
record = {"expected": args.expected, "frame_count": len(files), "status": "FAIL"}
errors = []
if len(files) != args.expected:
    errors.append(f"expected {args.expected} PNG frames; got {len(files)}")
if not files:
    print(json.dumps(record, indent=2))
    sys.exit(1)
frames = []
for index in sorted(set([0, len(files)//4, len(files)//2, len(files)*3//4, len(files)-1])):
    with Image.open(files[index]) as src:
        frames.append(src.convert("RGB"))
if any(im.size != (960, 540) for im in frames):
    errors.append("PNG resolution mismatch")
stddev = [round(v, 3) for v in ImageStat.Stat(frames[-1]).stddev]
record["last_frame_rgb_stddev"] = stddev
if max(stddev) < 15:
    errors.append("near-flat last frame")
diffs = []
for a, b in zip(frames, frames[1:]):
    diff = ImageChops.difference(a, b)
    score = sum(ImageStat.Stat(diff).mean) / 3
    diffs.append(round(score, 4))
record["sampled_frame_difference_mean"] = diffs
if len(diffs) == 0 or max(diffs) < 1.0:
    errors.append("no significant temporal motion")
movie = folder / "preview.mp4"
if not movie.exists() or movie.stat().st_size < 5000:
    errors.append("encoded video missing or too small")
else:
    probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames",
        "-select_streams", "v:0", "-show_entries",
        "stream=width,height,nb_read_frames,avg_frame_rate",
        "-of", "json", str(movie)], capture_output=True, text=True, check=True)
    record["video"] = json.loads(probe.stdout)
    streams = record["video"].get("streams", [])
    if not streams:
        errors.append("ffprobe found no video stream")
    else:
        s = streams[0]
        if (s.get("width"), s.get("height")) != (960, 540):
            errors.append("MP4 resolution mismatch")
        if int(s.get("nb_read_frames", "0")) != args.expected:
            errors.append("MP4 decoded-frame count mismatch")
contact = Image.new("RGB", (960, 540 * len(frames)))
for i, img in enumerate(frames):
    contact.paste(img, (0, i * 540))
contact.save(folder / "contact-sheet.jpg", quality=85)
record["errors"] = errors
record["status"] = "PASS" if not errors else "FAIL"
(folder / "summary.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
sys.exit(1 if errors else 0)
