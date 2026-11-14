#!/usr/bin/env python3
"""P0 55-degree anchor-guided keyview geometry from approved 45-degree artwork.

This deterministic geometry reference tracks original P5 anatomical landmarks.
It is an editable pose study; an independent painting is the final art input.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

BASE=Path(__file__).resolve().parent.parent
ASSETS=BASE/"private-assets"
SOURCE=ASSETS/"p2-views/whole/yaw045.png"
LANDMARKS=ASSETS/"p5-see-through/mv-candidate/landmark-qa.json"
MANIFEST=ASSETS/"p5-see-through/mv-candidate/parts.json"
DEST=ASSETS/"p15-09-anchor-pose"
ANCHOR_SHIFT={
 "face.chin":(.24,.18),
 "face.jaw.near":(.24,.18),
 "eye.near.iris":(.26,.20),
 "nose":(.24,.25),
 "mouth":(.24,.25),
 "ear.near":(.25,.18),
 "hair.ahoge.root":(.18,.20),
 "hair.clip.center":(.05,.00),
}
SUPPORT=[
 ((0,0),(0,0)),((1023,0),(0,0)),((0,1023),(0,0)),((1023,1023),(0,0)),
 ((100,380),(0,0)),((900,430),(0,0)),((240,860),(0,0)),((770,920),(0,0)),
 ((280,310),(4,0)),((340,640),(6,1)),((760,220),(4,0)),
]


def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()


def source_checks():
 d=json.loads(MANIFEST.read_text())
 q=json.loads(LANDMARKS.read_text())
 if d["characterId"]!="p0_character_001" or q["characterId"]!="p0_character_001":
  raise ValueError("P0 identity check failed")
 e=next(x for x in d["wholeViews"] if x["yawDeg"]==45)
 if ASSETS/e["path"]!=SOURCE or sha(SOURCE)!=e["sha256"]:
  raise ValueError("P0 yaw45 source differs from registered SHA")
 return d,q,e


def anchors(db):
 result=[]
 for role,(fraction,_) in ANCHOR_SHIFT.items():
  entries=db["landmarks"].get(role,[])
  a=next((r for r in entries if r["yaw"]==45 and r.get("visible")),None)
  b=next((r for r in entries if r["yaw"]==90 and r.get("visible")),None)
  if not a:continue
  source=np.array(a["xy"],dtype=np.float64)
  if b:
   target=source+(np.array(b["xy"])-source)*fraction
  elif role=="hair.clip.center":
   target=source+np.array([5.,0.])
  else:target=source
  result.append({"semantic":role,"source":source.tolist(),
                 "target":target.tolist(),"vector":(target-source).tolist(),
                 "physicalRole":"registered P5 landmark"})
 # Far-eye visibility is maintained through the 55-degree 3/4 view.
 # Shift it toward the nose as the near-eye shifts toward the contour.
 a=next(r for r in db["landmarks"]["eye.far.iris"] if r["yaw"]==45)
 far=np.array(a["xy"],dtype=np.float64)
 target=far+np.array([-6.,-2.])
 result.append({"semantic":"eye.far.iris","source":far.tolist(),
               "target":target.tolist(),"vector":(target-far).tolist(),
               "physicalRole":"partially-visible far eye"})
 for i,(point,vec) in enumerate(SUPPORT):
  target=np.array(point,dtype=float)+np.array(vec,dtype=float)
  result.append({"semantic":f"boundary.{i}","source":list(point),
                 "target":target.tolist(),"vector":list(vec),
                 "physicalRole":"canvas and silhouette boundary"})
 return result


def warp_image(paint,control,sigma=155.,regularization=.035):
 # Destination-to-source Gaussian basis honors target anchor locations.
 pts=np.asarray([a["target"] for a in control],dtype=np.float64)
 motion=np.asarray([np.array(a["source"])-np.array(a["target"]) for a in control])
 distances=((pts[:,None,:]-pts[None,:,:])**2).sum(-1)
 basis=np.exp(-distances/(2*sigma*sigma))
 coef=np.linalg.solve(basis+regularization*np.eye(len(pts)),motion)
 h,w=paint.shape[:2]
 gx,gy=np.meshgrid(np.arange(256,dtype=np.float64)*((w-1)/255),
                   np.arange(256,dtype=np.float64)*((h-1)/255))
 down=np.zeros((256,256,2),dtype=np.float64)
 for i,(p,vec) in enumerate(zip(pts,coef)):
  dist=(gx-p[0])**2+(gy-p[1])**2
  weight=np.exp(-dist/(2*sigma*sigma))
  down[:,:,0]+=vec[0]*weight
  down[:,:,1]+=vec[1]*weight
 flow=cv2.resize(down.astype(np.float32),(w,h),interpolation=cv2.INTER_CUBIC)
 xx,yy=np.meshgrid(np.arange(w,dtype=np.float32),np.arange(h,dtype=np.float32))
 # Warp premultiplied color to preserve transparency through every edge.
 pixels=paint.astype(np.float32)/255.
 pixels[:,:,:3]*=pixels[:,:,3:]
 mapped=cv2.remap(pixels,xx+flow[:,:,0],yy+flow[:,:,1],
                  cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
 alpha=np.clip(mapped[:,:,3:],0,1)
 rgb=np.where(alpha>1e-5,np.clip(mapped[:,:,:3],0,1)/np.maximum(alpha,1e-5),0)
 result=np.uint8(np.rint(np.concatenate([np.clip(rgb,0,1),alpha],axis=2)*255))
 return result,flow


def make_contact(paint,corrected):
 items=[("P0 45 source",paint),("55 anchor geometry",corrected)]
 middle=ASSETS/"p15-independent-candidates/yaw065-source-rgba.png"
 with Image.open(middle) as im:items.append(("P15 65 source",np.array(im.convert("RGBA"))))
 sheet=Image.new("RGB",(3*340,380),(246,246,246))
 d=ImageDraw.Draw(sheet)
 for i,(name,data) in enumerate(items):
  tmp=Image.new("RGBA",(1024,1024),"white")
  tmp.alpha_composite(Image.fromarray(data,"RGBA"))
  sheet.paste(tmp.convert("RGB").resize((340,340),Image.Resampling.LANCZOS),(i*340,27))
  d.text((i*340+9,7),name,fill=(15,15,15))
 f=DEST/"p15-09-pose-contact.jpg"
 sheet.save(f,quality=92)
 return f


def main():
 _,landmarks,source=source_checks()
 DEST.mkdir(parents=True,exist_ok=True)
 with Image.open(SOURCE) as im:
  original=np.array(im.convert("RGBA"))
 pts=anchors(landmarks)
 new,flow=warp_image(original,pts)
 path=DEST/"yaw055-p5-anchor-reference.png"
 Image.fromarray(new,"RGBA").save(path)
 panel=make_contact(original,new)
 measurement={
  "schema":"KOMA-P15-09-P5-ANCHOR-PROJECTED-55-V1",
  "characterId":"p0_character_001",
  "targetAngle":55.0,
  "sourceAngle":45.0,"sourceArtworkSha256":source["sha256"],
  "sourceLandmarksSha256":sha(LANDMARKS),
  "anchorCount":len(pts),"controlPoints":pts,
  "flowMaxPixelMagnitude":round(float(np.linalg.norm(flow,axis=2).max()),4),
  "flowMeanPixelMagnitude":round(float(np.linalg.norm(flow,axis=2).mean()),4),
  "sourceImageShape":list(original.shape),
  "generatedImageSha256":sha(path),
  "generatedImagePath":str(path.relative_to(ASSETS)),
  "contactPath":str(panel.relative_to(ASSETS)),
  "contactSha256":sha(panel),
  "geometryRole":"physically-constrained three-quarter pose study",
  "artisticStatus":"POSE_REFERENCE_REQUIRES_VISUAL_APPROVAL",
  "originalHeroSha256Verified":False,
  "requiredNextStage":"register independent painted parts and occlusion correspondences"
 }
 qa=BASE/"evidence/p15-09-anchor-pose-qa.json"
 qa.write_text(json.dumps(measurement,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":measurement["artisticStatus"],
                   "anchors":len(pts),
                   "maxDisplacement":measurement["flowMaxPixelMagnitude"],
                   "frameSHA256":measurement["generatedImageSha256"],
                   "contactSHA256":measurement["contactSha256"]}))
if __name__=="__main__":main()
