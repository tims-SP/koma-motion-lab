#!/usr/bin/env python3
"""Dense-flow and physical-anchor correspondence for existing P0 7x7 ArtMeshes.

Source: authentic P0 0/45/90 GIF views. DIS optical flow estimates dense
motion; See-through PSD iris/ear/face anchors constrain local geometry.
Vectors are per semantic mesh vertex with unchanged canonical mesh IDs.
"""
import argparse,hashlib,json,math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from flow_render import get_flow,read,sha

ROLES={
 "face.skin":["eye.near.iris","eye.far.iris","nose","mouth",
              "face.chin","face.jaw.near"],
 "eye.near":["eye.near.iris"],
 "eye.far":["eye.far.iris"],
 "ear.near":["ear.near"],
 "ear.far":["ear.far"],
 "nose":["nose"],"mouth":["mouth"],
 "hair.front":["eye.near.iris","eye.far.iris","hair.clip.center",
               "hair.ahoge.root"],
 "hair.side":["hair.side","ear.near"],
 "hair.back":["hair.back","ear.near","hair.ahoge.root"],
 "hair.ahoge":["hair.ahoge.root"],
 "hair.clip.cross_gold":["hair.clip.center"],
 "body.reference":["face.chin"]
}

def sample_flow(flow,pt,mask=None,range_px=40):
 h,w=flow.shape[:2]
 xx=int(max(0,min(w-1,round(float(pt[0])))))
 yy=int(max(0,min(h-1,round(float(pt[1])))))
 if mask is not None and not bool(mask[yy,xx]):
  x0=max(0,xx-range_px);x1=min(w,xx+range_px+1)
  y0=max(0,yy-range_px);y1=min(h,yy+range_px+1)
  coords=np.argwhere(mask[y0:y1,x0:x1])
  if len(coords):
   coords+=np.array([y0,x0])
   sel=int(np.argmin((coords[:,0]-yy)**2+(coords[:,1]-xx)**2))
   yy,xx=map(int,coords[sel])
 return flow[yy,xx].astype(np.float64)

def chosen_anchors(db,role,a,b):
 out=[]
 for name in ROLES.get(role,[]):
  rows=db["landmarks"].get(name)
  if not rows:continue
  pa=next((r for r in rows if r["yaw"]==a),None)
  pb=next((r for r in rows if r["yaw"]==b),None)
  if pa and pb and pa["visible"] and pb["visible"]:
   out.append((name,pa,pb))
 return out

