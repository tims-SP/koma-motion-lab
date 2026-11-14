#!/usr/bin/env python3
"""P12 source-grounded semantic disocclusion atlas for authentic P0 views.

Registers observed 0°/45°/90° P0 original RGBA parts; masks record
which target-visible pixels lack aligned source texels under per-part
DIS correspondence and P5 physical anchors. This is an engineering
asset-sufficiency diagnostic, not proof that every changed pixel needs art.
"""
import argparse,json,hashlib
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from p7_semantic_dense_flow import part_to_native,native_to_rgba,CANVAS
from flow_render import get_flow
from p8_semantic_occlusion import tracked,sha as source_sha

PAIR=(45,90)
ALPHA_THRESHOLD=.64

def mask_of(native):
 return (native[:,:,3]>=ALPHA_THRESHOLD).astype(np.uint8)

def aligned_mask(source_native,target_native,role,landmarks):
 # Original P0 semantic part identity is authoritative; warp the
 # original source alpha into the target's native 443px reference space.
 fa,fb=get_flow(native_to_rgba(source_native),
                native_to_rgba(target_native),mode="dis")
 landmarks_2=tracked(landmarks,role,45,90)
 x,y=np.meshgrid(np.arange(CANVAS,dtype=np.float32),
                 np.arange(CANVAS,dtype=np.float32))
 if role in ("eye.near","nose","mouth","ear.near") and len(landmarks_2)==1:
  _,origin,dest=landmarks_2[0]
  # source position for target pixel based on original 90° physical feature.
  delta=(origin-dest).astype(np.float32)
  target_source_x=x+delta[0]
  target_source_y=y+delta[1]
  method="physical-landmark-translation"
 else:
  target_source_x=x+fb[:,:,0]
  target_source_y=y+fb[:,:,1]
  method="reverse-DIS-original-layer"
 predicted=cv2.remap(source_native,target_source_x,target_source_y,
                     interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT)
 return predicted,method,landmarks_2

def rgba_u8(native):
 return native_to_rgba(native)

def tint(image,under,over,split=False):
 # Make gaps visible without destroying artist's source pixels.
 # Cyan marks target-only newly visible surface; amber marks source-only
 # texels that no longer overlap the target surface after registration.
 base=rgba_u8(image).copy()
 back=np.empty((CANVAS,CANVAS,3),dtype=np.uint8)
 back[:]=(48,62,81)
 alpha=base[:,:,3:4].astype(np.float32)/255.
 dst=(base[:,:,:3].astype(np.float32)*alpha+
      back.astype(np.float32)*(1-alpha)).astype(np.uint8)
 c=(dst.astype(np.float32)*.43).astype(np.uint8)
 dst[under>0]=np.clip(c[under>0]+np.array([30,166,175],np.uint8),0,255)
 dst[over>0]=np.clip(c[over>0]+np.array([170,110,24],np.uint8),0,255)
 return Image.fromarray(dst,"RGB")

def png_union(src,target,newmask,absentmask):
 img=Image.new("RGB",(CANVAS*3,CANVAS+44),(31,42,57))
 dst=ImageDraw.Draw(img)
 for i,(pic,desc) in enumerate((
  (tint(src,np.zeros_like(newmask),np.zeros_like(newmask)),"45° source warped to 90°"),
  (tint(target,np.zeros_like(newmask),np.zeros_like(newmask)),"90° original P0 source"),
  (tint(target,newmask,absentmask),"Cyan: target-only / amber: disappearing")
 )):
  img.paste(pic,(i*CANVAS,0))
  dst.text((i*CANVAS+6,CANVAS+11),desc,fill="#eef5fc")
 return img

