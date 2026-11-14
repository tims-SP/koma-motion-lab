#!/usr/bin/env python3
"""P0 semantic ArtMesh landmark-guided texture with visibility-aware occlusion.

Uses the approved P0 source textures at yaw 0/45/90, independently inferred
See-through PSD parts at 0/45, and physically tracked P0 landmark points.
Remaps original pixels only. All generated previews are review candidates.
"""
import argparse,hashlib,json,math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from flow_render import get_flow,sha
from p7_semantic_dense_flow import part_to_native,native_to_rgba,CANVAS,KEYS,DEFAULT_ANGLES
from p1_front_semantic import alpha_over

TRACKS={
 "face.skin":["face.chin","face.jaw.near","eye.near.iris","eye.far.iris","nose","mouth"],
 "ear.near":["ear.near"],"ear.far":["ear.far"],
 "eye.near":["eye.near.iris"],"eye.far":["eye.far.iris"],
 "nose":["nose"],"mouth":["mouth"],
 "hair.front":["hair.front","hair.clip.center","eye.near.iris"],
 "hair.side":["hair.side","ear.near"],
 "hair.back":["hair.back","hair.ahoge.root"],
 "hair.ahoge":["hair.ahoge.root"],
 "hair.clip.cross_gold":["hair.clip.center"],
 "body.reference":["face.chin"]
}
COORDINATE_SCALE=CANVAS/1024.0
FACE_CONTROLS={"face.skin","eye.near","eye.far","ear.near","ear.far","nose","mouth"}
HIGHLIGHT_ART={"hair.front","hair.side","hair.back","hair.ahoge","hair.clip.cross_gold"}
HIDE_WINDOWS={
 (0,45,"ear.far"):(2,31),
 (45,90,"eye.far"):(52,75),
 (45,90,"hair.clip.cross_gold"):(48,70),
}
def smoothstep(v,lo,hi):
 x=np.clip((v-lo)/(hi-lo),0,1)
 return x*x*(3-2*x)

def is_visible(entry):
 return entry["visibility"]=="visible"

def tracked(db,sid,a,b):
 result=[]
 for semantic in TRACKS.get(sid,[]):
  entries=db["landmarks"].get(semantic,[])
  src=next((e for e in entries if e["yaw"]==a),None)
  dst=next((e for e in entries if e["yaw"]==b),None)
  if not src or not dst or not src["visible"] or not dst["visible"]:
   continue
  A=np.array(src["xy"],dtype=np.float32)*COORDINATE_SCALE
  B=np.array(dst["xy"],dtype=np.float32)*COORDINATE_SCALE
  result.append((semantic,A,B))
 return result

def residual_guidance(flow,anchors,source_alpha,source_bbox):
 h,w=flow.shape[:2]
 if not anchors:return flow,{"controls":0,"meanResidual":0,"radius":0}
 x,y=np.meshgrid(np.arange(w,dtype=np.float32),
                 np.arange(h,dtype=np.float32))
 corr=np.zeros_like(flow,dtype=np.float32)
 weight=np.zeros((h,w),dtype=np.float32)
 pxw=(source_bbox[2]-source_bbox[0])*COORDINATE_SCALE
 pxh=(source_bbox[3]-source_bbox[1])*COORDINATE_SCALE
 radius=np.clip(max(pxw,pxh)*0.38,22,115)
 residuals=[]
 for label,A,B in anchors:
  ax=float(np.clip(A[0],0,w-1));ay=float(np.clip(A[1],0,h-1))
  estimated=cv2.remap(flow,np.array([[ax]],dtype=np.float32),
     np.array([[ay]],dtype=np.float32),cv2.INTER_LINEAR,
     borderMode=cv2.BORDER_REPLICATE)[0,0]
  residual=B-A-estimated
  length=float(np.linalg.norm(residual))
  # A single inferred outline landmark may be unreliable. Restrict the
  # physical correction while retaining image-driven local texture flow.
  cap=24 if len(anchors)>1 else 38
  if length>cap:residual*=cap/length
  distance=(x-A[0])**2+(y-A[1])**2
  factor=np.exp(-distance/(2*radius*radius))
  corr+=factor[:,:,None]*residual
  weight+=factor
  residuals.append(float(np.linalg.norm(residual)))
 # Blend physical anchor residuals with original DIS where support is weak.
 strength=np.minimum(weight,1.0)
 normalized=corr/np.maximum(weight[:,:,None],1e-5)
 corrected=flow+normalized*strength[:,:,None]
 return corrected,{"controls":len(anchors),
     "meanResidual":round(float(np.mean(residuals)),3),
     "radius":round(float(radius),2)}

