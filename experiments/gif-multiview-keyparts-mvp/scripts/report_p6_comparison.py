#!/usr/bin/env python3
"""Actual Chromium screenshot comparison of P0 ArtMesh view-transition methods."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as fp:
  for chunk in iter(lambda:fp.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def run(root,out):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 sources={
  "Original semantic mesh":{
   "folder":"vdd-canvas","temporal":"vdd-sequence",
   "texture":"texture-qa.json"
  },
  "Physical-flow ArtMesh":{
   "folder":"flow-mesh-browser","temporal":"flow-mesh-sequence",
   "texture":"flow-mesh-browser/texture-qa.json"
  },
  "Flow source transition":{
   "folder":"flow-blend-sequence","temporal":"flow-blend-sequence",
   "texture":"flow-blend-sequence/texture-qa.json"
  }
 }
 def path(folder,angle):
  return root/folder/("yaw"+str(angle).replace(".","p")+".png")
 dim=440;heading=62
 board=Image.new("RGB",(3*dim,2*(dim+heading)),(26,36,50))
 draw=ImageDraw.Draw(board)
 results={}
 for col,(name,config) in enumerate(sources.items()):
  texture=json.loads((root/config["texture"]).read_text())
  time=json.loads((root/config["temporal"]/"temporal-qa.json").read_text())
  if texture["characterId"]!="p0_character_001" or time["characterId"]!="p0_character_001":
   raise ValueError("QA source character mismatch")
  holdouts={float(i["angle"]):i for i in texture["holdouts"]}
  entry={"source":name,
         "textureStatus":texture["status"],
         "temporalStatus":time["status"],
         "temporalMedianDelta":time["medianAdjacentMeanRGBDelta"],
         "temporalMaxDelta":time["maxAdjacentMeanRGBDelta"],
         "temporalOutlierCount":len(time["outliers"]),
         "holdoutTextureEdgeDensity":{
            str(angle):holdouts[angle]["edgeDensityRelativeToAdjacentMax"]
            for angle in (22.5,67.5)},
         "sourceImages":[]}
  for row,angle in enumerate((22.5,67.5)):
   actual=path(config["folder"],angle)
   with Image.open(actual) as im:
    if im.size!=(1024,1024) or im.mode!="RGBA":
     raise ValueError("Actual source renderer must be native PNG RGBA")
    layer=Image.new("RGBA",im.size,(47,61,78,255))
    layer.alpha_composite(im)
    resized=layer.convert("RGB").resize((dim,dim),Image.Resampling.LANCZOS)
   y=row*(dim+heading);x=col*dim
   board.paste(resized,(x,y+heading))
   caption=f"{angle} deg · edge ratio {holdouts[angle]['edgeDensityRelativeToAdjacentMax']:.2f}"
   draw.text((x+12,y+8),name,fill="white")
   draw.text((x+12,y+31),caption,fill="#a7c8e8")
   entry["sourceImages"].append({
       "angle":angle,"path":str(actual.relative_to(root)),
       "sha256":sha(actual)})
  results[name]=entry
 sheet=out/"rendering-quality-comparison.jpg"
 board.save(sheet,quality=93)
 report={
  "schema":"KOMA-P0-P6-REAL-BROWSER-RENDER-COMPARISON-V1",
  "characterId":"p0_character_001",
  "sourceAngles":[0,45,90],
  "holdouts":[22.5,67.5],
  "methods":results,
  "contactSheet":str(sheet),"contactSHA256":sha(sheet),
  "sourceStyle":"P0 generated original source ArtMeshes plus independent See-through PSD",
  "qualityDecision":{
   "spatialGeometry":"PHYSICAL_FLOW_CANDIDATE",
   "temporalBlend":"CONTROLLED_SOURCE_TRANSITION_STUDY",
   "productionArtAcceptance":"PENDING_SOURCE_CONSISTENT_TEXTURE_CORRESPONDENCE"
  }
 }
 (out/"comparison-qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"contactSheet":str(sheet),"contactSHA256":sha(sheet),
                   "methods":{k:{"texture":v["holdoutTextureEdgeDensity"],
                                 "temporal":v["temporalStatus"],
                                 "outliers":v["temporalOutlierCount"]}
                              for k,v in results.items()}},ensure_ascii=False,indent=2))
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--output",required=True)
 args=p.parse_args()
 run(args.root,args.output)
