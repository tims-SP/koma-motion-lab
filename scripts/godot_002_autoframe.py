#!/usr/bin/env python3
"""Diagnostic camera fit from original unmodified static Godot render.

Only changes Node2D framing in the next render; never touches model/motion assets.
The resulting framed output MUST still pass visual inspection and motion QA.
"""
from PIL import Image
from pathlib import Path
import json
import sys

root = Path("out/godot-002")
files = sorted(root.glob("static*.png"))
if not files:
    raise SystemExit("no actual reference frames")
im = Image.open(files[len(files)//2]).convert("RGB").resize((96,54))
bg = (18,28,43)
mask = [(x,y) for y in range(54) for x in range(96)
        if sum(abs(im.getpixel((x,y))[channel]-bg[channel]) for channel in range(3)) > 90]
if len(mask) < 10:
    raise SystemExit("no sufficient foreground to infer camera transform")
x0,y0,x1,y1 = min(x for x,y in mask),min(y for x,y in mask),max(x for x,y in mask),max(y for x,y in mask)
width,height = (x1-x0+1)*10,(y1-y0+1)*10
zoom=min(2.75, max(1.0, min(650.0/width,470.0/height)))
center_x=(x0+x1+1)*5.0
center_y=(y0+y1+1)*5.0
dx=(480.0-center_x)*zoom
dy=(270.0-center_y)*zoom
result={"zoom":round(zoom,4),"shift_x":round(dx,4),"shift_y":round(dy,4),
        "original_foreground_bbox_960x540":[x0*10,y0*10,(x1+1)*10,(y1+1)*10],
        "method":"diagnostic camera-only fit; image and motion data unchanged",
        "status":"UNVERIFIED_VISUAL_COMPOSITION"}
(root/"autoframe.json").write_text(json.dumps(result,indent=2))
print("GODOT002_ZOOM="+str(result["zoom"]))
print("GODOT002_SHIFT_X="+str(result["shift_x"]))
print("GODOT002_SHIFT_Y="+str(result["shift_y"]))
print(json.dumps(result),file=sys.stderr)
