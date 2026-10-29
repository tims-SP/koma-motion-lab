#!/usr/bin/env python3
"""Conservative image/video validation: real Live2D playback, not yet fidelity parity."""
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
import glob
import json
import subprocess
import sys

out = Path("out/godot-002")
paths = sorted(glob.glob(str(out / "shot*.png")))
errors = []
report = {"experiment": "GODOT-002", "frames": len(paths),
          "expected": 90, "status": "FAIL", "parity": "NOT_TESTED"}
if len(paths) != 90:
    errors.append("frame_count_not_90")
if paths:
    samples = []
    for index in sorted(set([0, len(paths)//4, len(paths)//2, len(paths)*3//4, len(paths)-1])):
        with Image.open(paths[index]) as img:
            samples.append(img.convert("RGB"))
    if any(im.size != (960,540) for im in samples):
        errors.append("wrong_image_size")
    deviations = [round(sum(ImageStat.Stat(im).stddev)/3,2) for im in samples]
    report["deviations"] = deviations
    # Reject blank background or an invisible model.
    coverage = []
    bg = (18,28,43)
    for im in samples:
        pixels = im.resize((96,54)).getdata()
        n = sum(1 for p in pixels if sum(abs(p[c]-bg[c]) for c in range(3)) > 90)
        coverage.append(round(n/5184,4))
    report["foreground_coverage"] = coverage
    if max(coverage) < .025:
        errors.append("no_visible_model")
    differences = [round(sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3,3)
                   for a,b in zip(samples,samples[1:])]
    report["frame_differences"] = differences
    if not differences or max(differences) < .65:
        errors.append("no_visible_motion")
    contact = Image.new("RGB", (960, 540*len(samples)))
    for index, frame in enumerate(samples):
        contact.paste(frame, (0,540*index))
    contact.save(out/"contact-sheet.jpg",quality=90)
movie = out / "preview.mp4"
if not movie.is_file() or movie.stat().st_size < 5000:
    errors.append("missing_mp4")
else:
    args = ["ffprobe","-v","error","-count_frames","-select_streams","v:0",
            "-show_entries","stream=width,height,nb_read_frames","-of","json",str(movie)]
    p = subprocess.run(args,check=True,capture_output=True,text=True)
    streams = json.loads(p.stdout).get("streams",[])
    report["video"] = streams
    if not streams or int(streams[0].get("nb_read_frames","0"))!=90:
        errors.append("mp4_frame_mismatch")
report["errors"] = errors
report["status"] = "PASS_PLAYBACK_NOT_PARITY" if not errors else "FAIL"
out.mkdir(parents=True,exist_ok=True)
(out/"summary.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
sys.exit(1 if errors else 0)
