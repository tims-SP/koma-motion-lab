#!/usr/bin/env python3
"""Rebuild editable original P0 90-degree PSD from verified RGBA semantic layers.

No painting or substitute imagery: the PSD stores source P0 semantic image
pixels and alpha. Transparent/hidden semantics remain registered; depth
order and canvas are checked against original P0 whole-view image.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def run(root,out):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 registry_path=root/"p5-see-through/mv-candidate/parts.json"
 registry=json.loads(registry_path.read_text(encoding="utf8"))
 assert registry["characterId"]=="p0_character_001"
 original_entry=next(p for p in registry["wholeViews"] if p["yawDeg"]==90)
 source_whole=root/original_entry["path"]
 if sha(source_whole)!=original_entry["sha256"]:
  raise ValueError("Canonical P0 90 degree original source SHA256 differs")
 with Image.open(source_whole) as im:
  canonical=np.array(im.convert("RGBA"),dtype=np.uint8)
 assert canonical.shape==(1024,1024,4)
 layers=sorted((p for p in registry["parts"] if p["yawDeg"]==90),
               key=lambda x:x["depthOrder"])
 if len(layers)!=13 or [p["depthOrder"] for p in layers]!=list(range(13)):
  raise ValueError("P0 profile 13-part immutable source semantic order required")
 psd=PSDImage.new("RGB",(1024,1024))
 direct=Image.new("RGBA",(1024,1024),(0,0,0,0))
 source=[]
 for rec in layers:
  file=root/rec["path"]
  if sha(file)!=rec["frameSha256"]:
   raise ValueError("P0 source part SHA mismatched "+rec["semanticId"])
  with Image.open(file) as im:
   if im.mode!="RGBA" or im.size!=(1024,1024):
    raise ValueError("Each source semantic must be original 1024 native RGBA")
   pixels=im.copy()
  if rec["visibility"]=="hidden" and np.any(np.asarray(pixels)[:,:,3]):
   raise ValueError("Hidden layer has visible source pixels")
  direct.alpha_composite(pixels)
  pixel_layer=PixelLayer.frompil(pixels,psd,name=rec["semanticId"],top=0,left=0)
  pixel_layer.visible=(rec["visibility"]=="visible")
  psd.append(pixel_layer)
  source.append({
   "semanticId":rec["semanticId"],"sourcePNGPath":rec["path"],
   "sourceSHA256":rec["frameSha256"],
   "registeredAlphaPixels":int(np.count_nonzero(np.array(pixels)[:,:,3])),
   "depthOrder":rec["depthOrder"],
   "visibility":rec["visibility"],
   "bbox":rec["bbox"]
  })
 directArray=np.array(direct)
 if not np.array_equal(directArray,canonical):
  diff=np.abs(directArray.astype(np.int16)-canonical.astype(np.int16))
  raise ValueError("Source P0 layered RGBA reconstruction is not pixel exact. max="+str(diff.max()))
 dest=out/"p0-character-001-registered-profile-yaw090.psd"
 psd.save(dest)
 reopened=PSDImage.open(dest)
 if len(reopened)!=13 or reopened.size!=(1024,1024):
  raise ValueError("PSD saved source semantic layers incorrectly")
 repainted=Image.new("RGBA",(1024,1024),(0,0,0,0))
 evaluated=[]
 for index,layer in enumerate(reopened):
  rec=source[index]
  if layer.name!=rec["semanticId"]:
   raise ValueError("Original semantic layer order changed")
  if layer.visible!=(rec["visibility"]=="visible"):
   raise ValueError("Original semantic occlusion visibility changed")
  decoded=layer.composite()
  if decoded is None:raise ValueError("Cannot composite real P0 source layer")
  if decoded.size!=(1024,1024):raise ValueError("PSD changed global canvas")
  decoded=decoded.convert("RGBA")
  with Image.open(root/rec["sourcePNGPath"]) as im:
   inp=np.asarray(im.convert("RGBA"),dtype=np.int16)
  pix=np.asarray(decoded,dtype=np.int16)
  delta=np.abs(pix-inp)
  if int(delta[:,:,3].max())!=0:
   raise ValueError("PSD damaged source alpha for "+rec["semanticId"])
  meaningful=inp[:,:,3]>0
  maxVisible=int(delta[:,:,:3][meaningful].max()) if meaningful.any() else 0
  if maxVisible>1:raise ValueError("PSD pixel color roundtrip changed visible P0 strokes")
  repainted.alpha_composite(decoded)
  evaluated.append({**rec,
    "psdLayerName":layer.name,
    "originalAlphaExact":True,
    "maximumVisibleColorRoundTripDifference":maxVisible})
 painted=np.asarray(repainted,dtype=np.int16)
 compare=np.abs(painted-canonical.astype(np.int16))
 alphaMax=int(compare[:,:,3].max())
 colored=(canonical[:,:,3]>0)
 visibleMax=int(compare[:,:,:3][colored].max())
 visibleMean=round(float(compare[:,:,:3][colored].mean()),7)
 if alphaMax!=0 or visibleMax>2:
  raise ValueError("PSD decode composite diverged from canonical P0 image")
 directPath=out/"p0-character-001-profile-source-rgba.png"
 direct.save(directPath)
 decodedPath=out/"p0-character-001-profile-psd-composite.png"
 repainted.save(decodedPath)
 # Compare high-resolution actual reference / layered PSD raster.
 W=520;H=570
 contact=Image.new("RGB",(W*2,H),(42,56,75))
 canvas=ImageDraw.Draw(contact)
 for i,image in enumerate((Image.fromarray(canonical,"RGBA"),repainted)):
  back=Image.new("RGBA",image.size,(47,62,81,255))
  back.alpha_composite(image)
  contact.paste(back.convert("RGB").resize((W,W),Image.Resampling.LANCZOS),(i*W,0))
  canvas.text((i*W+12,530),
   "P0 canonical yaw90" if i==0 else "13-layer editable PSD",fill="#ffffff")
 shot=out/"p0-90-psd-source-comparison.jpg"
 contact.save(shot,quality=94)
 record={
  "schema":"KOMA-P0-P11-EDITABLE-PROFILE-PSD-ORIGINAL-LAYERS-V1",
  "characterId":"p0_character_001",
  "angle":90,
  "source":"approved P0 original 90-degree PNG and registered transparent 13 semantic parts",
  "globalCanvas":[1024,1024],
  "sourceCanonicalPNGPath":original_entry["path"],
  "sourceCanonicalSHA256":original_entry["sha256"],
  "sourcePartsRegistrySHA256":sha(registry_path),
  "psdPath":str(dest.relative_to(root)),
  "psdSHA256":sha(dest),
  "psdBytes":dest.stat().st_size,
  "nativeLayerCount":len(layers),
  "layers":evaluated,
  "sourceReconstructionPixelExact":True,
  "sourceRGBAPreviewPath":str(directPath.relative_to(root)),
  "sourceRGBAPreviewSHA256":sha(directPath),
  "PSDCompositePath":str(decodedPath.relative_to(root)),
  "PSDCompositeSHA256":sha(decodedPath),
  "PSDCompositeAlphaMaxDifference":alphaMax,
  "PSDCompositeVisibleColorMaxDifference":visibleMax,
  "PSDCompositeVisibleColorMeanDifference":visibleMean,
  "sourceComparisonPath":str(shot.relative_to(root)),
  "sourceComparisonSHA256":sha(shot),
  "visualState":"P0_ORIGINAL_SIDE_PROFILE_EDITABLE_LAYERS_REGISTERED",
  "assetSourceType":"P0_REGISTERED_ORIGINAL_SEMANTIC_PNG",
  "originalP0ArtisticSource":True,
  "profileOccludedArtwork":"REQUIRES_SOURCE_AUTHORING_FOR_UNSEEN_SKIN_AND_HAIR_SURFACES"
 }
 (out/"qa.json").write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 print(json.dumps({k:record[k] for k in (
  "characterId","angle","nativeLayerCount","sourceReconstructionPixelExact",
  "psdSHA256","psdBytes","PSDCompositeAlphaMaxDifference",
  "PSDCompositeVisibleColorMaxDifference","visualState")},ensure_ascii=False,indent=2))
 return record

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 args=p.parse_args()
 run(args.root,args.out)
