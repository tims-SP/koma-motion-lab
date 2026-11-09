#!/usr/bin/env python3
"""P14 P0 intermediate source art: align hair-ornament occlusion and preserve source provenance."""
import argparse, hashlib, json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()

def main(root):
 root=Path(root).resolve()
 prior=root/"p5-see-through/mv-candidate/parts.json"
 registry=json.loads(prior.read_text(encoding="utf8"))
 assert registry["characterId"]=="p0_character_001"
 approved={x["yawDeg"]:x for x in registry["wholeViews"]}
 for angle in (45,90):
  assert sha(root/approved[angle]["path"])==approved[angle]["sha256"]
 out=root/"p14-authored-candidates"
 source=out/"yaw067p5-qwen2511-preserve-right-v2.png"
 with Image.open(source) as im:
  assert im.mode=="RGB" and im.size==(1024,1024)
  rgb=np.asarray(im).copy()
 # This exact independent P0-candidate portrait was manually inspected;
 # the generated gold ornament sits on hair where both registered P0
 # 67.5/72.5 views require the far-side clip to be occluded.
 hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
 yy,xx=np.indices((1024,1024))
 region=(xx>=392)&(xx<=532)&(yy>=275)&(yy<=419)
 gold=(hsv[:,:,0]>=8)&(hsv[:,:,0]<=39)&(hsv[:,:,1]>=64)&(hsv[:,:,2]>=83)
 color=(rgb[:,:,0].astype(int)>rgb[:,:,1].astype(int)+7)&(rgb[:,:,1].astype(int)>rgb[:,:,2].astype(int)+7)
 core=(region&gold&color).astype(np.uint8)*255
 count=int((core>0).sum())
 if not 400<=count<=8500:raise ValueError(f"P0 gold ornament segmentation requires review: {count}")
 kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(17,17))
 mask=cv2.dilate(core,kernel)
 # Fills gold surface and thin dark ink border without modifying
 # unrelated eye/face regions.
 inpaint=cv2.inpaint(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),mask,7,cv2.INPAINT_TELEA)
 output=cv2.cvtColor(inpaint,cv2.COLOR_BGR2RGB)
 file=out/"yaw067p5-qwen2511-occlusion-retouched.png"
 Image.fromarray(output,"RGB").save(file)
 delta=np.abs(output.astype(np.int16)-rgb.astype(np.int16))
 affected=int(np.count_nonzero(np.any(delta>0,axis=2)))
 contact=Image.new("RGB",(3*430,430+36),(35,49,65))
 labels=("Original P0 90°","67.5° generated","67.5° clip occluded")
 pics=[]
 for original in (root/approved[90]["path"],source,file):
  with Image.open(original) as im:
   base=Image.new("RGBA",im.size,(246,246,248,255))
   base.alpha_composite(im.convert("RGBA"))
   pics.append(base.convert("RGB").resize((430,430),Image.Resampling.LANCZOS))
 draw=ImageDraw.Draw(contact)
 for i,im in enumerate(pics):
  contact.paste(im,(430*i,0));draw.text((430*i+9,440),labels[i],fill="#f6f8fc")
 comparison=out/"yaw067p5-source-occlusion-contact.jpg"
 contact.save(comparison,quality=92)
 qa={
  "schema":"KOMA-P0-P14-67P5-ART-SOURCE-OCCLUSION-RETENTION-V1",
  "characterId":"p0_character_001","yaw":67.5,
  "approvedP0SourceAngles":[45,90],
  "sourceOriginal45SHA256":approved[45]["sha256"],
  "sourceOriginal90SHA256":approved[90]["sha256"],
  "sourceGeneratedRGB":{"path":str(source.relative_to(root)),"sha256":sha(source)},
  "occlusionAlignedRGB":{"path":str(file.relative_to(root)),"sha256":sha(file)},
  "hairOrnamentMask":{"corePixels":count,"expandedPixels":int((mask>0).sum()),"pixelChanged":affected,
                       "method":"bounded HSV gold segmentation and Telea source-hair inpainting",
                       "bounds":[392,275,532,419]},
  "reviewImage":{"path":str(comparison.relative_to(root)),"sha256":sha(comparison)},
  "identityGate":"PENDING_MANUAL_P0_CHARACTER_ART_REVIEW",
  "viewPoseGate":"PENDING_ORIGINAL_YAW67P5_ANATOMY_REVIEW",
  "artworkKind":"INDEPENDENT_MODEL_GENERATED_RGBA_REFERENCE_RETOUCH",
  "status":"SOURCE_ORNAMENT_VISIBILITY_REGISTERED"
 }
 (out/"yaw067p5-occlusion-retouched.qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"status":qa["status"],"corePixels":count,"pixelChanged":affected,
   "outSha256":qa["occlusionAlignedRGB"]["sha256"],"contactSHA256":qa["reviewImage"]["sha256"]},
   ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",required=True)
 args=parser.parse_args()
 main(args.root)
