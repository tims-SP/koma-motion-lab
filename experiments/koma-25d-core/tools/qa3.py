#!/usr/bin/env python3
"""CORE-003 automated render checks: diagnostic only; no anime art acceptance."""
import json
from pathlib import Path
from PIL import Image, ImageChops

root=Path(__file__).resolve().parents[1]
folder=root/"out"/"core003"
frames=sorted((folder/"turn").glob("*.png"))
if len(frames)!=73:raise SystemExit(f"FAIL: {len(frames)} != 73")
background=(242,244,248)

def load(path):
    im=Image.open(path).convert("RGB")
    if im.size!=(960,540):raise ValueError(f"Unexpected size: {path}")
    return im.crop((0,110,960,540))

def fraction(a,b,thresh=20):
    diff=ImageChops.difference(a,b).convert("L")
    hist=diff.histogram()
    return sum(hist[thresh+1:])/(a.width*a.height)

bg=Image.new("RGB",(960,430),background)
source=load(folder/"original_front_only.png")
with_shell=load(folder/"front_with_shell.png")
front_changes=fraction(source,with_shell)
coverage=[]
for frame in frames:
    im=load(frame)
    coverage.append(fraction(im,bg,24))
if any(v<0.013 for v in (coverage[0],coverage[18],coverage[36],coverage[54],coverage[72])):
    raise SystemExit(f"FAIL: blank model at one canonical angle: {[coverage[i] for i in (0,18,36,54,72)]}")
# A source front should remain mostly unchanged when the side/back shell is present.
if front_changes>0.03:
    raise SystemExit(f"FAIL: side/back proxy destroys source view (>3% changed): {front_changes:.4%}")
# In profile & rear pose, actual side/back material must alter rendered pixels.
new_views={}
for angle in (45,90,135,180):
    canary=load(folder/f"diagnostic_{angle}.png")
    no_shell=load(folder/f"no_shell_{angle}.png")
    new_views[str(angle)]=fraction(canary,no_shell)
if min(new_views["90"],new_views["135"],new_views["180"])<0.012:
    raise SystemExit(f"FAIL: side/back UV maps not visible: {new_views}")
# Rotation should not have abrupt multi-frame mask loss.
step_changes=[abs(coverage[i]-coverage[i-1]) for i in range(1,len(coverage))]
if max(step_changes)>0.035:
    raise SystemExit(f"FAIL: sudden geometry mask jump: {max(step_changes)}")
montage=Image.new("RGB",(960*5,540*2))
for i,idx in enumerate((0,18,36,54,72)):
    im=Image.open(frames[idx]).convert("RGB")
    montage.paste(im,(960*i,0))
for i,deg in enumerate((0,45,90,135,180)):
    name="original_front_only.png" if deg==0 else f"no_shell_{deg}.png"
    montage.paste(Image.open(folder/name).convert("RGB"),(960*i,540))
montage.save(folder/"contact.png")
report={
  "status":"PASS_DIAGNOSTIC_MULTIVIEW_SMOKE_NOT_ART",
  "num_frames":len(frames),
  "angles":[0,45,90,135,180],
  "visible_coverage_0_45_90_135_180":[coverage[i] for i in (0,18,36,54,72)],
  "max_adjacent_coverage_jump":max(step_changes),
  "front_with_shell_changed_fraction":front_changes,
  "side_back_canary_vs_source_only_changed_fraction":new_views,
  "real_front_view_pixel_parity":"NOT_TESTED_AGAINST_GODOT",
  "uv_registered_new_views":"NO",
  "source_animation_runtime_parity":"NOT_TESTED",
  "art_seam_consistency":"NOT_TESTED",
  "production_side_art":"MISSING",
  "production_back_art":"MISSING",
  "anime_visual_acceptance":"FAIL_INCOMPLETE_CHARACTER_APPEARANCE",
  "usage":"ENGINEERING_DIAGNOSTIC_ONLY"
}
(folder/"qa.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
