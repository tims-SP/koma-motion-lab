#!/usr/bin/env python3
"""P13 paint-source-priority view interpolation, preserving original P0 art.

Original semantic part RGB values come only from P0 authored 45 and 90
degree transparent layers; there is no synthetic painting or stock filler.
This is a falsifiable candidate for avoiding double-ink in 67.5/72.5
holdouts, not independently painted intermediate reference art.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
import p8_semantic_occlusion as p8
from p7_semantic_dense_flow import part_to_native,native_to_rgba,CANVAS
from p1_front_semantic import alpha_over
from flow_render import get_flow

SOURCES=(45,90)
KEYS=(0,45,90)
VISIBILITY_SCHEDULE={
 "body.reference":.64,
 "hair.back":.40,
 "face.skin":.58,
 "ear.near":.51,
 "hair.side":.38,
 "eye.near":.63,
 "nose":.60,
 "mouth":.63,
 "hair.front":.39,
 "hair.ahoge":.43
}
VISIBLE_PARTS={"body.reference","hair.back","face.skin","ear.near","hair.side",
 "eye.near","nose","mouth","hair.front","hair.ahoge"}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as fp:
  for b in iter(lambda:fp.read(1024*1024),b""):h.update(b)
 return h.hexdigest()

def fid(angle):
 return p8.output_frame_id(angle)

def smoothstep(v,a,b):
 x=np.clip((v-a)/(b-a),0,1)
 return x*x*(3-2*x)

def composite(wa,wb,t,role,method,ca,cb):
 center=VISIBILITY_SCHEDULE.get(role,.50)
 if method=="source-staggered":
  # Constant source art ownership per part, with alpha fallthrough to
  # mapped other-source opacity when a sole source lacks coverage.
  q=np.float32(t>=center)
 elif method=="source-feathered":
  q=np.float32(smoothstep(t,center-.085,center+.085))
 elif method=="confidence-source":
  # Graphical source ownership is spatially coherent on a semantic
  # piece, but a short confidence-weighted transition remains.
  q=np.float32(smoothstep(t,center-.13,center+.13))
  ra=(0.2+ca*.8)*wa[:,:,3]
  rb=(0.2+cb*.8)*wb[:,:,3]
  fac=rb/(ra+rb+1e-6)
  fac=cv2.GaussianBlur(fac,(0,0),7.5)
  # Maintain the same keyframe ownership while favoring source parts
  # that actually have alpha/flow confidence.
  influence=np.clip((fac-.5)*.18,-.08,.08)
  q=np.clip(q+influence,0,1)
 else:
  raise ValueError("Unsupported P13 candidate: "+method)
 if method=="source-staggered":
  # Source-conditional copy eliminates duplicate source-line layering.
  chosen=wa if q<.5 else wb
  alt=wb if q<.5 else wa
  # Never fabricate missing target alpha; fallback only to the second
  # authoritative source in a fully transparent mapped target hole.
  result=chosen.copy()
  gaps=result[:,:,3]<0.015
  result[gaps]=alt[gaps]
  return result
 return wa*(1-q if np.isscalar(q) else 1-q[:,:,None])+wb*(q if np.isscalar(q) else q[:,:,None])

def render(root,out,angles,method,write_layers):
 root=Path(root).resolve();out=Path(out).resolve()
 out.mkdir(exist_ok=True,parents=True)
 registryfile=root/"p5-see-through/mv-candidate/parts.json"
 psdfile=root/"p11-profile-psd/yaw090/qa.json"
 registry=json.loads(registryfile.read_text())
 psd=json.loads(psdfile.read_text())
 landmarks=json.loads((root/"p5-see-through/mv-candidate/landmark-qa.json").read_text())
 assert registry["characterId"]==psd["characterId"]==landmarks["characterId"]=="p0_character_001"
 assert psd["sourceReconstructionPixelExact"]
 assert psd["psdSHA256"]==sha(root/psd["psdPath"])
 slots={(i["yawDeg"],i["semanticId"]):i for i in registry["parts"]}
 ids=[x["semanticId"] for x in registry["parts"] if x["yawDeg"]==45]
 assert len(ids)==13 and len(slots)==39
 whole={}
 for v in registry["wholeViews"]:
  f=root/v["path"]
  if sha(f)!=v["sha256"]:raise ValueError("Authored P0 viewpoint changed")
  whole[v["yawDeg"]]=f
 assert set(whole)==set(KEYS)
 pairs={};parts={}
 for role in ids:
  A=slots[45,role];B=slots[90,role]
  sources={}
  for yaw,entry in ((45,A),(90,B)):
   file=root/entry["path"]
   if sha(file)!=entry["frameSha256"]:raise ValueError("Semantic original source hash differs")
   sources[yaw]=part_to_native(file)
  parts[role]=sources
  if A["visibility"]!="visible" or B["visibility"]!="visible":
   pairs[role]=None
   continue
  fwd,reverse=get_flow(native_to_rgba(sources[45]),native_to_rgba(sources[90]),mode="dis")
  local=p8.tracked(landmarks,role,45,90) if role in p8.FACE_CONTROLS else []
  fa,_=p8.residual_guidance(fwd,local,sources[45][:,:,3],A["bbox"])
  fb,_=p8.residual_guidance(reverse,[(n,b,a) for n,a,b in local],sources[90][:,:,3],B["bbox"])
  confA,_,_=p8.forward_backward_confidence(fa,fb)
  confB,_,_=p8.forward_backward_confidence(fb,fa)
  pairs[role]=(fa,fb,confA,confB)
 gx,gy=np.meshgrid(np.arange(CANVAS,dtype=np.float32),
                   np.arange(CANVAS,dtype=np.float32))
 reference=json.loads((root/"p8-semantic-occlusion/selective-sequence/qa.json").read_text())
 original_frames={float(x["angle"]):x for x in reference["frames"]}
 frame_data=[]
 layer_data=[]
 reference_paths={}
 for angle in angles:
  if angle in KEYS:
   with Image.open(whole[angle]) as im:frame=im.convert("RGBA").copy()
   origin="P0_AUTHOR_KEYFRAME"
  elif angle<45:
   reference_frame=original_frames.get(angle)
   if not reference_frame:
    raise ValueError("P8 source-authorized RGBA angle is missing "+str(angle))
   path=root/reference_frame["path"]
   if sha(path)!=reference_frame["sha256"]:raise ValueError("P8 original viewpoint interpolation was altered")
   with Image.open(path) as im:frame=im.convert("RGBA").copy()
   origin="P8_ORIGINAL_SOURCE_BASELINE"
  else:
   t=(angle-45)/45
   display=np.zeros((CANVAS,CANVAS,4),dtype=np.uint8)
   editable_composite=Image.new("RGBA",(1024,1024),(0,0,0,0)) if write_layers and angle in (67.5,72.5) else None
   origin="P0_SOURCE_DERIVED_VDD_CANDIDATE"
   for role in ids:
    A=slots[45,role];B=slots[90,role]
    pa=parts[role][45];pb=parts[role][90]
    pair=pairs[role]
    if pair is not None:
     fa,fb,ca,cb=pair
     xa=gx-t*fa[:,:,0];ya=gy-t*fa[:,:,1]
     xb=gx-(1-t)*fb[:,:,0];yb=gy-(1-t)*fb[:,:,1]
     wa=cv2.remap(pa,xa,ya,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
     wb=cv2.remap(pb,xb,yb,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
     qa=cv2.remap(ca,xa,ya,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
     qb=cv2.remap(cb,xb,yb,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
     merged=composite(wa,wb,t,role,method,qa,qb)
    elif A["visibility"]=="visible":
     faded=p8.schedule_visibility(role,45,90,angle)
     merged=pa*faded
    elif B["visibility"]=="visible":
     faded=1-p8.schedule_visibility(role,45,90,angle)
     merged=pb*faded
    else:
     # A semantic identity remains registered with a fully transparent
     # native RGBA layer when both approved source views hide the part.
     merged=np.zeros_like(pa)
    output=native_to_rgba(merged)
    display=alpha_over(display,output)
    if write_layers and angle in (67.5,72.5):
     # Source arrays use premultiplied RGB, so resize the premultiplied
     # semantic layer before un-premultiplication to prevent dark fringes.
     large=Image.fromarray(native_to_rgba(
       cv2.resize(merged,(1024,1024),interpolation=cv2.INTER_LINEAR)),"RGBA")
     editable_composite.alpha_composite(large)
     folder=out/"layers"/("yaw"+str(angle).replace(".","p"))
     folder.mkdir(exist_ok=True,parents=True)
     part_path=folder/(role+".png")
     large.save(part_path)
     layer_data.append({"angle":angle,"semanticId":role,
       "source45SHA256":A["frameSha256"],"source90SHA256":B["frameSha256"],
       "visibilityAt45":A["visibility"],"visibilityAt90":B["visibility"],
       "mode":method,"path":str(part_path.relative_to(root)),
       "sha256":sha(part_path),"canvas":[1024,1024]})
   frame=editable_composite if editable_composite is not None else Image.fromarray(display,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS)
  destination=out/fid(angle)
  frame.save(destination)
  frame_data.append({"angle":angle,"path":str(destination.relative_to(root)),
    "sha256":sha(destination),"sourceType":origin})
  if angle in (22.5,67.5,72.5):reference_paths[str(angle)]=str(destination.relative_to(root))
 pic=Image.new("RGB",(5*320,362),(32,43,58));draw=ImageDraw.Draw(pic)
 for ix,angle in enumerate((0,22.5,45,67.5,90)):
  target=out/fid(angle)
  with Image.open(target) as im:
   canvas=Image.new("RGBA",(1024,1024),(48,64,83,255))
   canvas.alpha_composite(im.convert("RGBA"))
   image=canvas.convert("RGB").resize((320,320),Image.Resampling.LANCZOS)
  pic.paste(image,(ix*320,0))
  draw.text((ix*320+10,335),f"{angle}° · P0 source-derived",fill="white")
 contact=out/"p13-source-priority-contact.jpg"
 pic.save(contact,quality=92)
 meta={
  "schema":"KOMA-P0-P13-SOURCE-OWNERSHIP-VDD-TRIAL-V1",
  "characterId":"p0_character_001",
  "sourceAuthoredAngles":[0,45,90],
  "sourceP0ArtMeshViewSlots":39,
  "sourceEditablePSDViews":[0,45,90],
  "profilePSD_SHA256":psd["psdSHA256"],
  "sourcePartRegistrySHA256":sha(registryfile),
  "motionMode":method,"sourceViewHandoff":VISIBILITY_SCHEDULE,
  "canvas":[1024,1024],
  "frames":frame_data,"frameCount":len(frame_data),
  "semanticLayers":layer_data,"semanticLayerCount":len(layer_data),
  "expectedSemanticSlotsPerIntermediateAngle":13,
  "registeredIntermediateAngles":[67.5,72.5],
  "contactPath":str(contact.relative_to(root)), "contactSHA256":sha(contact),
  "assetStatus":"AUTHORED_SOURCE_DERIVED_INTERMEDIATE_CANDIDATE",
  "artisticAcceptance":"PENDING_VALIDATED_VIEW_TEXTURE_AND_OCCLUSION"
 }
 (out/"qa.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"mode":method,"frames":len(frame_data),"nativeSemanticLayers":len(layer_data),
                   "contactSHA256":meta["contactSHA256"]},ensure_ascii=False,indent=2))
 return meta

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--mode",choices=["source-staggered","source-feathered","confidence-source"],default="source-feathered")
 p.add_argument("--angles",default=",".join(str(x*2.5) for x in range(37)))
 p.add_argument("--write-layers",action="store_true")
 a=p.parse_args()
 render(a.root,a.out,[float(x) for x in a.angles.split(",")],a.mode,a.write_layers)
