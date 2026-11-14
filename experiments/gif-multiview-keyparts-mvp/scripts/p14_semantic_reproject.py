#!/usr/bin/env python3
"""P14 source-matched semantic separation of newly painted 72.5° P0 artwork.

A mature DIS bidirectional flow maps the 90° approved original P0 ArtMesh
ownership into the independently edited candidate. Each source-drawn
pixel is assigned to a single named RGBA part. The approved original
ahoge is retained as its own source-aligned transparent layer.

This is artwork *registration* for human review, not approval of the
independently generated character identity or animation motion.
"""
import argparse,hashlib,json
from pathlib import Path

import cv2,numpy as np
from PIL import Image,ImageDraw
from flow_render import get_flow
from p8_semantic_occlusion import TRACKS
from p1_front_semantic import alpha_over

CANVAS=1024;FLOW_GRID=443
NO_VISIBLE_AT_90={"ear.far","eye.far","hair.clip.cross_gold"}
AHOGE="hair.ahoge"
REGISTRATION_TH=0.11

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def load(p):
 return json.loads(Path(p).read_text(encoding="utf8"))

def source_as_RGBA(path):
 with Image.open(path) as pic:
  if pic.mode!="RGBA" or pic.size!=(CANVAS,CANVAS):
   raise ValueError("P0 approved image must use 1024 original RGBA")
  return np.array(pic,dtype=np.uint8)

def coords_from_target(w,h,reverse):
 dx=cv2.resize(reverse[:,:,0],(w,h),interpolation=cv2.INTER_LINEAR)*(w/FLOW_GRID)
 dy=cv2.resize(reverse[:,:,1],(w,h),interpolation=cv2.INTER_LINEAR)*(h/FLOW_GRID)
 yy,xx=np.indices((h,w),dtype=np.float32)
 return xx+dx,yy+dy