def forward_backward_confidence(fwd,rev):
 gridx,gridy=np.meshgrid(np.arange(CANVAS,dtype=np.float32),
                        np.arange(CANVAS,dtype=np.float32))
 targetx=gridx+fwd[:,:,0]
 targety=gridy+fwd[:,:,1]
 back=cv2.remap(rev,targetx,targety,cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT)
 error=np.sqrt(((fwd+back)**2).sum(axis=2))
 outside=((targetx<0)|(targetx>=CANVAS)|(targety<0)|(targety>=CANVAS))
 score=np.exp(-np.clip(error,0,50)/11.0)
 score[outside]=0.0
 return score.astype(np.float32),float(np.mean(error)),float(np.mean(outside))

def schedule_visibility(sid,a,b,angle):
 slot=(a,b,sid)
 if slot in HIDE_WINDOWS:
  lo,hi=HIDE_WINDOWS[slot]
  return float(1-smoothstep(angle,lo,hi))
 return float(1-(angle-a)/(b-a))

def output_frame_id(angle):
 return "yaw"+(str(int(angle)) if float(angle).is_integer()
               else str(angle).replace(".","p"))+".png"

def source_composite(samples,slots,ids,key,angle,cache,grid,mode):
 src=cache[key]
 with Image.open(src) as original:
  original_rgba=np.asarray(original.convert("RGBA"))
 if angle==key:
  return original_rgba
 return None

