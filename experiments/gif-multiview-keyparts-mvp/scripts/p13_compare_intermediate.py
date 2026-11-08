#!/usr/bin/env python3
"""P13 source-derived original P0 intermediate texture review and provenance QA."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for p in iter(lambda:f.read(1024*1024),b""):h.update(p)
 return h.hexdigest()

def read(file):return json.loads(Path(file).read_text(encoding="utf8"))

def compare(root,out):
 root=Path(root).resolve();out=Path(out).resolve()
 out.mkdir(parents=True,exist_ok=True)
 baseline=read(root/"p8-semantic-occlusion/selective-sequence/qa.json")
 baseTexture=read(root/"p8-semantic-occlusion/selective-sequence/texture-qa.json")
 baseTime=read(root/"p8-semantic-occlusion/selective-sequence/temporal-qa.json")
 meta=read(root/"p13-source-priority/source-feathered/qa.json")
 trialTexture=read(root/"p13-source-priority/source-feathered/texture-qa.json")
 trialTime=read(root/"p13-source-priority/source-feathered/temporal-qa.json")
 art=read(root/"p13-source-priority/p13-paint-contract.json")
 browser=read(root/"p13-source-priority/browser/browser-qa.json")
 gif=read(root/"p13-source-priority/p0-character-001-intermediate-turn.qa.json")
 assert all(x["characterId"]=="p0_character_001" for x in
            (baseline,baseTexture,baseTime,meta,trialTexture,trialTime,art,browser,gif))
 assert meta["frameCount"]==baseline["frameCount"]==37
 assert meta["semanticLayerCount"]==26
 assert len(art["intermediateViews"])==2
 assert gif["GIFFrames"]==72
 assert browser["screenshotCount"]==12
 other={}
 for method in ("source-staggered","confidence-source"):
  report=read(root/f"p13-source-priority/{method}/qa.json")
  tex=read(root/f"p13-source-priority/{method}/texture-qa.json")
  time=read(root/f"p13-source-priority/{method}/temporal-qa.json")
  assert report["frameCount"]==37
  other[method]={"textureStatus":tex["status"],
                 "edgeRatioByYaw":{str(x["angle"]):x["edgeDensityRelativeToAdjacentMax"]
                                   for x in tex["holdouts"]},
                 "temporalStatus":time["status"],
                 "temporalOutliers":len(time["outliers"]),
                 "referenceContactSHA256":report["contactSHA256"]}
 textured=lambda report:{str(item["angle"]):item["edgeDensityRelativeToAdjacentMax"] for item in report["holdouts"]}
 records=[]
 display=Image.new("RGB",(4*448,2*(448+38)),(29,39,53))
 draw=ImageDraw.Draw(display)
 for row,angle in enumerate((67.5,72.5)):
  a=next(x for x in baseline["frames"] if x["angle"]==angle)
  b=next(x for x in meta["frames"] if x["angle"]==angle)
  A=root/a["path"];B=root/b["path"]
  assert sha(A)==a["sha256"] and sha(B)==b["sha256"]
  rgba=[np.asarray(Image.open(f).convert("RGBA")).copy() for f in (A,B)]
  mi=np.logical_and(rgba[0][:,:,3]>0,rgba[1][:,:,3]>0)
  un=np.logical_or(rgba[0][:,:,3]>0,rgba[1][:,:,3]>0)
  iou=round(float(mi.sum())/max(1,int(un.sum())),5)
  diff=round(float(np.abs(rgba[0].astype(np.float32)-rgba[1].astype(np.float32)).mean()),4)
  records.append({"angle":angle,"sourceBaselineSHA256":a["sha256"],
     "sourceDerivedSHA256":b["sha256"],"silhouetteIoU":iou,
     "meanRGBAChannelDifference":diff})
  for col in range(4):
   source=rgba[0] if col in (0,2) else rgba[1]
   if col>=2:
    # Honest crop; 2x zoom of the face and visible mouth / near eye.
    source=source[320:780,370:860,:]
   view=Image.fromarray(source,"RGBA")
   backdrop=Image.new("RGBA",view.size,(49,63,81,255))
   backdrop.alpha_composite(view)
   thumb=backdrop.convert("RGB").resize((448,448),Image.Resampling.LANCZOS)
   x=col*448;y=row*(448+38)
   display.paste(thumb,(x,y))
   label=("P8 original RGBA" if col%2==0 else "P13 source-derived")
   draw.text((x+10,y+455),label+" @ "+str(angle)+"°",fill="white")
 image=out/"p13-original-intermediate-comparison.jpg"
 display.save(image,quality=94)
 qa={
  "schema":"KOMA-P0-P13-SOURCE-COMPONENT-PAINT-CONTRACT-QA-V1",
  "characterId":"p0_character_001",
  "authoritativeOriginalViewAngles":[0,45,90],
  "sourceP0SemanticArtMeshViewSlots":39,
  "intermediatePreviewAngles":[67.5,72.5],
  "sourceDerivedRGBAFrames":37,
  "sourceDerivedRGBAComponentSlots":26,
  "sourceDerivedComponentType":"P0_AUTHORED_KEYVIEW_TEXEL_WARP",
  "P13PaintingContractSHA256":sha(root/"p13-source-priority/p13-paint-contract.json"),
  "independentPaintComponentsPending":len(art["authoringPriority"])*2,
  "sourceDerivedRenderMode":meta["motionMode"],
  "originalP8Baseline":{
   "textureStatus":baseTexture["status"],
   "textureRatios":textured(baseTexture),
   "temporalStatus":baseTime["status"],
   "outliers":len(baseTime["outliers"])
  },
  "P13SourceDerivedTrial":{
   "textureStatus":trialTexture["status"],
   "textureRatios":textured(trialTexture),
   "temporalStatus":trialTime["status"],
   "outliers":len(trialTime["outliers"]),
   "maxAdjacentRGBDelta":trialTime["maxAdjacentMeanRGBDelta"]
  },
  "alternativeMethods":other,
  "silhouetteDifferences":records,
  "originalSourceVisualContact":{"path":str(image.relative_to(root)),
                                 "sha256":sha(image)},
  "realChromiumScreenshots":browser["screenshotCount"],
  "browserStatus":browser["status"],
  "sourceGIF72FramesSha256":gif["GIFSHA256"],
  "adoptedMotionBaseline":"P8_SEMANTIC_OCCLUSION",
  "independentArtAcceptance":"PENDING_P0_INTERMEDIATE_ORIGINAL_ARTWORK",
  "engineeringStatus":"P13_SOURCE_RGBA_COMPONENT_REGISTRY_AND_VIEWER_READY"
 }
 (out/"comparison-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({
  "engineeringStatus":qa["engineeringStatus"],"originalP8":qa["originalP8Baseline"],
  "P13SourceDerived":qa["P13SourceDerivedTrial"],
  "layerSlots":qa["sourceDerivedRGBAComponentSlots"],
  "independentPaintComponentsPending":qa["independentPaintComponentsPending"],
  "comparisonSHA256":qa["originalSourceVisualContact"]["sha256"]
 },ensure_ascii=False,indent=2))
 return qa

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 x=p.parse_args()
 compare(x.root,x.out)
