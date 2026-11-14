#!/usr/bin/env python3
"""P14 native 1024 RGBA character matte using rembg isnet-anime.

Source is an independently generated, registered RGB artwork candidate.
The source identity/angle gate is independent of alpha quality; a clean
foreground mask is not an artistic identity approval.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
import numpy as np

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as fp:
  for block in iter(lambda:fp.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def run(original,out,session):
 original=Path(original).resolve()
 out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
 with Image.open(original) as im:
  if im.size!=(1024,1024) or im.mode!="RGB":
   raise ValueError("Original generated anime portrait must be RGB 1024")
  inp=im.copy()
 from rembg import remove
 image=remove(inp,session=session,alpha_matting=False,post_process_mask=False)
 if image.mode!="RGBA" or image.size!=(1024,1024):
  raise ValueError("isnet-anime must return full-canvas 8-bit RGBA")
 alpha=np.asarray(image.getchannel("A")).copy()
 # Convert the near-opaque matte interior into fully opaque pixels,
 # retaining 8-bit antialias on the actual outline.
 alpha[alpha>=248]=255
 alpha[alpha<=4]=0
 image.putalpha(Image.fromarray(alpha,"L"))
 soft=((alpha>0)&(alpha<255))
 foreground=alpha>16
 if int(foreground.sum())<90000 or int(foreground.sum())>800000:
  raise ValueError("Unexpected source character foreground coverage")
 indices=np.argwhere(foreground)
 t,l=indices.min(axis=0);b,r=indices.max(axis=0)
 side_border=int(np.count_nonzero(alpha[:,0])+np.count_nonzero(alpha[:,-1]))
 topBorder=int(np.count_nonzero(alpha[0,:]))
 if side_border>500 or topBorder>120:
  raise ValueError("Foreground mask spans image boundaries unexpectedly")
 image.save(out)
 measure={
  "schema":"KOMA-P0-P14-INDEPENDENT-ART-RGBA-MATTE-QA-V1",
  "characterId":"p0_character_001",
  "sourceArtworkPath":str(original),"sourceArtworkSHA256":sha(original),
  "matteModel":"rembg isnet-anime",
  "alphaCorePolicy":{"fullyOpaqueMin":248,"transparentMax":4},
  "matteEngine":"onnxruntime CPU",
  "originalInputMode":"RGB",
  "outputPNGPath":str(out),
  "outputPNG_SHA256":sha(out),
  "canvas":[1024,1024],"outputMode":"RGBA",
  "alphaForegroundPixelsGt16":int(foreground.sum()),
  "alphaPartialPixels":int(soft.sum()),
  "alphaBounds":[int(l),int(t),int(r+1),int(b+1)],
  "borderAlphaPixels":{"leftRight":side_border,"top":topBorder},
  "matteStatus":"SOURCE_RGBA_FOREGROUND_REGISTERED",
  "identityAndAngleApproval":"PENDING",
  "fineEdgeArtisticApproval":"PENDING"
 }
 outfile=out.with_suffix(".qa.json")
 outfile.write_text(json.dumps(measure,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 print(json.dumps({k:measure[k] for k in (
  "matteStatus","outputPNG_SHA256","alphaForegroundPixelsGt16",
  "alphaPartialPixels","alphaBounds","borderAlphaPixels"
 )},ensure_ascii=False,indent=2))
 return measure

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--input",required=True)
 p.add_argument("--output",required=True)
 p.add_argument("--model",default="isnet-anime")
 args=p.parse_args()
 from rembg import new_session
 sess=new_session(args.model,providers=["CPUExecutionProvider"])
 run(args.input,args.output,sess)