def warp(root,out):
 root=Path(root).resolve();out=Path(out).resolve()
 out.parent.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((root/"p5-see-through/mv-candidate/parts.json").read_text())
 landmarks=json.loads((root/"p5-see-through/mv-candidate/landmark-qa.json").read_text())
 slots={(p["yawDeg"],p["semanticId"]):p for p in manifest["parts"]}
 assert len(slots)==39 and landmarks["characterId"]=="p0_character_001"
 source={}
 for yaw in (0,45,90):
  source[yaw]=root/f"recovered-review/frames/head_8/yaw{yaw:03d}_whole.png"
  with Image.open(source[yaw]) as im:assert im.size==(443,443)
 frame={yaw:read(file) for yaw,file in source.items()}
 grid_scale=1024/443
 qa_pairs={}
 json_pairs={}
 for a,b in ((0,45),(45,90)):
  forward,reverse=get_flow(frame[a],frame[b],mode="dis")
  flow={a:forward,b:reverse}
  json_pairs[str(a)+"-"+str(b)]={}
  pair_metrics={
     "fwdMeanNativePx":round(float(np.linalg.norm(forward,axis=2).mean()),4),
     "revMeanNativePx":round(float(np.linalg.norm(reverse,axis=2).mean()),4),
     "parts":{}}
  for srcYaw,destYaw in ((a,b),(b,a)):
   sub={}
   for role in sorted({p["semanticId"] for p in manifest["parts"]}):
    p=slots[(srcYaw,role)]
    opposite=slots[(destYaw,role)]
    source_points=np.array(p["mesh"]["vertices"],dtype=np.float64)
    if p["visibility"]=="hidden" or opposite["visibility"]=="hidden":
     sub[role]=[[0,0] for _ in source_points]
     continue
    filepath=root/p["path"]
    with Image.open(filepath) as im:
     alpha=np.array(im.convert("RGBA").getchannel("A"))
    mask=cv2.resize(alpha,(443,443),interpolation=cv2.INTER_AREA)>=20
    controls=chosen_anchors(landmarks,role,srcYaw,destYaw)
    control_data=[]
    for name,first,second in controls:
     A=np.asarray(first["xy"],dtype=np.float64)
     B=np.asarray(second["xy"],dtype=np.float64)
     anchorFlow=sample_flow(flow[srcYaw],A/grid_scale,None)*grid_scale
     residual=(B-A)-anchorFlow
     norm=float(np.linalg.norm(residual))
     if norm>100:residual*=100/norm
     control_data.append((name,A,residual))
    moved=[];magnitudes=[];anchorResidual=[]
    bbox=p.get("bbox") or [0,0,1024,1024]
    radius=max(45,min(210,(bbox[2]-bbox[0]+bbox[3]-bbox[1])*0.26))
    for vertex in source_points:
     delta=sample_flow(flow[srcYaw],vertex/grid_scale,mask)*grid_scale
     if control_data:
      weights=[]
      corrections=[]
      for name,A,residual in control_data:
       dist=float(np.linalg.norm(vertex-A))
       wt=math.exp(-(dist/radius)**2/2)
       weights.append(wt);corrections.append(residual)
      weights=np.asarray(weights,dtype=np.float64)
      if weights.sum()>1e-5:
       weights/=weights.sum()
       correction=np.sum(np.stack(corrections)*weights[:,None],axis=0)
       # Semantic control handles adjust dense flow conservatively.
       correction*=min(1.,sum(math.exp(-float(np.linalg.norm(vertex-A))**2/
                                             (2*radius*radius)) for _,A,_ in control_data))
       delta+=correction
     norm=float(np.linalg.norm(delta))
     if norm>170:delta*=170/norm
     moved.append([round(float(x),3) for x in delta])
     magnitudes.append(float(np.linalg.norm(delta)))
    sub[role]=moved
    pair_metrics["parts"][str(srcYaw)+"/"+role]={
      "vertexCount":len(moved),
      "meanVertexDisplacementPx":round(float(np.mean(magnitudes)),3),
      "maxVertexDisplacementPx":round(float(np.max(magnitudes)),3),
      "physicalAnchorControls":[x[0] for x in control_data],
      "sourceImageSHA256":sha(filepath)
    }
   json_pairs[str(a)+"-"+str(b)][str(srcYaw)]=sub
  qa_pairs[str(a)+"-"+str(b)]=pair_metrics
 payload={
  "schema":"KOMA-P0-P6-FLOW-CONSTRAINED-ARTMESH-MOTION-V1",
  "characterId":"p0_character_001",
  "canvas":[1024,1024],
  "nativeFlowCanvas":[443,443],
  "sourceP0SHA256":{str(yaw):sha(file) for yaw,file in source.items()},
  "sourceManifestSHA256":sha(root/"p5-see-through/mv-candidate/parts.json"),
  "landmarksSHA256":sha(root/"p5-see-through/mv-candidate/landmark-qa.json"),
  "mode":"OpenCV DIS dense flow sampled on real source meshes plus physical anchor residuals",
  "pairs":json_pairs,
  "qa":{
    "pairs":qa_pairs,
    "trackedSemanticSlots":39,
    "verticesPerMesh":49,
    "status":"SOURCE_DERIVED_CORRESPONDENCE_CANDIDATE",
    "artisticAcceptance":"PENDING_ACTUAL_BROWSER_RENDER_REVIEW"
  }
 }
 out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps({
  "status":payload["qa"]["status"],
  "sourceP0Angles":[0,45,90],
  "controlVertices":sum(len(v) for pair in json_pairs.values() for byAngle in pair.values() for v in byAngle.values()),
  "file":str(out),
  "sha256":sha(out),
  "sourceManifestSHA256":payload["sourceManifestSHA256"]
 },ensure_ascii=False,indent=2))
 return payload

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--output",required=True)
 args=p.parse_args()
 warp(args.root,args.output)
