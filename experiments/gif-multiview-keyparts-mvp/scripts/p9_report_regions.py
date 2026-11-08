#!/usr/bin/env python3
"""Build true-source visual QA for original P0 color-region correspondences."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as fp:
  for chunk in iter(lambda:fp.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def read(path):
 return json.loads(Path(path).read_text(encoding="utf-8"))

def export(root):
 root=Path(root).resolve()
 p9=root/"p9-region-correspondence"
 original=p9/"region-pair-contact.jpg"
 im=Image.open(original).convert("RGB")
 width,height=im.size
 if (width,height)!=(5760,390):
  raise ValueError("Expected 16 original P0 color-piece panels")
 grid=Image.new("RGB",(width//2,height*2),(26,38,54))
 grid.paste(im.crop((0,0,width//2,height)),(0,0))
 grid.paste(im.crop((width//2,0,width,height)),(0,height))
 gridpath=p9/"region-pair-grid.jpg"
 grid.save(gridpath,quality=94)
 sources=[
  ("P8 · 物理锚点遮挡","p8-semantic-occlusion/selective-sequence",
   "p8-semantic-occlusion/selective-sequence/texture-qa.json"),
  ("P9 · 面部颜色区域","p9-region-correspondence/face",
   "p9-region-correspondence/face/texture-qa.json"),
  ("P9 · 面部与发束区域","p9-region-correspondence/face-hair",
   "p9-region-correspondence/face-hair/texture-qa.json")
 ]
 dim=450;head=50
 contact=Image.new("RGB",(3*dim,2*(dim+head)),(27,39,54))
 draw=ImageDraw.Draw(contact)
 records=[]
 for col,(label,folder,qaFile) in enumerate(sources):
  texture=read(root/qaFile)
  ratios={float(x["angle"]):x["edgeDensityRelativeToAdjacentMax"] for x in texture["holdouts"]}
  frames=[]
  for row,angle in enumerate((22.5,67.5)):
   frame=root/folder/("yaw"+str(angle).replace(".","p")+".png")
   with Image.open(frame) as native:
    if native.mode!="RGBA" or native.size!=(1024,1024):
     raise ValueError("Correspondence source must be true 1024 RGBA "+str(frame))
    matte=Image.new("RGBA",native.size,(50,64,83,255))
    matte.alpha_composite(native.convert("RGBA"))
    img=matte.convert("RGB").resize((dim,dim),Image.Resampling.LANCZOS)
   x=col*dim;y=row*(dim+head)
   contact.paste(img,(x,y+head))
   draw.text((x+8,y+5),label,fill="white")
   draw.text((x+8,y+26),f"{angle}° · edge ratio {ratios[angle]:.3f}",fill="#c0d9ed")
   frames.append({
    "yaw":angle,
    "sourcePath":str(frame.relative_to(root)),
    "sha256":sha(frame),
    "edgeRatio":ratios[angle]
   })
  records.append({"method":label,"textureStatus":texture["status"],"frames":frames})
 comparison=p9/"region-quality-comparison.jpg"
 contact.save(comparison,quality=94)
 source=read(p9/"qa.json")
 browser=read(p9/"browser/browser-qa.json")
 if source["characterId"]!="p0_character_001" or browser["characterId"]!="p0_character_001":
  raise ValueError("P0 identity mismatch")
 if browser["status"]!="PASS_REAL_P0_REGION_CORRESPONDENCE_VIEW":
  raise ValueError("P9 browser QA required")
 qa={
  "schema":"KOMA-P0-P9-REGION-PART-MATCH-QUALITY-V1",
  "characterId":"p0_character_001",
  "sourceOriginalKeyViews":[0,45,90],
  "genuinePSDViews":[0,45],
  "sourceP0RegistrySHA256":source["sourceRegistrySHA256"],
  "regionMatches":source["matchedColorRegions"],
  "registeredSemanticPairs":source["registeredSemanticPairs"],
  "contactGrid":{"path":str(gridpath.relative_to(root)),"sha256":sha(gridpath)},
  "qualityComparison":{"path":str(comparison.relative_to(root)),"sha256":sha(comparison)},
  "methods":records,
  "chosenGeometry":"P8_SEMANTIC_OCCLUSION_ARTMESH_BASELINE",
  "regionCorpus":"RESEARCH_CORRESPONDENCE_CANDIDATES",
  "futureGate":"HIGH_CONFIDENCE_PHYSICAL_STROKE_IDENTITIES",
  "artisticApproval":"PENDING"
 }
 dest=p9/"comparison-qa.json"
 dest.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":qa["regionCorpus"],"regionMatches":qa["regionMatches"],
    "contactGridSHA256":qa["contactGrid"]["sha256"],
    "qualityComparisonSHA256":qa["qualityComparison"]["sha256"],
    "methods":qa["methods"]},ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 a=p.parse_args()
 export(a.root)
