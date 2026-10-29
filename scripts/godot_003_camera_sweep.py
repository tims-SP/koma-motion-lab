#!/usr/bin/env python3
"""GODOT-003 visual framing experiment on the authentic Live2D character.

Takes nine actual frames from Godot. Each varies only the global Node2D
transform, not MOC3, textures, mesh weights, masks or motions. Deliberately
reports framing findings separately from any Cubism fidelity claim.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import itertools
import json
import os
import subprocess
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: camera_sweep.py GODOT_BIN GODOT_PROJECT")
godot, project = sys.argv[1:]
out = Path("out/godot-002")
sweep_dir = out / "sweep"
sweep_dir.mkdir(parents=True,exist_ok=True)
combos = list(itertools.product((0.85,1.0,1.15),(180,250,320)))
records = []
sheets = []
for index,(zoom,shift_y) in enumerate(combos):
    stem = (sweep_dir / f"camera-{index:02d}").resolve()
    env = os.environ.copy()
    env.update({
        "GODOT003_SWEEP":"1",
        "GODOT003_SWEEP_ZOOM":str(zoom),
        "GODOT003_SWEEP_SHIFT_Y":str(shift_y),
        "GODOT002_DISABLE_MOTIONS":"1",
        "LIBGL_ALWAYS_SOFTWARE":"1",
        "GALLIUM_DRIVER":"llvmpipe",
    })
    # Execute against the real plugin in a software-rendered X11 display
    # prepared by the parent xvfb-run process.
    args = [godot, "--path", project, "--audio-driver", "Dummy",
            "--rendering-method", "gl_compatibility",
            "--rendering-driver", "opengl3",
            "--write-movie", str(stem)+".png",
            "--fixed-fps", "30", "--quit-after", "1"]
    p = subprocess.run(args,env=env,stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,text=True,timeout=120)
    (sweep_dir/f"camera-{index:02d}.log").write_text(p.stdout)
    if p.returncode or "GODOT003_CAMERA_SWEEP_APPLIED" not in p.stdout:
        raise SystemExit(f"camera {index} Godot failed rc={p.returncode}; see log")
    files = sorted(sweep_dir.glob(f"camera-{index:02d}*.png"))
    if len(files) != 1:
        raise SystemExit(f"camera {index}: expected 1 real MovieMaker frame, found {len(files)}")
    im = Image.open(files[0]).convert("RGB")
    if im.size != (960,540):
        raise SystemExit(f"camera {index}: wrong image size {im.size}")
    small=im.resize((240,135))
    pix=small.load()
    coords=[(x,y) for y in range(135) for x in range(240)
            if sum(abs(pix[x,y][k]-(18,28,43)[k]) for k in range(3)) > 90]
    if coords:
        bbox=[min(x for x,y in coords)*4,min(y for x,y in coords)*4,
              (max(x for x,y in coords)+1)*4,(max(y for x,y in coords)+1)*4]
        touches=(bbox[0]<=4 or bbox[1]<=4 or bbox[2]>=956 or bbox[3]>=536)
        coverage=round(len(coords)/(240*135),5)
    else:
        bbox=None
        touches=True
        coverage=0
    record={"candidate":index,"zoom":zoom,"shift_y":shift_y,
            "visible_bbox":bbox,"foreground_coverage":coverage,
            "touches_frame_edge":touches}
    records.append(record)
    print("GODOT003_CAMERA_RESULT",json.dumps(record),flush=True)
    thumb=im.resize((320,180),Image.Resampling.LANCZOS)
    sheets.append(thumb)

board=Image.new("RGB",(960,615),(34,38,44))
d=ImageDraw.Draw(board)
for i,(im,item) in enumerate(zip(sheets,records)):
    col,row=i%3,i//3
    x0,y0=col*320,row*205
    board.paste(im,(x0,y0+24))
    label=f"#{i} Z{item['zoom']} Y+{item['shift_y']}"
    if item["touches_frame_edge"]:
        label += " [CLIPPED]"
    d.text((x0+7,y0+6),label,fill=(255,255,255))
board.save(out/"fullbody-camera-sweep.jpg",quality=92,subsampling=0)
summary={"status":"CAMERA_CANDIDATES_REQUIRE_VISUAL_REVIEW",
         "source":"actual Godot 4.7.2 GDCubism frames, original MOC3",
         "candidates":records,
         "note":"Do not select camera by visible foreground alone: the model can be clipped or partly missing."}
(out/"camera-sweep.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
print("GODOT003_CAMERA_SWEEP_COMPLETED",len(records),flush=True)