def render(root,out,angles,mode="confidence",publish_layers=False):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((root/"p5-see-through/mv-candidate/parts.json").read_text())
 landmark=json.loads((root/"p5-see-through/mv-candidate/landmark-qa.json").read_text())
 if manifest["characterId"]!="p0_character_001" or landmark["characterId"]!="p0_character_001":
  raise ValueError("Approved P0 identity mismatch")
 slots={(p["yawDeg"],p["semanticId"]):p for p in manifest["parts"]}
 ids=[x["semanticId"] for x in manifest["parts"] if x["yawDeg"]==0]
 assert len(slots)==39 and len(ids)==13 and len(set(ids))==13
 sources={}
 for entry in manifest["wholeViews"]:
  path=root/entry["path"]
  if sha(path)!=entry["sha256"]:raise ValueError("P0 original view SHA mismatched")
  sources[entry["yawDeg"]]=path
 assert set(sources)=={0,45,90}
 samples={}
 for yaw in KEYS:
  for role in ids:
   ent=slots[yaw,role]
   file=root/ent["path"]
   if sha(file)!=ent["frameSha256"]:raise ValueError("Source P0 part hash mismatch")
   samples[yaw,role]=part_to_native(file)
 gx,gy=np.meshgrid(np.arange(CANVAS,dtype=np.float32),
                   np.arange(CANVAS,dtype=np.float32))
 grid=np.stack([gx,gy],axis=2)
 match={}
 diagnostics={}
 for a,b in ((0,45),(45,90)):
  for role in ids:
   ea=slots[a,role];eb=slots[b,role]
   if not (is_visible(ea) and is_visible(eb)):
    match[a,b,role]=None
    continue
   sA=native_to_rgba(samples[a,role])
   sB=native_to_rgba(samples[b,role])
   forward,reverse=get_flow(sA,sB,mode="dis")
   anchors=tracked(landmark,role,a,b) if mode not in ("selective","profile") or role in FACE_CONTROLS else []
   fa,metricsA=residual_guidance(forward,anchors,samples[a,role][:,:,3],ea["bbox"])
   backanchors=[(name,B,A) for name,A,B in anchors]
   fb,metricsB=residual_guidance(reverse,backanchors,samples[b,role][:,:,3],eb["bbox"])
   reliabilityA,errA,outA=forward_backward_confidence(fa,fb)
   reliabilityB,errB,outB=forward_backward_confidence(fb,fa)
   match[a,b,role]=(fa,fb,reliabilityA,reliabilityB)
   diagnostics[f"{a}-{b}/{role}"]={
    "originalRGBAsha":[ea["frameSha256"],eb["frameSha256"]],
    "physicalAnchorCount":len(anchors),
    "sourceResidual":metricsA,
    "targetResidual":metricsB,
    "forwardReverseFlowMeanError":[round(errA,3),round(errB,3)],
    "mappedOutsideRatio":[round(outA,4),round(outB,4)],
    "meanReliability":[round(float(reliabilityA.mean()),4),
                       round(float(reliabilityB.mean()),4)]}
 records=[];snapshots={};sourceLayerCount=0
 for angle in angles:
  if angle in KEYS:
   with Image.open(sources[angle]) as im:
    full=np.asarray(im.convert("RGBA"))
  else:
   a,b=(0,45) if angle<45 else (45,90)
   t=(angle-a)/(b-a)
   whole=np.zeros((CANVAS,CANVAS,4),dtype=np.uint8)
   ordered=sorted(ids,key=lambda sid:slots[a,sid]["depthOrder"])
   for sid in ordered:
    A=slots[a,sid];B=slots[b,sid]
    pa,pb=samples[a,sid],samples[b,sid]
    matchdata=match[a,b,sid]
    if matchdata is not None:
     fa,fb,confA,confB=matchdata
     xa=gx-t*fa[:,:,0];ya=gy-t*fa[:,:,1]
     xb=gx-(1-t)*fb[:,:,0];yb=gy-(1-t)*fb[:,:,1]
     wa=cv2.remap(pa,xa,ya,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
     wb=cv2.remap(pb,xb,yb,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
     ca=cv2.remap(confA,xa,ya,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
     cb=cv2.remap(confB,xb,yb,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
     if mode=="profile" and a==45:
      # Warp the true 90-degree source earlier into view. Crossfade
      # through a narrow interval with physically corrected per-part
      # flow so that 72.5 degrees has a single side-view texture.
      sideWeight=smoothstep(t,0.30,0.55)
      merged=wa*(1-sideWeight)+wb*sideWeight
     elif mode=="selective" and sid not in FACE_CONTROLS:
      if a==45:
       if t<=0.5: merged=wa
       elif t>=0.7: merged=wb
       else:
        blend=smoothstep(t,0.5,0.7)
        merged=wa*(1-blend)+wb*blend
      else:
       merged=wa*(1-t)+wb*t
     elif mode in ("confidence","selective","profile"):
      # Bias color selection to physically consistent flow. Prefer the
      # locally visible source around disocclusion boundaries.
      reliA=(0.20+0.80*ca)*np.maximum(wa[:,:,3],0)
      reliB=(0.20+0.80*cb)*np.maximum(wb[:,:,3],0)
      colorDifference=np.abs(wa[:,:,:3]-wb[:,:,:3]).mean(axis=2)
      # Confidence against cross-view double lines, without forfeiting
      # the 45/90 endpoint source transition.
      contradictory=np.clip((colorDifference-0.09)/0.30,0,1)
      preferred=smoothstep(t,0.40,0.67) if a==45 else smoothstep(t,0.27,0.73)
      directional=(1-contradictory)*t+contradictory*preferred
      weightA=(1-directional)*reliA
      weightB=directional*reliB
      facB=weightB/np.maximum(weightA+weightB,1e-5)
      facB=np.clip(facB,0,1)
      merged=wa*(1-facB[:,:,None])+wb*facB[:,:,None]
     else:
      merged=wa*(1-t)+wb*t
    elif is_visible(A):
     fade=schedule_visibility(sid,a,b,angle)
     merged=pa*fade
    elif is_visible(B):
     fade=1-schedule_visibility(sid,a,b,angle)
     merged=pb*fade
    else:
     continue
    rendered=native_to_rgba(merged)
    whole=alpha_over(whole,rendered)
    sourceLayerCount+=1
    if publish_layers:
     dest=out/"layers"/str(angle).replace(".","p")
     dest.mkdir(parents=True,exist_ok=True)
     Image.fromarray(rendered,"RGBA").save(dest/(sid+".png"))
   full=np.asarray(Image.fromarray(whole,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS))
  frame=out/output_frame_id(angle)
  Image.fromarray(full,"RGBA").save(frame)
  records.append({"angle":angle,"path":str(frame.relative_to(root)),
                  "sha256":sha(frame),"isOriginalView":angle in KEYS})
  if angle in DEFAULT_ANGLES:snapshots[float(angle)]=Image.fromarray(full,"RGBA")
 contact=Image.new("RGB",(320*5,354),(31,41,57))
 draw=ImageDraw.Draw(contact)
 for index,angle in enumerate(DEFAULT_ANGLES):
  source=snapshots.get(float(angle))
  if source is None:continue
  matte=Image.new("RGBA",source.size,(48,62,82,255))
  matte.alpha_composite(source)
  contact.paste(matte.convert("RGB").resize((320,320),Image.Resampling.LANCZOS),(index*320,0))
  draw.text((index*320+15,331),str(angle)+"°",fill="white")
 contactpath=out/"semantic-occlusion-contact.jpg"
 contact.save(contactpath,quality=94)
 qa={
  "schema":"KOMA-P0-P8-SEMANTIC-PHYSICAL-TEXEL-MAPPING-V1",
  "characterId":"p0_character_001",
  "registeredArtMeshViews":len(slots),
  "sourceAngles":list(KEYS),"sourcePSDViews":[0,45],
  "flowGrid":[CANVAS,CANVAS],
  "outputRGBAResolution":[1024,1024],
  "mode":mode,
  "algorithm":"per-semantic DIS + physical-anchor residuals + forward/reverse visibility confidence",
  "translucency":"premultiplied RGBA; original P0 author keyviews immutable",
  "occlusionWindows":[{"pair":[a,b],"semanticId":sid,"visibilityWindow":[lo,hi]}
     for (a,b,sid),(lo,hi) in HIDE_WINDOWS.items()],
  "inputRegistrySHA256":sha(root/"p5-see-through/mv-candidate/parts.json"),
  "inputLandmarksSHA256":sha(root/"p5-see-through/mv-candidate/landmark-qa.json"),
  "pairDiagnostics":diagnostics,
  "angles":angles,"frameCount":len(records),"frames":records,
  "contactImage":str(contactpath.relative_to(root)),
  "contactSHA256":sha(contactpath),
  "artisticAcceptance":"PENDING_INDEPENDENT_ORIGINAL_VIEW_INSPECTION"
 }
 (out/"qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":"P8_ORIGINAL_RGBA_CORRESPONDENCE_RENDERED",
                   "frames":len(records),
                   "sourceLayers":len(slots),
                   "mode":mode,
                   "registeredValidPairs":len(diagnostics),
                   "contactSHA256":sha(contactpath)},ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--angles",default=",".join(map(str,DEFAULT_ANGLES)))
 p.add_argument("--mode",choices=["confidence","linear","selective","profile"],default="confidence")
 p.add_argument("--write-layers",action="store_true")
 args=p.parse_args()
 render(args.root,args.out,[float(x) for x in args.angles.split(",")],args.mode,args.write_layers)
