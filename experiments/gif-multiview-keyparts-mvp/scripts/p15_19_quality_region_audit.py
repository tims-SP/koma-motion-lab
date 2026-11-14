#!/usr/bin/env python3
"""P15-19 RGB/edge and semantic occlusion review of source ArtMesh VDD.

Metrics are local diagnostics, NOT an artistic perceptual judgement.
"""
from pathlib import Path
from PIL import Image, ImageEnhance
import cv2, numpy as np, json, hashlib, shutil, zipfile

R=Path(__file__).resolve().parent.parent
P=R/"private-assets"
ANG=[55,57.5,60,62.5,65]
BASE=P/"p15-17-anatomical-5frame"
WIDE=P/"p15-18-stroke-wide-5frame"
ARC=P/"p15-10-semantic-pose/arc"
CAM=json.loads((R/"evidence/p15-12-camera-proxy-qa.json").read_text())
OUT=P/"exports/p15-19-quality-review"
OUT.mkdir(parents=True,exist_ok=True)
ROI_NAMES=["near_eye","far_eye","nose_bridge","front_hair","side_hair","gold_clip"]
RADIUS={"near_eye":52,"far_eye":46,"nose_bridge":65,"front_hair":100,"side_hair":115,"gold_clip":48}
ANCHOR={"near_eye":"eye.near.iris","far_eye":"eye.far.iris","nose_bridge":"nose","front_hair":"hair.front","side_hair":"hair.side","gold_clip":"hair.clip.center"}
PARTS={"near_eye":"eye.near","far_eye":"eye.far","nose_bridge":"nose","front_hair":"hair.front","side_hair":"hair.side","gold_clip":"hair.clip.cross_gold"}

def yawid(y):
 return "yaw"+str(y).replace(".","p").replace("p0","")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
 return h.hexdigest()
def read(p):
 with Image.open(p) as im:return np.asarray(im.convert("RGBA"))
def image(path,a):
 path.parent.mkdir(parents=True,exist_ok=True)
 Image.fromarray(a).save(path)
def crop(arr,x,y,r):
 side=2*r; xx=int(round(x));yy=int(round(y))
 # canvas-bounded review, no repositioning or invented paint
 pad=np.pad(arr,((r,r),(r,r),(0,0)),constant_values=0)
 return pad[yy:yy+side,xx:xx+side].copy()
def edges(a):
 rgb=a[:,:,:3];gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
 e=cv2.Canny(gray,55,135)>0
 return e&(a[:,:,3]>25)
def metric(a,b):
 delta=np.abs(a.astype(np.int16)[:,:,:3]-b.astype(np.int16)[:,:,:3])
 changed=np.any(delta>2,axis=2)
 aa=a[:,:,3]>16;bb=b[:,:,3]>16
 overlap=aa&bb
 edgea=edges(a);edgeb=edges(b)
 edge_union=edgea|edgeb
 return {"changedRgbPixels":int(np.count_nonzero(changed&overlap)),
         "changedRgbPercentOfOverlappingAlpha":round(float(np.count_nonzero(changed&overlap)/max(1,np.count_nonzero(overlap)))*100,3),
         "meanAbsoluteRgbDelta":round(float(delta[overlap].mean()) if np.any(overlap) else 0,4),
         "edgeDisagreementPercent":round(100*float(np.count_nonzero(edgea^edgeb)/max(1,np.count_nonzero(edge_union))),3),
         "bothAlphaPixels":int(np.count_nonzero(overlap))}
def run():
 rows=[]
 for y in ANG:
  angle_id=yawid(y)
  frame=next(item for item in CAM["frames"] if item["yaw"]==y)
  a=read(BASE/(angle_id+".png"));b=read(WIDE/(angle_id+".png"))
  if a.shape!=(1024,1024,4) or b.shape!=a.shape:raise ValueError("Unexpected RGBA dimensions")
  raw_a=BASE/(angle_id+".png");raw_b=WIDE/(angle_id+".png")
  if sha(raw_a)==sha(raw_b):raise AssertionError("stroke-wide must not be identical at this frame")
  pics=[]
  arc_mask={}
  for roi in ROI_NAMES:
   x,ypos=frame["anchors"][ANCHOR[roi]]["xy"]
   rad=RADIUS[roi]
   acrop=crop(a,x,ypos,rad);bcrop=crop(b,x,ypos,rad)
   da=np.abs(acrop.astype(np.int16)-bcrop.astype(np.int16)).astype(np.uint8)
   da[:,:,:3]=np.minimum(255,np.abs(acrop[:,:,:3].astype(np.int16)-bcrop[:,:,:3].astype(np.int16))*4).astype(np.uint8)
   da[:,:,3]=255
   paths={}
   for kind,arr in (("anatomy",acrop),("stroke-wide",bcrop),("rgb-delta-x4",da)):
    dest=OUT/(angle_id+"-"+roi+"-"+kind+".png")
    image(dest,arr);paths[kind]=dest.name
   part=ARC/angle_id/"parts"/(PARTS[roi]+".png")
   part_mask=read(part)[:,:,3]>16
   arc_mask[roi]=int(np.count_nonzero(part_mask))
   pics.append({"roi":roi,"center":[round(x,3),round(ypos,3)],
    "radius":rad,"files":paths,"difference":metric(acrop,bcrop),
    "sourceP15_10PartVisiblePixels":arc_mask[roi],
    "sourceP15_10MaskSHA256":sha(part)})
  rows.append({"yaw":y,"baseSHA256":sha(raw_a),"wideSHA256":sha(raw_b),
   "globalDifference":metric(a,b),"rois":pics})
 report={"schema":"KOMA-P15-19-QUALITY-REGION-AUDIT-V1",
 "characterId":"p0_character_001",
 "sourceP15_18SHA256":sha(P/"exports/p15-18-mode-comparison/qa.json"),
 "sourceCameraSHA256":sha(R/"evidence/p15-12-camera-proxy-qa.json"),
 "angles":ANG,
 "roiInterpretation":"P5 camera-projected square crops. P15-10 visibility counts are from separate earlier renderer and NOT P12 visibility measurements.",
 "views":rows,
 "artisticAcceptance":False,"independentPaintingApproved":0,"hiddenUnderpaintApproved":0,
 "status":"LOCAL_PIXEL_DIAGNOSTIC_ONLY_REVIEW_REQUIRED"}
 (R/"evidence/p15-19-quality-region-qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 (OUT/"qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 return report

if __name__=="__main__":
 q=run()
 for v in q["views"]:
  print(v["yaw"],{x["roi"]:{"changed":x["difference"]["changedRgbPixels"],"edgeDisagree":x["difference"]["edgeDisagreementPercent"],"p15mask":x["sourceP15_10PartVisiblePixels"]} for x in v["rois"]})
 print("ROI_SUMMARY",json.dumps({"views":len(q["views"]),"crops":len(q["views"])*6*3,"status":q["status"]}))
