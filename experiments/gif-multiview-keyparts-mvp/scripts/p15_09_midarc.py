#!/usr/bin/env python3
"""Physical-anchor pose inbetweening between P0 45 and generated 65 source views.

Uses exact P0 45 texture with tracked P5 anchors for the first half, then
source-owned optical flow from the anchor pose reference toward P15 source65.
The produced frames are geometrical candidates, with artistic approval separate.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p8_semantic_occlusion import output_frame_id
from p15_07_geometry_bridge import field,warp,compose,sha
from p15_09_anchor_pose import BASE,ASSETS,SOURCE,DEST,LANDMARKS,anchors,warp_image,source_checks

OUT=ASSETS/"p15-09-midarc"
SOURCE65=ASSETS/"p15-independent-candidates/yaw065-source-rgba.png"
QA65=ASSETS/"p15-independent-candidates/yaw065-artmesh/ingest-qa.json"
ANGLES=[45.,47.5,50.,52.5,55.,57.5,60.,62.5,65.]


def rgba(path):
 with Image.open(path) as im:return np.asarray(im.convert("RGBA")).copy()


def score(a,b):
 ma=a[:,:,3]>127;mb=b[:,:,3]>127
 return round(float(np.logical_and(ma,mb).sum())/
              max(1,int(np.logical_or(ma,mb).sum())),5)


def draw(pictures,out):
 sheet=Image.new("RGB",(9*220,260),(246,246,246))
 pen=ImageDraw.Draw(sheet)
 for i,(angle,pic) in enumerate(pictures):
  base=Image.new("RGBA",(1024,1024),"white")
  base.alpha_composite(Image.fromarray(pic,"RGBA"))
  sheet.paste(base.convert("RGB").resize((220,220),Image.Resampling.LANCZOS),
              (220*i,24))
  pen.text((220*i+12,4),str(angle)+" degrees",fill=(20,20,20))
 f=out/"p15-09-midarc-contact.jpg"
 sheet.save(f,quality=92)
 return f


def run():
 _,db,ref=source_checks()
 z=json.loads(QA65.read_text())["referencePainting"]
 if ASSETS/z["path"]!=SOURCE65 or sha(SOURCE65)!=z["sha256"]:
  raise ValueError("P15 65 candidate source SHA mismatch")
 original=rgba(SOURCE)
 registered=rgba(SOURCE65)
 landmark_controls=anchors(db)
 OUT.mkdir(parents=True,exist_ok=True)
 frames=[]
 src55=None
 for ang in ANGLES:
  if ang<=55:
   w=(ang-45)/10.
   scaled=[]
   for item in landmark_controls:
    orig=np.array(item["source"])
    final=np.array(item["target"])
    changed=dict(item)
    changed["target"]=(orig+(final-orig)*w).tolist()
    scaled.append(changed)
   pixels,_=warp_image(original,scaled)
   if ang==45:
    pixels=original.copy()
   if ang==55:src55=pixels.copy()
   method="P5_ANCHOR_GUIDED_RGB"
  else:
   if ang==65:
    pixels=registered.copy()
    method="P15_REGISTERED_PAINTED_SOURCE"
   else:
    # The 55-degree key is geometry-derived; the 65-degree key is a
    # painted reference. Their topology transition is reviewed visually.
    from p15_07_geometry_bridge import N,FLOW
    import cv2
    if ang==57.5:
     fa,fb=field(src55,registered)
    t=(ang-55)/10.
    xx,yy=np.meshgrid(np.arange(N,dtype=np.float32),
                      np.arange(N,dtype=np.float32))
    wa=warp(src55,fa,t,(xx,yy))
    wb=warp(registered,fb,1-t,(xx,yy))
    pixels=compose(wa,wb,t,"source-owner",None)
    method="SOURCE_OWNED_TEXTURE_BRIDGE"
  dest=OUT/output_frame_id(ang)
  Image.fromarray(pixels,"RGBA").save(dest)
  if ang==45 and not np.array_equal(pixels,original):
   raise AssertionError("P0 45 source pixel invariant")
  if ang==65 and not np.array_equal(pixels,registered):
   raise AssertionError("P15 65 source pixel invariant")
  frames.append((ang,pixels))
 file=draw(frames,OUT)
 old_dir=ASSETS/"p15-07-wholekey-preview"
 transitions=[]
 for i in range(1,len(frames)):
  a,b=frames[i-1],frames[i]
  if not all((old_dir/output_frame_id(y)).is_file() for y,_ in (a,b)):
   raise FileNotFoundError("P15-07 comparison baseline absent")
  olda=rgba(old_dir/output_frame_id(a[0]))
  oldb=rgba(old_dir/output_frame_id(b[0]))
  transitions.append({
    "from":a[0],"to":b[0],
    "anchorAlphaIoU":score(a[1],b[1]),
    "baselineAlphaIoU":score(olda,oldb),
    "anchorMeanOpaqueRGBDelta":round(float(np.mean(abs(a[1].astype("f4")-b[1]))),4),
    "baselineMeanOpaqueRGBDelta":round(float(np.mean(abs(olda.astype("f4")-oldb))),4),
  })
 report={
  "schema":"KOMA-P15-09-ANCHOR-POSE-ARC-REVIEW-V1",
  "characterId":"p0_character_001",
  "angles":ANGLES,
  "source45Sha256":ref["sha256"],
  "source65Sha256":z["sha256"],
  "anchorGeometry55Sha256":sha(DEST/"yaw055-p5-anchor-reference.png"),
  "renderedFrames":[{"yaw":a,"sha256":sha(OUT/output_frame_id(a)),
                    "method":("P5_ANCHOR_GEOMETRY" if a<=55 else "P15_PAINTED_BRIDGE")}
                     for a,_ in frames],
  "adjacentGeometry":transitions,
  "contactSha256":sha(file),
  "contactPrivatePath":str(file.relative_to(ASSETS)),
  "renderStatus":"GEOMETRY_REFERENCE_GENERATED",
  "artisticStatus":"NEEDS_INDEPENDENT_POSE_AND_OCCLUSION_ART",
  "source55Admission":"GEOMETRY_DERIVED_INTERMEDIATE"
 }
 (BASE/"evidence/p15-09-midarc-qa.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({"status":report["renderStatus"],"frames":len(frames),
                   "alphaIoU":transitions,"contactSha256":report["contactSha256"]}))
if __name__=="__main__":run()
