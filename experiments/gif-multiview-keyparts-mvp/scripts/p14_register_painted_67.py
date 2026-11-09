#!/usr/bin/env python3
"""Register the painted P0 67.5-degree RGB artwork as 13 native RGBA ArtMeshes.

Part ownership is initialized from the approved P0 90° source semantic
ArtMeshes using DIS reverse flow and refined by one-eye/ear face anatomy.
The independently generated character pixels remain immutable; splitting
owns every foreground pixel once, including its already painted ahoge.
"""
import argparse, hashlib, json
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw
from flow_render import get_flow
from p14_semantic_reproject import assign_labels,coords_from_target,source_as_RGBA
from p1_front_semantic import alpha_over

W=1024; GRID=443
HIDDEN={"eye.far","ear.far","hair.clip.cross_gold"}

def sha(f):
 h=hashlib.sha256()
 with Path(f).open("rb") as fp:
  for chunk in iter(lambda:fp.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def load(f):return json.loads(Path(f).read_text(encoding="utf8"))

def ahoge_owner(target):
 a=target[:,:,3]
 mask=(a>5).astype(np.uint8)
 clip=np.zeros_like(mask)
 clip[:108,395:650]=mask[:108,395:650]
 n,labels,stats,_=cv2.connectedComponentsWithStats(clip,8)
 eligible=[]
 for i in range(1,n):
  x,y,w,h,count=map(int,stats[i])
  if count>=220 and y<=42 and 405<x<620 and x+w>515:
   eligible.append((count,i))
 if not eligible:raise ValueError("P0 candidate ahoge cannot be isolated from source art")
 idx=max(eligible)[1]
 member=(labels==idx)
 # Follow the original loop attachment only within the expected hair root.
 root_region=np.zeros_like(mask)
 root_region[92:130,555:614]=mask[92:130,555:614]
 dil=cv2.dilate(member.astype(np.uint8),np.ones((7,7),np.uint8),iterations=2)>0
 member|=(root_region>0)&dil
 if int(member.sum())<1000:raise ValueError("Candidate P0 ahoge is incomplete")
 return member

def render(root,out):
 root=Path(root).resolve();out=Path(out).resolve()
 out.mkdir(parents=True,exist_ok=True)
 p0=load(root/"p5-see-through/mv-candidate/parts.json")
 p11=load(root/"p11-profile-psd/yaw090/qa.json")
 occlusion=load(root/"p14-authored-candidates/yaw067p5-occlusion-retouched.qa.json")
 if any(x["characterId"]!="p0_character_001" for x in (p0,p11,occlusion)):
  raise ValueError("Original P0 character source identity differs")
 if sha(root/p11["psdPath"])!=p11["psdSHA256"]:
  raise ValueError("P0 canonical profile PSD SHA mismatch")
 whole=next(x for x in p0["wholeViews"] if x["yawDeg"]==90)
 master=root/whole["path"]
 if sha(master)!=whole["sha256"]:
  raise ValueError("Original 90 degree author keyframe changed")
 rgb_file=root/occlusion["occlusionAlignedRGB"]["path"]
 matte_file=root/"p14-authored-candidates/yaw067p5-qwen2511-occlusion-retouched-rgba.png"
 matte_qa=load(matte_file.with_suffix(".qa.json"))
 if sha(rgb_file)!=occlusion["occlusionAlignedRGB"]["sha256"] or sha(matte_file)!=matte_qa["outputPNG_SHA256"]:
  raise ValueError("Generated P0 source painting / matte changed")
 target=source_as_RGBA(matte_file)
 master_rgb=source_as_RGBA(master)
 original_parts=sorted((x for x in p0["parts"] if x["yawDeg"]==90),
                      key=lambda x:x["depthOrder"])
 if len(original_parts)!=13:raise ValueError("P0 semantic components incomplete")
 base=cv2.resize(master_rgb,(GRID,GRID),interpolation=cv2.INTER_AREA)
 view=cv2.resize(target,(GRID,GRID),interpolation=cv2.INTER_AREA)
 _,reverse=get_flow(base,view,mode="dis")
 mx,my=coords_from_target(W,W,reverse)
 predictions=[]
 for p in original_parts:
  f=root/p["path"]
  if sha(f)!=p["frameSha256"]:raise ValueError("Original P0 semantic SHA changed "+p["semanticId"])
  if p["semanticId"] in HIDDEN or p["semanticId"]=="hair.ahoge":
   predictions.append(np.zeros((W,W),dtype=np.float32))
  else:
   alpha=source_as_RGBA(f)[:,:,3].astype(np.float32)/255
   predictions.append(cv2.remap(alpha,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT))
 roles=[x["semanticId"] for x in original_parts]
 labels,nearfallback=assign_labels(predictions,roles,target[:,:,3],target[:,:,:3])
 ahoge=ahoge_owner(target)
 labels[ahoge]=roles.index("hair.ahoge")
 foreground=(target[:,:,3]>0)
 if int(np.count_nonzero((labels<0)&foreground))!=0:
  raise ValueError("Semantic mapping lost independently painted P0 foreground")
 result=Image.new("RGBA",(W,W),(0,0,0,0))
 records=[]
 for i,p in enumerate(original_parts):
  rgba=target.copy()
  rgba[(labels!=i) | (~foreground)]=0
  if p["semanticId"] in HIDDEN:
   rgba[:]=0
  f=out/"layers"/(p["semanticId"]+".png")
  f.parent.mkdir(parents=True,exist_ok=True)
  Image.fromarray(rgba,"RGBA").save(f)
  alpha=rgba[:,:,3]
  record={
   "yaw":67.5,
   "characterId":"p0_character_001","semanticId":p["semanticId"],
   "depthOrder":p["depthOrder"],"reference90Visibility":p["visibility"],
   "referenceOriginal90SHA256":p["frameSha256"],
   "registeredNativeCanvas":[1024,1024],
   "paintingSourceSHA256":sha(rgb_file),
   "path":str(f.relative_to(root)),
   "sha256":sha(f),
   "visibleAlphaPixels":int(np.count_nonzero(alpha>0)),
   "partialAlphaPixels":int(np.count_nonzero((alpha>0)&(alpha<255))),
   "origin":"QWEN2511_ANIME_EDIT_P0_SOURCE_PAINTING"
  }
  records.append(record)
  result.alpha_composite(Image.fromarray(rgba,"RGBA"))
 comp=out/"yaw067p5-painted-semantic-composite.png"
 result.save(comp)
 expected=target.astype(np.int16);actual=np.asarray(result).astype(np.int16)
 valid=target[:,:,3]>0
 alphaerr=int(np.abs(actual[:,:,3]-expected[:,:,3]).max())
 rgberr=int(np.abs(actual[:,:,:3][valid]-expected[:,:,:3][valid]).max())
 if alphaerr!=0 or rgberr>0:
  raise ValueError(f"P0 13-part painted image reconstruction differs alpha={alphaerr} rgb={rgberr}")
 # visual side-by-side source-to-new paint and final 13 native layers
 contact=Image.new("RGB",(4*340,382),(32,46,63))
 draw=ImageDraw.Draw(contact)
 right72=root/"p14-authored-candidates/yaw072p5-artmesh/yaw072p5-p0-source-mapped-artmesh.png"
 cells=[(master,"P0 original 90°"),(matte_file,"Painted 67.5° RGBA"),
        (comp,"67.5° / 13 ArtMesh"),(right72,"Painted 72.5° / 13 ArtMesh")]
 for i,(f,label) in enumerate(cells):
  with Image.open(f) as src:
   clean=Image.new("RGBA",src.size,(48,62,81,255))
   clean.alpha_composite(src.convert("RGBA"))
  contact.paste(clean.convert("RGB").resize((340,340),Image.Resampling.LANCZOS),(i*340,0))
  draw.text((i*340+8,353),label,fill="white")
 contactfile=out/"p14-67-72-artmesh-contact.jpg"
 contact.save(contactfile,quality=94)
 source_cov=int((foreground & (np.max(np.stack(predictions,axis=0),axis=0)>.11)).sum())
 qa={
  "schema":"KOMA-P0-P14-PAINTED-67P5-SEMANTIC-ARTMESH-V1",
  "characterId":"p0_character_001","candidateAngle":67.5,
  "originalSourceP0Angles":[0,45,90],
  "originalSource90SHA256":whole["sha256"],
  "profilePSD_SHA256":p11["psdSHA256"],
  "originalArtMeshViewSlots":39,
  "independentPaintedRGB":{"path":str(rgb_file.relative_to(root)),"sha256":sha(rgb_file)},
  "originalRGBA":{"path":str(matte_file.relative_to(root)),"sha256":sha(matte_file)},
  "sourceInkOcclusionQA_SHA256":sha(root/"p14-authored-candidates/yaw067p5-occlusion-retouched.qa.json"),
  "nativeCanvas":[W,W],"sourceSemanticMethod":"P0 90-degree source semantic ownership using reverse DIS and explicit near-feature segmentation",
  "layerCount":len(records),"parts":records,
  "ahogePaintedPixels":int(ahoge.sum()),
  "sourceRegistrationCoverageFraction":round(source_cov/max(1,int(foreground.sum())),5),
  "nearestKnownOwnerPixelCount":nearfallback,
  "composite":{"path":str(comp.relative_to(root)),"sha256":sha(comp)},
  "referenceContact":{"path":str(contactfile.relative_to(root)),"sha256":sha(contactfile)},
  "alphaRecompositionMaxDifference":alphaerr,
  "visibleRGBRecompositionMaxDifference":rgberr,
  "status":"P14_INTERMEDIATE_PAINTED_SOURCE_SEMANTIC_CANDIDATE_REGISTERED",
  "viewAngleApproval":"PENDING_SOURCE_P0_67P5_ARTISTIC_REVIEW",
  "artisticApproval":"PENDING"
 }
 (out/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"status":qa["status"],"angle":67.5,"parts":len(records),
  "ahogePixels":qa["ahogePaintedPixels"],
  "visibleRGBMaxDifference":rgberr,"alphaMaxDifference":alphaerr,
  "sourceCoverage":qa["sourceRegistrationCoverageFraction"],
  "contactSha256":qa["referenceContact"]["sha256"]},ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",required=True)
 parser.add_argument("--out",required=True)
 args=parser.parse_args()
 render(args.root,args.out)
