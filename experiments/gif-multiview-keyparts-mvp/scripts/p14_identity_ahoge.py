#!/usr/bin/env python3
"""P14 original P0 ahoge identity layer for 72.5-degree painted source."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()

def run(root):
 root=Path(root).resolve()
 data=root/"p14-authored-candidates";data.mkdir(exist_ok=True,parents=True)
 registry=json.loads((root/"p5-see-through/mv-candidate/parts.json").read_text(encoding="utf8"))
 assert registry["characterId"]=="p0_character_001"
 source=next(x for x in registry["parts"] if x["yawDeg"]==90 and x["semanticId"]=="hair.ahoge")
 path=root/source["path"]
 if sha(path)!=source["frameSha256"]:raise ValueError("P0 original ahoge SHA mismatched")
 with Image.open(path) as img:
  if img.mode!="RGBA" or img.size!=(1024,1024):raise ValueError("P0 source RGBA required")
  raw=np.array(img,dtype=np.uint8)
 # Registered view-specific anchor and smooth root transition.
 orig=raw[:,:,3].astype(np.float32)
 gradient=np.clip((147-np.arange(1024,dtype=np.float32))/35,0,1)
 raw[:,:,3]=np.round(orig*gradient[:,None]).astype("uint8")
 shift=(-20,0)
 layer=Image.new("RGBA",(1024,1024),(0,0,0,0))
 layer.paste(Image.fromarray(raw,"RGBA"),shift)
 ap=data/"yaw072p5-original-ahoge-layer.png"
 layer.save(ap)
 sourcePaint=data/"yaw072p5-qwen2511-sourceguided-rgba.png"
 with Image.open(sourcePaint) as img:
  if img.mode!="RGBA" or img.size!=(1024,1024):raise ValueError("New P14 painted alpha source required")
  img=img.copy()
 composite=Image.alpha_composite(img,layer)
 output=data/"yaw072p5-original-ahoge-composite.png"
 composite.save(output)
 ar=np.asarray(layer.getchannel("A"))
 bounds=np.argwhere(ar>0)
 assert len(bounds)>100 and int(ar[0,:].sum())==0
 report={
  "schema":"KOMA-P0-P14-ORIGINAL-AHOGE-IDENTITY-LAYER-V1",
  "characterId":"p0_character_001","viewAngle":72.5,
  "sourceAngle":90,"semanticId":"hair.ahoge",
  "originalSourcePNG":{"path":source["path"],"sha256":source["frameSha256"]},
  "sourcePaintedRGBA":{"path":str(sourcePaint.relative_to(root)),"sha256":sha(sourcePaint)},
  "transformation":{"translationXY":list(shift),"softRootFadeY":[112,147]},
  "layer":{"path":str(ap.relative_to(root)),"sha256":sha(ap),
           "visibleAlphaPixels":int((ar>0).sum())},
  "composite":{"path":str(output.relative_to(root)),"sha256":sha(output)},
  "identitySource":"P0 original approved 90-degree ahoge",
  "registrationStatus":"SOURCE_AHOGE_RGB_AND_ALPHA_TRACKED",
  "artisticAcceptance":"PENDING"
 }
 f=data/"yaw072p5-original-ahoge.qa.json"
 f.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps({"status":report["registrationStatus"],"sourceAhogeSHA":source["frameSha256"],
  "layerSHA":report["layer"]["sha256"],"compositeSHA":report["composite"]["sha256"]},indent=2))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 args=p.parse_args()
 run(args.root)
