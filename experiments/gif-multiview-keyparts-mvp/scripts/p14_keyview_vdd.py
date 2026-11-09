#!/usr/bin/env python3
"""P14 P0 five-keyview ArtMesh VDD using original source and painted candidates.

Sources: approved P0 authored 0/45/90°, P14 painted 67.5/72.5°
candidate full-resolution 13-part RGBA, exact per-keyframe SHA-256.
Correspondence: per-semantic DIS (443px) and 1024px alpha-premultiplied
bidirectional resampling. No substitute texture or learned image fill.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from flow_render import get_flow
from p7_semantic_dense_flow import part_to_native,native_to_rgba
from p8_semantic_occlusion import output_frame_id

SOURCE_KEYS=(0,45,67.5,72.5,90)
INTERVALS=((45,67.5),(67.5,72.5),(72.5,90))
W=1024
G=443

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def load(file):return json.loads(Path(file).read_text(encoding="utf8"))

def register(root):
 p0=load(root/"p5-see-through/mv-candidate/parts.json")
 p14a=load(root/"p14-authored-candidates/yaw067p5-artmesh/qa.json")
 p14b=load(root/"p14-authored-candidates/yaw072p5-artmesh/qa.json")
 p11=load(root/"p11-profile-psd/yaw090/qa.json")
 baseline=load(root/"p8-semantic-occlusion/selective-sequence/qa.json")
 if any(x["characterId"]!="p0_character_001" for x in (p0,p14a,p14b,p11,baseline)):
  raise ValueError("Source P0 approved character lineage mismatch")
 if (p14a["layerCount"],p14b["semanticLayerCount"],baseline["frameCount"])!=(13,13,37):
  raise ValueError("Original and painted 13-source semantic ArtMeshes incomplete")
 if sha(root/p11["psdPath"])!=p11["psdSHA256"]:
  raise ValueError("Original P0 profile PSD source changed")
 layer={};keys={};source_keys={}
 for entry in p0["wholeViews"]:
  angle=entry["yawDeg"];f=root/entry["path"]
  if sha(f)!=entry["sha256"]:raise ValueError("Approved original P0 keyview SHA differs")
  keys[float(angle)]=(f,entry["sha256"])
  source_keys[float(angle)]="P0_APPROVED_ORIGINAL"
 roleorder=[p["semanticId"] for p in p0["parts"] if p["yawDeg"]==45]
 assert len(roleorder)==13 and len(set(roleorder))==13
 for part in p0["parts"]:
  if part["yawDeg"] not in (45,90):continue
  angle=float(part["yawDeg"])
  f=root/part["path"]
  if sha(f)!=part["frameSha256"]:raise ValueError("Original semantic source SHA changed "+part["semanticId"])
  layer[angle,part["semanticId"]]=(f,part["frameSha256"])
 for angle,qa,records,pathkey in (
  (67.5,p14a,p14a["parts"],"composite"),
  (72.5,p14b,p14b["semanticLayerRecords"],"composite")
 ):
  item=qa[pathkey];keyfile=root/item["path"]
  if sha(keyfile)!=item["sha256"]:raise ValueError("Painted P0 source composite changed")
  keys[angle]=(keyfile,item["sha256"])
  source_keys[angle]="P14_INDEPENDENT_GENERATED_AND_ARTMESH_REGISTERED_CANDIDATE"
  found=set()
  for part in records:
   sid=part["semanticId"]
   if sid in found:raise ValueError("Duplicate painted P0 semantic part "+sid)
   found.add(sid)
   file=root/part["path"]
   signature=part["sha256"]
   if sha(file)!=signature:raise ValueError("Painted original source semantic SHA differs")
   layer[angle,sid]=(file,signature)
  if found!=set(roleorder):raise ValueError("Painted P0 original semantic identity coverage incomplete")
 assert set(keys)=={0,45,67.5,72.5,90}
 return keys,layer,roleorder,source_keys,baseline

def interpolate_alpha(sourceRGBA,flow,weight,grid):
 full=np.asarray(sourceRGBA,dtype=np.float32)/255
 full[:,:,:3]*=full[:,:,3:4]
 dx=cv2.resize(flow[:,:,0],(W,W),interpolation=cv2.INTER_LINEAR)*(W/G)
 dy=cv2.resize(flow[:,:,1],(W,W),interpolation=cv2.INTER_LINEAR)*(W/G)
 xx,yy=grid
 mx=xx-weight*dx
 my=yy-weight*dy
 warp=cv2.remap(full,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 return warp

def choose_overlay(wa,wb,t,method):
 if method=="source-coherent":
  return wa if t<0.5 else wb
 if method=="smooth-ink":
  f=np.clip((t-.32)/.36,0,1)
  f=f*f*(3-2*f)
  return wa*(1-f)+wb*f
 raise ValueError("P14 rendering method invalid: "+method)

def render(root,out,angles,method):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 keys,layers,roles,sourceRole,baseline=register(root)
 xx,yy=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(W,dtype=np.float32))
 grid=(xx,yy)
 textures={}
 flow={}
 for a,b in INTERVALS:
  for role in roles:
   A=layers[a,role][0];B=layers[b,role][0]
   if (a,role) not in textures:
    with Image.open(A) as img:textures[a,role]=np.asarray(img.convert("RGBA")).copy()
   if (b,role) not in textures:
    with Image.open(B) as img:textures[b,role]=np.asarray(img.convert("RGBA")).copy()
   sA=part_to_native(A);sB=part_to_native(B)
   if (np.max(sA[:,:,3])<.005 or np.max(sB[:,:,3])<.005):
    flow[a,b,role]=None
   else:
    fa,fb=get_flow(native_to_rgba(sA),native_to_rgba(sB),mode="dis")
    flow[a,b,role]=(fa,fb)
 p8_frames={float(x["angle"]):x for x in baseline["frames"]}
 rows=[]
 for angle in angles:
  angle=round(float(angle),4)
  if angle in keys:
   file,signature=keys[angle]
   with Image.open(file) as img:
    output=img.convert("RGBA").copy()
   if sha(file)!=signature:raise ValueError("P0 original/source-painted keyframe unexpectedly changed")
   provenance=sourceRole[angle]
  elif angle<45:
   item=p8_frames.get(angle)
   if not item:raise ValueError("P8 source frame needed "+str(angle))
   file=root/item["path"]
   if sha(file)!=item["sha256"]:
    raise ValueError("Previously QA-verified P8 original RGBAs changed")
   with Image.open(file) as image:output=image.convert("RGBA").copy()
   provenance="P8_APPROVED_SOURCE_DERIVED_ANIMATION"
  else:
   a,b=next(((a,b) for a,b in INTERVALS if a<angle<b), (None,None))
   if a is None:raise ValueError("Requested angle not bracketed by source artworks "+str(angle))
   t=(angle-a)/(b-a)
   output=Image.new("RGBA",(W,W),(0,0,0,0))
   for role in roles:
    sourceA=textures[a,role];sourceB=textures[b,role]
    maps=flow[a,b,role]
    if maps is None:
     if int(sourceA[:,:,3].max())<=1:
      rgba=sourceB.copy()
      rgba[:,:,3]=np.rint(rgba[:,:,3].astype(float)*t).astype(np.uint8)
     elif int(sourceB[:,:,3].max())<=1:
      rgba=sourceA.copy()
      rgba[:,:,3]=np.rint(rgba[:,:,3].astype(float)*(1-t)).astype(np.uint8)
     else:
      rgba=np.zeros_like(sourceA)
    else:
     wa=interpolate_alpha(sourceA,maps[0],t,grid)
     wb=interpolate_alpha(sourceB,maps[1],1-t,grid)
     merged=choose_overlay(wa,wb,t,method)
     rgba=native_to_rgba(merged)
    output.alpha_composite(Image.fromarray(rgba,"RGBA"))
   provenance="P14_P0_KEYVIEW_SEMANTIC_VDD"
  result=out/output_frame_id(angle)
  output.save(result)
  rows.append({"angle":angle,"path":str(result.relative_to(root)),
               "sha256":sha(result),"bytes":result.stat().st_size,
               "sourceType":provenance})
 contact=Image.new("RGB",(6*280,310),(33,45,59))
 draw=ImageDraw.Draw(contact)
 for i,angle in enumerate((0,22.5,45,67.5,72.5,90)):
  frame=out/output_frame_id(angle)
  if not frame.is_file():continue
  with Image.open(frame) as img:
   base=Image.new("RGBA",img.size,(48,62,81,255))
   base.alpha_composite(img.convert("RGBA"))
  contact.paste(base.convert("RGB").resize((280,280),Image.Resampling.LANCZOS),(i*280,0))
  draw.text((i*280+9,288),f"{angle}° · {method}",fill="white")
 contact_file=out/"p14-p0-keyview-vdd-contact.jpg"
 contact.save(contact_file,quality=93)
 qa={
  "schema":"KOMA-P0-P14-PAINTED-KEYVIEW-ARTMESH-VDD-V1",
  "characterId":"p0_character_001",
  "originalKeyAngles":[0,45,90],
  "paintedCandidateKeyAngles":[67.5,72.5],
  "semanticIDs":roles,
  "semanticComponentCount":13,
  "sourceKeyViews":{str(y):{"path":str(p.relative_to(root)),"sha256":signature,
                          "source":sourceRole[y]} for y,(p,signature) in keys.items()},
  "sourceOriginalArtMeshRegistrySHA256":sha(root/"p5-see-through/mv-candidate/parts.json"),
  "sourcePainted67QA_SHA256":sha(root/"p14-authored-candidates/yaw067p5-artmesh/qa.json"),
  "sourcePainted72QA_SHA256":sha(root/"p14-authored-candidates/yaw072p5-artmesh/qa.json"),
  "nativeRGBA":[1024,1024],
  "bidirectionalFlowCanvas":[443,443],
  "method":method,
  "frameCount":len(rows),"frames":rows,
  "contactPath":str(contact_file.relative_to(root)),
  "contactSHA256":sha(contact_file),
  "visualAcceptance":"PENDING_P0_ORIGINAL_VIEW_CHARACTER_ART_REVIEW",
  "motionAcceptance":"PENDING_TEMPORAL_AND_TEXTURE_QA",
  "status":"P14_SOURCE_PAINTED_KEYVIEW_ANIMATION_RENDERED"
 }
 (out/"qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":qa["status"],"mode":method,"registeredFrames":len(rows),
                  "authoredSourceKeys":qa["originalKeyAngles"],
                  "paintedCandidateKeys":qa["paintedCandidateKeyAngles"],
                  "contactSHA256":qa["contactSHA256"]},ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--root",required=True)
 ap.add_argument("--out",required=True)
 ap.add_argument("--method",choices=["source-coherent","smooth-ink"],default="smooth-ink")
 ap.add_argument("--angles",default=",".join(str(i*2.5) for i in range(37)))
 x=ap.parse_args()
 render(x.root,x.out,[float(v) for v in x.angles.split(",")],x.method)
