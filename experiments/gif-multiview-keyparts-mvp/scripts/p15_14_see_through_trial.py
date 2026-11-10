#!/usr/bin/env python3
"""P0 45-degree source See-through semantic PSD extraction via public demo.

Runs on the registered P0 original and stores raw PSD, gallery layers, and
source hashes under private assets. Gallery roles must still be mapped to
the existing 13-role ArtMesh by a separate structural acceptance process.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shutil
from pathlib import Path
from gradio_client import Client,handle_file
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/"private-assets"
SOURCE=PRIVATE/"p2-views/whole/yaw045.png"
OUT=PRIVATE/"p15-14-see-through"
QA=ROOT/"evidence/p15-14-layer-psd-source-qa.json"
SPACE="24yearsold/see-through-demo"
EXPECTED="78a08d5f010a8f449efda915a710a2de8958c3b1a32375df491d806fca251e40"

def sha(path):
 digest=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):digest.update(block)
 return digest.hexdigest()

def resolve_file(item):
 if isinstance(item,dict):
  item=item.get("path") or item.get("name") or item.get("url")
 if not item or not Path(item).is_file():raise FileNotFoundError(str(item))
 return Path(item)

def run(resolution=768,seed=42,split=True):
 if sha(SOURCE)!=EXPECTED:raise AssertionError("P0 original 45-degree source hash changed")
 OUT.mkdir(parents=True,exist_ok=True)
 client=Client(SPACE,verbose=False)
 result=client.predict(handle_file(str(SOURCE)),resolution,seed,split,api_name="/inference")
 if not isinstance(result,(tuple,list)) or len(result)<2:
  raise ValueError("Unexpected PSD inference response")
 source_psd=resolve_file(result[0])
 final=OUT/"p0-yaw45-see-through.psd"
 shutil.copy2(source_psd,final)
 if final.read_bytes()[:4]!=b"8BPS":
  raise ValueError("PSD signature missing")
 rows=[]
 for i,entry in enumerate(result[1]):
  caption=entry.get("caption") if isinstance(entry,dict) else None
  path=resolve_file(entry.get("image") if isinstance(entry,dict) else entry)
  name=re.sub("[^a-zA-Z0-9_-]+","-",caption or "part")[:45].strip("-")
  dst=OUT/f"layer-{i:02d}-{name}.png"
  with Image.open(path) as im:
   if im.mode!="RGBA":im=im.convert("RGBA")
   im.save(dst)
   width,height=im.size
  rows.append({"index":i,"sourceCaption":caption,"path":str(dst.relative_to(PRIVATE)),
               "sha256":sha(dst),"canvas":[width,height]})
 qa={"schema":"KOMA-P15-14-SEE-THROUGH-ORIGINAL-PSD-V1",
  "characterId":"p0_character_001","sourceOriginalYaw":45,"sourceSha256":EXPECTED,
  "space":SPACE,"resolution":resolution,"seed":seed,"splitEyesEars":split,
  "psd":{"path":str(final.relative_to(PRIVATE)),"sha256":sha(final),
         "bytes":final.stat().st_size},
  "galleryLayerCount":len(rows),"galleryLayers":rows,
  "status":"P0_PSD_AND_LAYER_GALLERY_EXTRACTED",
  "independentlyAcceptedArtmeshLayers":0,
  "approvedHeroHashReference":"P0 original 45 registration"}
 QA.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":qa["status"],"psdBytes":qa["psd"]["bytes"],
  "psdSHA256":qa["psd"]["sha256"],"galleryLayerCount":len(rows),
  "captions":[r["sourceCaption"] for r in rows]},ensure_ascii=False),flush=True)
 return qa

if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--resolution",type=int,default=768)
 a.add_argument("--seed",type=int,default=42)
 args=a.parse_args()
 run(args.resolution,args.seed,True)
