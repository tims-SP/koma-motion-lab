#!/usr/bin/env python3
"""P15-34 registered pigment/ink feature candidates on P0-derived RGBA ArtMesh.

The candidates are measured from source pixels, rather than unconstrained
alpha percentiles. They are NOT artist-approved anatomical correspondences
or an inferred physical 3D nose / hair mounting solution.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_32_mesh_vdd import R,P,ANGLES,ROLES,slug,read
from p15_33_semantic_vdd import CAMERA,SRC
OUT=P/"p15-34-ink-landmarks"
QA=R/"evidence/p15-34-ink-landmarks-qa.json"
N=443

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _point(xy):
 return np.asarray(xy,dtype=np.float32).round(3).tolist()

def _choose(pixels,axis,which):
 # Select an actual pigmented sample nearest the extreme projection.
 projections=pixels @ np.asarray(axis,dtype=np.float32)
 order=np.argsort(projections)
 index=int(np.clip(round(.04*(len(order)-1)),0,len(order)-1))
 idx=order[index] if which=="low" else order[-index-1]
 return pixels[int(idx)]

def _features_eye(a,primary):
 ys,xs=np.where(a[:,:,3]>45)
 if len(xs)<100:raise ValueError("Eye part lacks painted support")
 xmin,xmax=xs.min(),xs.max();ymin,ymax=ys.min(),ys.max()
 rgb=a[:,:,:3].astype(np.int16)
 darkness=255-(.299*rgb[:,:,0]+.587*rgb[:,:,1]+.114*rgb[:,:,2])
 # Eyelid: dark ink above the central iris, within the true eye alpha.
 top=int(np.percentile(ys,53))
 ink=(a[:,:,3]>75)&(darkness>135)
 ink[:ymin]=False;ink[top+1:]=False
 pts=np.column_stack(np.where(ink)[:,::-1]).astype(np.float32)
 if len(pts)<40:
  ink=(a[:,:,3]>65)&(darkness>90)
  ink[top+1:]=False
  pts=np.column_stack(np.where(ink)[:,::-1]).astype(np.float32)
 if len(pts)<20:raise ValueError("Eye ink insufficient for corner candidates")
 a1=_choose(pts,[1,0],"low")
 a2=_choose(pts,[1,0],"high")
 # Extreme x positions are observed ink pixels, not alpha-bbox corners.
 if np.linalg.norm(a1-a2)<.25*(xmax-xmin):raise ValueError("Eye corner spread too small")
 return np.stack([primary,a1,a2]),[
  "iris.camera","eyelid.left.ink.candidate","eyelid.right.ink.candidate"],{
   "supportInkPixels":len(pts),"sourceExtent":[int(xmin),int(ymin),int(xmax),int(ymax)]
  }

def _features_clip(a,primary):
 alpha=a[:,:,3]
 rgb=a[:,:,:3]
 hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
 # Reddish/yellow/gold enamel and dark metallic outlines remain in the
 # clip's own registered ArtMesh; a threshold excludes background pixels.
 gold=(alpha>78)&(hsv[:,:,0]>=4)&(hsv[:,:,0]<=36)&(hsv[:,:,1]>38)
 if int(gold.sum())<90:gold=alpha>95
 ys,xs=np.where(gold)
 pts=np.stack([xs,ys],axis=1).astype(np.float32)
 if len(pts)<100:raise ValueError("Gold clip pigment missing")
 candidates=[]
 for axis,which in [([1,1],"low"),([1,1],"high"),([1,-1],"low"),([1,-1],"high")]:
  candidates.append(_choose(pts,axis,which))
 if len({tuple(v.astype(int)) for v in candidates})<4:
  # For a narrow crossed shape, the upper and lower strokes may touch,
  # but four separate pigments must still be directly observed.
  raise ValueError("Gold bar ends merge in registered source")
 return np.vstack([primary,np.asarray(candidates)]),[
  "clip.center.camera","clip.diagonal_plus.end_a.ink.candidate",
  "clip.diagonal_plus.end_b.ink.candidate",
  "clip.diagonal_minus.end_a.ink.candidate",
  "clip.diagonal_minus.end_b.ink.candidate"],{
   "supportGoldPixels":len(pts),"goldColorMaskUsed":bool(int(gold.sum())>=90)
  }

def _features_side_hair(a,primary):
 alpha=a[:,:,3]
 dark=cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY)<140
 mask=alpha>70
 # Use painted hair boundary contours, rather than alpha-mass support.
 edges=cv2.Canny(np.uint8(mask)*255,35,90)>0
 ys,xs=np.where(edges)
 if len(xs)<80:raise ValueError("Side hair boundary missing")
 pts=np.column_stack((xs,ys)).astype(np.float32)
 ylo,yhi=np.percentile(ys,[15,98])
 near_root=pts[(pts[:,1]>=ylo-6)&(pts[:,1]<=ylo+25)]
 near_tip=pts[pts[:,1]>=yhi-10]
 if len(near_root)<10 or len(near_tip)<10:raise ValueError("Hair root/tip support missing")
 root=near_root[np.argmin(np.linalg.norm(near_root-primary[None,:],axis=1))]
 tip=near_tip[np.argmin(abs(near_tip[:,0]-float(primary[0]))) ]
 return np.stack([primary,root,tip]),[
  "hair.side.camera","hair.side.root.contour.candidate","hair.side.tip.contour.candidate"],{
   "supportBoundaryPixels":len(pts),"sourceAlphaMass":int(mask.sum())
  }

EXTRACT={"eye.far":_features_eye,
 "hair.clip.cross_gold":_features_clip,
 "hair.side":_features_side_hair}

def measured(a,role,anchor):
 pts,ids,extra=EXTRACT[role](a,np.asarray(anchor,dtype=np.float32))
 if not (np.isfinite(pts).all() and np.all(pts>=0) and np.all(pts<=442)):
  raise ValueError("Invalid image sample")
 # Three P0-derived source roles, including locally painted ink endpoints.
 return pts.astype(np.float32),ids,extra

def make():
 cam=json.loads((R/"evidence/p15-12-camera-proxy-qa.json").read_text())
 original45=P/"p2-views/whole/yaw045.png"
 expected="78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40"
 if sha(original45)!=expected:raise AssertionError("Original P0 source changed")
 frames=[]
 for yaw in ANGLES:
  source=next(x for x in cam["frames"] if x["yaw"]==yaw)
  anchors={role:np.array(source["anchors"][key]["xy"],np.float32)*(N/1024)
           for role,key in CAMERA.items()}
  directory=OUT/slug(yaw);directory.mkdir(parents=True,exist_ok=True)
  observations={}
  for role in ROLES:
   path=SRC/slug(yaw)/(role+".png")
   a=read(path)
   pts,ids,extra=measured(a,role,anchors[role])
   if len(pts)!=len(ids):raise ValueError("Named point count differs")
   image=Image.fromarray(a,"RGBA").convert("RGB")
   # White composition makes transparent images readable without adding ink.
   canvas=Image.new("RGBA",(N,N),"white")
   canvas.alpha_composite(Image.fromarray(a,"RGBA"))
   view=canvas.convert("RGB");pen=ImageDraw.Draw(view)
   colors=["#155cce","#ed285f","#e89d08","#3ea251","#945af0"]
   for i,(x,y) in enumerate(pts):
    c=colors[i%len(colors)]
    pen.ellipse((float(x)-3,float(y)-3,float(x)+3,float(y)+3),
                fill=c,outline="white",width=1)
    pen.text((float(x)+5,float(y)-8),ids[i],fill="#1b2432",
             stroke_fill="white",stroke_width=1)
   dest=directory/(role+".png");view.save(dest)
   observations[role]={"sourceRGBA":str(path.relative_to(P)),
                       "sourceSHA256":sha(path),"featureNames":ids,
                       "points443":np.round(pts,3).tolist(),"evidence":extra,
                       "annotationPath":str(dest.relative_to(P)),
                       "annotationSHA256":sha(dest),
                       "artistApproved":False}
  frames.append({"yaw":yaw,"features":observations})
 result={"schema":"KOMA-P15-34-PAINTED-INK-CANDIDATES-V1",
  "characterId":"p0_character_001","source45P0SHA256":expected,
  "angleKeys":ANGLES,"meshRoleCount":len(ROLES),"frames":frames,
  "featureAuthority":"ink/contour observations from P0-derived source-keyframe RGBA",
  "verifiedIndependentArtistLandmarks":0,
  "physicalClipMountVerified":False,
  "true3DFacialOcclusionVerified":False,
  "formalArtApproval":False,"status":"IMAGE_GROUNDED_FEATURE_CANDIDATES_REGISTERED"}
 QA.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":result["status"],"views":len(frames),
   "featuresPerRole":{r:len(frames[0]["features"][r]["featureNames"]) for r in ROLES},
   "examples":{r:frames[0]["features"][r]["points443"] for r in ROLES}}))
 return result

if __name__=="__main__":make()