def assign_labels(sourceMaskList,src_roles,alpha,rgb):
 # Combine P0 view-dependent source ownership with 72.5-degree image
 # color identity and explicitly registered new-view anatomical ROIs.
 yy,xx=np.indices(alpha.shape,dtype=np.float32)
 pix=rgb.astype(np.int16)
 R,G,B=[pix[:,:,c] for c in range(3)]
 hair=(R>145)&((R-G)>20)&((B-G)>9)&((R-B)>4)&(yy<747)
 skin=(R>165)&(G>95)&(B>95)&((B-G)<16)&(R>B)&(~hair)
 foreground=alpha>0
 ids={sid:i for i,sid in enumerate(src_roles)}
 labels=np.full(alpha.shape,-1,dtype=np.int16)
 for i,sid in enumerate(src_roles):
  if sid in NO_VISIBLE_AT_90 or sid==AHOGE:continue
  score=sourceMaskList[i]
  if sid.startswith("hair."):
   chosen=(score>REGISTRATION_TH)&hair
  elif sid=="face.skin":
   chosen=(score>REGISTRATION_TH)&skin
  elif sid=="body.reference":
   chosen=(score>REGISTRATION_TH)&(yy>=715)&(~hair)
  elif sid=="ear.near":
   chosen=(score>REGISTRATION_TH)&skin
  elif sid=="eye.near":
   chosen=(score>REGISTRATION_TH)&(~hair)
  else:
   chosen=(score>REGISTRATION_TH)&(~hair)
  labels[chosen&foreground]=i
 # Source-based region ownership is refined by the candidate's *newly
 # painted* skin/hair edges. Pixel coordinates are annotations for this
 # one independently painted keyview, never universal model defaults.
 face=(xx>=472)&(xx<=780)&(yy>=295)&(yy<=696)&skin
 labels[face&foreground]=ids["face.skin"]
 for sid in ("hair.back","hair.side","hair.front"):
  mask=(sourceMaskList[ids[sid]]>REGISTRATION_TH)&hair
  labels[mask&foreground]=ids[sid]
 # Ear cartilage/skin is anatomically separate from both hair and cheek.
 ear=(((xx-452)/52)**2+((yy-475)/80)**2<1)&skin
 labels[ear&foreground]=ids["ear.near"]
 # One right-facing eye, with visible iris, sclera and lashes. Color
 # exclusion avoids giving nearby pink bangs to the eye ArtMesh.
 eye=(((xx-621)/89)**2+((yy-427)/64)**2<1)&(~hair)
 labels[eye&foreground]=ids["eye.near"]
 # Side nose surface and subtle single mouth stroke are anchored
 # separately from the facial skin ArtMesh.
 nose=(((xx-723)/48)**2+((yy-530)/46)**2<1)&skin
 labels[nose&foreground]=ids["nose"]
 mouth=(((xx-704)/37)**2+((yy-593)/25)**2<1)&(~hair)
 labels[mouth&foreground]=ids["mouth"]
 # The torso begins below the neck; preserve source hair hanging into
 # the collar and keep the dark jacket as body.reference.
 jacket=(yy>746)&(~hair)&(foreground)
 labels[jacket]=ids["body.reference"]
 firstMissing=foreground&(labels<0)
 if np.any(firstMissing):
  known=labels>=0
  if not np.any(known):raise ValueError("P0 semantic source correspondence entirely absent")
  _,near=cv2.distanceTransformWithLabels(np.where(known,0,255).astype("uint8"),
            cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
  lookup=np.full(int(near.max())+1,-1,dtype=np.int16)
  lookup[near[known]]=labels[known]
  fill=lookup[near[firstMissing]]
  if np.any(fill<0):raise ValueError("Nearest source semantic owner unknown")
  labels[firstMissing]=fill
 # Keep the near ear inside its annotated cartilage/outer-ear boundary.
 earRegion=(((xx-452)/52)**2+((yy-475)/80)**2<1)
 misplaced=(labels==ids["ear.near"])&(~earRegion)
 labels[misplaced]=np.where(hair[misplaced],ids["hair.side"],ids["face.skin"])
 # Remove stray cheek/skin pixels from the frontal fringe ArtMesh.
 strayFringe=(labels==ids["hair.front"])&(~hair)&(yy>320)
 labels[strayFringe]=ids["face.skin"]
 if np.any(foreground&(labels<0)):
  raise ValueError("P0 registered semantics have missing target foreground pixels")
 return labels,int(firstMissing.sum())

def run(root,out):
 root=Path(root).resolve();out=Path(out).resolve()
 out.mkdir(parents=True,exist_ok=True)
 original=load(root/"p5-see-through/mv-candidate/parts.json")
 p11=load(root/"p11-profile-psd/yaw090/qa.json")
 if original["characterId"]!="p0_character_001" or p11["characterId"]!="p0_character_001":
  raise ValueError("P0 registered identity differs")
 if sha(root/p11["psdPath"])!=p11["psdSHA256"]:
  raise ValueError("Canonical P0 90° PSD SHA changed")
 side=next(x for x in original["wholeViews"] if x["yawDeg"]==90)
 source_file=root/side["path"]
 if sha(source_file)!=side["sha256"]:
  raise ValueError("Original source 90° SHA differs")
 P=sorted((x for x in original["parts"] if x["yawDeg"]==90),
          key=lambda x:x["depthOrder"])
 if len(P)!=13 or [x["depthOrder"] for x in P]!=list(range(13)):
  raise ValueError("P0 registered original 13 source semantic roles required")
 targetFolder=root/"p14-authored-candidates"
 imageRGB=targetFolder/"yaw072p5-qwen2511-sourceguided.png"
 cutout=targetFolder/"yaw072p5-qwen2511-sourceguided-rgba.png"
 overlayFile=targetFolder/"yaw072p5-original-ahoge-layer.png"
 for f in (imageRGB,cutout,overlayFile):
  if not f.is_file():raise FileNotFoundError(f)
 target=source_as_RGBA(cutout)
 ahoge=source_as_RGBA(overlayFile)
 source=source_as_RGBA(source_file)
 # Bright original artwork background is not an optical-flow guide:
 # P0 source alpha is composited over the same dark working color.
 flowA=cv2.resize(source,(FLOW_GRID,FLOW_GRID),interpolation=cv2.INTER_AREA)
 flowB=cv2.resize(target,(FLOW_GRID,FLOW_GRID),interpolation=cv2.INTER_AREA)
 ab,ba=get_flow(flowA,flowB,mode="dis")
 mapx,mapy=coords_from_target(CANVAS,CANVAS,ba)
 predictions=[]
 for entry in P:
  filename=root/entry["path"]
  if sha(filename)!=entry["frameSha256"]:
   raise ValueError("Source P0 original layer checksum mismatch "+entry["semanticId"])
  if entry["semanticId"] in NO_VISIBLE_AT_90 or entry["semanticId"]==AHOGE:
   predictions.append(np.zeros((CANVAS,CANVAS),dtype=np.float32))
  else:
   sourceAlpha=source_as_RGBA(filename)[:,:,3].astype(np.float32)/255
   remapped=cv2.remap(sourceAlpha,mapx,mapy,cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_CONSTANT,borderValue=0)
   predictions.append(remapped)
 labels,fillPixels=assign_labels(predictions,[x["semanticId"] for x in P],target[:,:,3],target[:,:,:3])
 foreground=target[:,:,3]>0
 sourceCov=np.max(np.stack(predictions,axis=0),axis=0)>REGISTRATION_TH
 covered=int((foreground&sourceCov).sum())
 visible=int(foreground.sum())
 entries=[]
 layered=Image.new("RGBA",(CANVAS,CANVAS),(0,0,0,0))
 for i,entry in enumerate(P):
  sid=entry["semanticId"]
  if sid==AHOGE:
   rgba=ahoge.copy()
  elif sid in NO_VISIBLE_AT_90:
   rgba=np.zeros((CANVAS,CANVAS,4),dtype=np.uint8)
  else:
   rgba=target.copy()
   rgba[labels!=i]=0
  file=out/"layers"/(sid+".png");file.parent.mkdir(parents=True,exist_ok=True)
  Image.fromarray(rgba,"RGBA").save(file)
  alpha=rgba[:,:,3]
  coverage=int((alpha>0).sum())
  partial=int(((alpha>0)&(alpha<255)).sum())
  entries.append({
   "characterId":"p0_character_001","yaw":72.5,"semanticId":sid,
   "depthOrder":entry["depthOrder"],"original90Visibility":entry["visibility"],
   "original90RGBA_SHA256":entry["frameSha256"],
   "paintingSource":"Qwen-Image-Edit-2511 generated P0 intermediate reference" if sid!=AHOGE else "P0 original 90-degree ahoge",
   "sourcePainting_SHA256":sha(imageRGB) if sid!=AHOGE else entry["frameSha256"],
   "globalCanvas":[CANVAS,CANVAS],
   "alphaPixels":coverage,"partialAlphaPixels":partial,
   "path":str(file.relative_to(root)),"sha256":sha(file)
  })
  layered.alpha_composite(Image.fromarray(rgba,"RGBA"))
 composite=out/"yaw072p5-p0-source-mapped-artmesh.png"
 layered.save(composite)
 intended=Image.alpha_composite(Image.fromarray(target,"RGBA"),Image.fromarray(ahoge,"RGBA"))
 visiblePixels=np.asarray(intended.getchannel("A"))>0
 output=np.asarray(layered,dtype=np.int16)
 expected=np.asarray(intended,dtype=np.int16)
 alphaMax=int(np.abs(output[:,:,3]-expected[:,:,3]).max())
 rgbMax=int(np.abs(output[:,:,:3]-expected[:,:,:3])[visiblePixels].max()) if visiblePixels.any() else 0
 if alphaMax>0 or rgbMax>1:
  raise ValueError(f"P0 transparent semantic reconstruction differs alpha={alphaMax} RGB={rgbMax}")
 # Source-only independent art comparison panel.
 preview=Image.new("RGB",(4*360,360+40),(34,47,62))
 draw=ImageDraw.Draw(preview)
 source90=Image.fromarray(source,"RGBA")
 variants=[source90,Image.fromarray(target,"RGBA"),layered,
           Image.fromarray(source_as_RGBA(root/"p14-authored-candidates/yaw072p5-original-ahoge-composite.png"),"RGBA")]
 captions=["Original P0 90°","72.5° new RGBA","72.5° 13 ArtMesh","72.5° source ahoge"]
 for i,img in enumerate(variants):
  matte=Image.new("RGBA",img.size,(48,62,82,255))
  matte.alpha_composite(img)
  preview.paste(matte.convert("RGB").resize((360,360),Image.Resampling.LANCZOS),(i*360,0))
  draw.text((i*360+9,370),captions[i],fill="#f0f5ff")
 photo=out/"p14-profile-semantic-contact.jpg"
 preview.save(photo,quality=93)
 qa={
  "schema":"KOMA-P0-P14-INDEPENDENT-PAINTED-CANDIDATE-SEMANTIC-ARTMESH-V1",
  "characterId":"p0_character_001","candidateAngle":72.5,
  "originalSourceKeyViews":[0,45,90],"originalSource90SHA256":side["sha256"],
  "originalP11PSD_SHA256":p11["psdSHA256"],
  "originalP0SemanticViewSlots":39,
  "originalSemanticLayerCount":13,"generatedNativeCanvas":[1024,1024],
  "independentArtworkRGB":{"path":str(imageRGB.relative_to(root)),"sha256":sha(imageRGB)},
  "animeMatte":{"path":str(cutout.relative_to(root)),"sha256":sha(cutout)},
  "sourceAhogeOverlay":{"path":str(overlayFile.relative_to(root)),"sha256":sha(overlayFile)},
  "sourceSemanticMethod":"P0 90-degree registered ArtMesh ownership warped by DIS optical flow, nearest known ownership fallback",
  "flowGrid":[FLOW_GRID,FLOW_GRID],
  "foregroundPixels":visible,
  "registeredSourceMaskCoverage":covered,
  "registeredCoverageFraction":round(covered/max(visible,1),5),
  "targetPixelsAssignedViaNearestSource":fillPixels,
  "nearestSourceFallbackFraction":round(fillPixels/max(visible,1),5),
  "semanticLayerRecords":entries,
  "semanticLayerCount":len(entries),
  "composite":{"path":str(composite.relative_to(root)),"sha256":sha(composite)},
  "referenceContact":{"path":str(photo.relative_to(root)),"sha256":sha(photo)},
  "recomposedAlphaMaxDifference":alphaMax,
  "recomposedVisibleRGBMaxDifference":rgbMax,
  "registerStatus":"P14_ORIGINAL_P0_SEMANTIC_CANDIDATE_REGISTERED",
  "identityApproval":"PENDING_ANATOMICAL_AND_HAIR_COLOR_LINE_ART_REVIEW",
  "viewAngleApproval":"PENDING_TRUE_72P5_ANATOMICAL_VERIFICATION",
  "artisticApproval":"PENDING"
 }
 (out/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 print(json.dumps({
  "status":qa["registerStatus"],"semanticLayers":len(entries),
  "alphaMaxDifference":alphaMax,"visibleRGBMaxDifference":rgbMax,
  "sourceCoverageFraction":qa["registeredCoverageFraction"],
  "nearestFallbackFraction":qa["nearestSourceFallbackFraction"],
  "compositeSHA256":qa["composite"]["sha256"]
 },ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 args=p.parse_args()
 run(args.root,args.out)