def run(root,out):
 root=Path(root).resolve()
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 registryfile=root/"p5-see-through/mv-candidate/parts.json"
 landmarkfile=root/"p5-see-through/mv-candidate/landmark-qa.json"
 p11file=root/"p11-profile-psd/yaw090/qa.json"
 p10file=root/"p10-stroke-identity/qa.json"
 registry=json.loads(registryfile.read_text(encoding="utf8"))
 landmarks=json.loads(landmarkfile.read_text(encoding="utf8"))
 p11=json.loads(p11file.read_text(encoding="utf8"))
 p10=json.loads(p10file.read_text(encoding="utf8"))
 if any(x["characterId"]!="p0_character_001" for x in (registry,landmarks,p11,p10)):
  raise ValueError("P0 semantic identity mismatch")
 if p11["psdSHA256"]!=source_sha(root/p11["psdPath"]):
  raise ValueError("P0 90 degree editable profile PSD SHA invalid")
 slots={(p["yawDeg"],p["semanticId"]):p for p in registry["parts"]}
 assert len(slots)==39
 roles=[x["semanticId"] for x in registry["parts"] if x["yawDeg"]==45]
 issues=[]
 diagnostics=[]
 for role in roles:
  A=slots[45,role];B=slots[90,role]
  entry={"role":role,
    "source45SHA256":A["frameSha256"],"target90SHA256":B["frameSha256"],
    "sourceVisibility":A["visibility"],"targetVisibility":B["visibility"],
    "p10AcceptedStrokePairs":len(p10["pairs"].get("45-90/"+role,{}).get("accepted",[]))}
  for entryPart in (A,B):
   if source_sha(root/entryPart["path"])!=entryPart["frameSha256"]:
    raise ValueError("Source 45/90 P0 part SHA mismatch")
  source=part_to_native(root/A["path"])
  target=part_to_native(root/B["path"])
  sourceMask=mask_of(source);targetMask=mask_of(target)
  originalSource=int(sourceMask.sum());originalTarget=int(targetMask.sum())
  entry["sourceOpaquePixels"]=originalSource
  entry["targetOpaquePixels"]=originalTarget
  if A["visibility"]=="visible" and B["visibility"]=="visible":
   warped,method,controls=aligned_mask(source,target,role,landmarks)
   predictedMask=mask_of(warped)
   intersection=int(np.logical_and(predictedMask,targetMask).sum())
   union=int(np.logical_or(predictedMask,targetMask).sum())
   newly=(targetMask>0)&(predictedMask==0)
   lost=(predictedMask>0)&(targetMask==0)
   entry.update({
    "registrationMethod":method,
    "physicalAnchorCount":len(controls),
    "predictedSourceAlignedOpaquePixels":int(predictedMask.sum()),
    "observedSurfaceIoU":round(intersection/max(1,union),5),
    "targetOnlyPixels":int(newly.sum()),
    "sourceOnlyPixels":int(lost.sum()),
    "targetOnlyFraction":round(float(newly.sum())/max(1,originalTarget),5),
    "sourceOnlyFraction":round(float(lost.sum())/max(1,predictedMask.sum()),5),
    "interpretation":"SOURCE_ALPHA_CORRESPONDENCE_DIAGNOSTIC"
   })
   # 1024 mapped original-painted source and real P0 target for inspection
   plot=png_union(warped,target,newly.astype(np.uint8),lost.astype(np.uint8))
   filename=out/(role+".jpg")
   plot.save(filename,quality=93)
   entry["sourceComparisonPath"]=str(filename.relative_to(root))
   entry["sourceComparisonSHA256"]=source_sha(filename)
   if entry["targetOnlyFraction"]>0.15:
    issues.append({"semanticId":role,"targetOnlyFraction":entry["targetOnlyFraction"],
       "priority":"ARTWORK_CORRESPONDENCE_REVIEW",
       "sourcePixelsSHA256":A["frameSha256"],"targetPixelsSHA256":B["frameSha256"]})
  else:
   entry.update({
    "registrationMethod":"P0_ARTMESH_VISIBILITY",
    "targetOnlyPixels":originalTarget,
    "sourceOnlyPixels":originalSource,
    "targetOnlyFraction":1.0 if originalTarget and not originalSource else 0.0,
    "observedSurfaceIoU":None,
    "interpretation":"SEMANTIC_LAYER_VISIBILITY_CHANGE"
   })
  diagnostics.append(entry)
 issues.sort(key=lambda x:x["targetOnlyFraction"],reverse=True)
 jsonpath=out/"qa.json"
 qa={
  "schema":"KOMA-P0-P12-VIEW-SOURCE-OCCLUSION-GAPS-V1",
  "characterId":"p0_character_001",
  "sourceAngles":[45,90],
  "sourceCanvas":[1024,1024],
  "nativeWarpCanvas":[CANVAS,CANVAS],
  "masterPSDSource90":p11["psdPath"],
  "masterPSDSource90SHA256":p11["psdSHA256"],
  "originalRegistrySHA256":source_sha(registryfile),
  "originalLandmarksSHA256":source_sha(landmarkfile),
  "sourceP10StrokesSHA256":source_sha(p10file),
  "registeredSemanticSlots":39,
  "registeredPairCount":len(diagnostics),
  "gapPriority":issues,
  "parts":diagnostics,
  "meaning":"Target-only masks are source-registration coverage gaps; they are candidates for redraw or more accurate mapping, not verified hidden anatomy.",
  "status":"SOURCE_ASSET_GAP_REGISTERED",
  "artisticAcceptance":"PENDING"
 }
 jsonpath.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps({
  "status":qa["status"],
  "sourceParts":len(diagnostics),
  "highGapRegions":len(issues),
  "priority":[(i["semanticId"],i["targetOnlyFraction"]) for i in issues],
  "source90PSDVerified":True
 },ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 args=p.parse_args()
 run(args.root,args.out)
