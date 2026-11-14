#!/usr/bin/env python3
"""Upstream See-through layered-PSD extraction for independently generated P0 views."""
import argparse,hashlib,json,shutil,time
from pathlib import Path
from gradio_client import Client,handle_file

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()

def run(source,yaw,out,space,resolution,seed):
 source=Path(source).resolve();out=Path(out).resolve()
 if yaw not in (65,77.5) or not source.is_file():raise ValueError("P15 registered original source required")
 out.mkdir(parents=True,exist_ok=True)
 began=time.monotonic()
 result=Client(space,verbose=False).predict(handle_file(str(source)),resolution,seed,False,api_name="/inference")
 psd=result[0] if isinstance(result,(list,tuple)) else result
 if isinstance(psd,dict):psd=psd.get("path") or psd.get("name")
 if not psd or not Path(psd).is_file():raise FileNotFoundError("No generated PSD")
 key="yaw"+str(yaw).replace(".","p")
 dest=out/(key+"-layers.psd");shutil.copyfile(psd,dest)
 record={"schema":"KOMA-P0-P15-06-SEE_THROUGH-PSD-PROVENANCE-V1",
 "characterId":"p0_character_001","yaw":yaw,"source":str(source),"sourceSHA256":sha(source),
 "space":space,"model":"See-through LayerDiff3D + Marigold","resolution":resolution,"seed":seed,
 "output":str(dest),"psdSHA256":sha(dest),"bytes":dest.stat().st_size,
 "runtimeSeconds":round(time.monotonic()-began,1)}
 (out/(key+"-qa.json")).write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"yaw":yaw,"psdSHA256":record["psdSHA256"],"bytes":record["bytes"]}))
 return record

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--source",required=True);p.add_argument("--yaw",required=True,type=float)
 p.add_argument("--output",required=True);p.add_argument("--space",default="afredzhou/see-through-demo")
 p.add_argument("--resolution",default=768,type=int);p.add_argument("--seed",default=42,type=int)
 a=p.parse_args();run(a.source,a.yaw,a.output,a.space,a.resolution,a.seed)
