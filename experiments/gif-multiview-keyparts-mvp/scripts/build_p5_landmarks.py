#!/usr/bin/env python3
"""Build image-derived physical-landmark correspondence across authentic P0 views.

Official See-through PSD gives iris/ear/clip components at 0° and 45°.
90° visible parts use the original P0 source ArtMesh registration, since
the semantic PSD has not been generated for that reference view.

Correspondences are geometry evidence, not pose/identity substitutions.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw

SEMANTIC_TRACKS={
 "face.chin":("face.skin","chin"),
 "face.jaw.near":("face.skin","jaw.left"),
 "eye.near.iris":("eye.near","iris.center"),
 "eye.far.iris":("eye.far","iris.center"),
 "ear.near":("ear.near","center"),
 "ear.far":("ear.far","center"),
 "nose":("nose","center"),
 "mouth":("mouth","center"),
 "hair.ahoge.root":("hair.ahoge","outline.bottom"),
 "hair.clip.center":("hair.clip.cross_gold","clip.center"),
 "hair.front":("hair.front","center"),
 "hair.side":("hair.side","center"),
 "hair.back":("hair.back","center")
}
NEAR_FAR={
 "eye.near.iris":("eye.iris.pair",0),
 "eye.far.iris":("eye.iris.pair",1),
 "ear.near":("ear.pair",0),
 "ear.far":("ear.pair",1)
}
LABELS=["face.chin","eye.near.iris","eye.far.iris","nose","mouth",
        "ear.near","hair.clip.center","hair.ahoge.root"]

def hashfile(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as fp:
  for chunk in iter(lambda:fp.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def components(file,alpha_cut=150,minArea=70):
 with Image.open(file) as im:
  a=np.asarray(im.convert("RGBA"))
 mask=(a[:,:,3]>=alpha_cut).astype(np.uint8)
 n,l,stats,xy=cv2.connectedComponentsWithStats(mask,8)
 c=sorted([{"pixels":int(stats[i,4]),
            "xy":[round(float(x),2) for x in xy[i]],
            "bbox":[int(v) for v in stats[i,:4]]}
           for i in range(1,n) if stats[i,4]>=minArea],
          key=lambda x:x["pixels"],reverse=True)
 return c

def get_anchor(part,name):
 for a in part["anchors"]:
  if a["id"]==name:return [float(x) for x in a["xy"]]
 raise ValueError("Anchor "+part["semanticId"]+"/"+name+" unavailable")

def source_psd_layers(root,yaw):
 directory=root/("p4-see-through/front/exported" if yaw==0 else
                 "p5-see-through/yaw045/exported")
 qa=json.loads((directory/"layer-qa.json").read_text())
 if qa["characterId"]!="p0_character_001" or qa.get("viewYawDeg",0)!=yaw:
  raise ValueError("Wrong PSD identity/view")
 result={}
 for entry in qa["layers"]:
  file=directory/entry["outputPath"]
  if hashfile(file)!=entry["outputSha256"]:raise ValueError("PSD layer checksum mismatch")
  result[entry["semanticCandidateId"]]=file
 return result

def model_landmark(layers,landmark,part):
 if landmark in NEAR_FAR:
  semantic,side=NEAR_FAR[landmark]
  nodes=components(layers[semantic],150,200)
  if len(nodes)<2:return None
  nodes=sorted(nodes[:2],key=lambda x:x["xy"][0])
  chosen=nodes[side]
  # Model ear or iris centroid is expected within/near original semantics
  # but may include small offsets from original P0 layers.
  return (chosen["xy"],"PSD_ALPHA_CONNECTED_COMPONENT",chosen["pixels"])
 if landmark=="hair.clip.center":
  nodes=components(layers["hair.clip.cross_gold"],130,160)
  if nodes:return (nodes[0]["xy"],"PSD_GOLD_CLIP_COMPONENT",nodes[0]["pixels"])
 if landmark in ("nose","mouth"):
  nodes=components(layers[landmark],80,15)
  if nodes:
   point=nodes[0]["xy"]
   box=part.get("bbox")
   if box and box[0]-12<=point[0]<=box[2]+12 and box[1]-12<=point[1]<=box[3]+12:
    return (point,"PSD_FACE_COMPONENT_WITHIN_ORIGINAL_SEMANTIC_BBOX",nodes[0]["pixels"])
 return None

def make(root,out):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(exist_ok=True,parents=True)
 registry=json.loads((root/"p5-see-through/mv-candidate/parts.json").read_text())
 if len(registry["parts"])!=39:raise ValueError("3×13 ArtMeshes not registered")
 byslot={(x["yawDeg"],x["semanticId"]):x for x in registry["parts"]}
 original={r["yawDeg"]:r for r in registry["wholeViews"]}
 layers={yaw:source_psd_layers(root,yaw) for yaw in (0,45)}
 tracks={}
 for semantic,(partId,anchor) in SEMANTIC_TRACKS.items():
  coords=[]
  for yaw in (0,45,90):
   part=byslot[(yaw,partId)]
   visible=part["visibility"]=="visible"
   if not visible:
    coords.append({"yaw":yaw,"visible":False,"xy":None,"source":"REGISTERED_P0_OCCLUSION"})
    continue
   source="P0_GIF_ARTMESH_SOURCE_ANCHOR"
   x=get_anchor(part,anchor)
   evidencePixels=None
   if yaw in layers:
    chosen=model_landmark(layers[yaw],semantic,part)
    if chosen:
     x,source,evidencePixels=chosen
   coords.append({"yaw":yaw,"visible":True,"xy":x,
     "source":source,"sourceEvidencePixels":evidencePixels})
  tracks[semantic]=coords
 # Interpolate only same physical landmarks visible in both reference views.
 mid={}
 for yaw in (22.5,67.5):
  a,b=(0,45) if yaw<45 else (45,90)
  t=(yaw-a)/(b-a)
  points={}
  for semantic,track in tracks.items():
   x=next(p for p in track if p["yaw"]==a)
   y=next(p for p in track if p["yaw"]==b)
   if not x["visible"] or not y["visible"]:continue
   points[semantic]={"xy":[round((1-t)*x["xy"][i]+t*y["xy"][i],2)
                            for i in (0,1)],
                    "sourceAngles":[a,b],"method":"TRACKED_PHYSICAL_ID_LINEAR_PREDICTION"}
  mid[str(yaw)]=points
 # Actual reference landmarks and predicted holdout landmarks are visualized
 # atop genuine recovered author assets and actual P5 Chromium renders.
 combined=[(0,root/original[0]["path"]),
           (22.5,root/"p5-see-through/mv-candidate/vdd-canvas/yaw22p5.png"),
           (45,root/original[45]["path"]),
           (67.5,root/"p5-see-through/mv-candidate/vdd-canvas/yaw67p5.png"),
           (90,root/original[90]["path"])]
 width=360;head=30;canvas=Image.new("RGB",(5*width,width+55),(25,39,56))
 dr=ImageDraw.Draw(canvas)
 for index,(yaw,path) in enumerate(combined):
  im=Image.open(path).convert("RGBA")
  assert im.size==(1024,1024)
  matte=Image.new("RGBA",im.size,(52,69,87,255));matte.alpha_composite(im)
  canvas.paste(matte.convert("RGB").resize((width,width),Image.Resampling.LANCZOS),(index*width,head))
  dr.text((index*width+8,6),str(yaw)+"°  "+("P0 key" if yaw in (0,45,90) else "VDD predicted"),fill="#eeeeee")
  marks=mid.get(str(yaw),{}) if yaw not in (0,45,90) else {
    key:next(v for v in track if v["yaw"]==yaw)
    for key,track in tracks.items()}
  for key in LABELS:
   item=marks.get(key)
   if not item or not item.get("xy") or item.get("visible") is False:continue
   x,y=item["xy"];cx=index*width+x*width/1024;cy=head+y*width/1024
   fill="#ffff66" if yaw in (0,45,90) else "#00ffe5"
   dr.ellipse((cx-3,cy-3,cx+3,cy+3),fill=fill,outline="#182636",width=1)
   dr.text((cx+4,cy-10),key.split(".")[0]+(".iris" if ".iris" in key else ""),fill=fill)
 sheet=out/"landmark-correspondence.jpg"
 canvas.save(sheet,quality=93)
 # Mathematical gates: near eye x, nose x move monotonically on this set,
 # while physical far eye and clip visibility follows original asset register.
 near=[next(x for x in tracks["eye.near.iris"] if x["yaw"]==y) for y in (0,45,90)]
 nose=[next(x for x in tracks["nose"] if x["yaw"]==y) for y in (0,45,90)]
 clip90=next(x for x in tracks["hair.clip.center"] if x["yaw"]==90)
 far90=next(x for x in tracks["eye.far.iris"] if x["yaw"]==90)
 gates={
    "sourcePSDEyeIrisComponents0":all(next(x for x in tracks[k] if x["yaw"]==0)["source"]=="PSD_ALPHA_CONNECTED_COMPONENT"
        for k in ("eye.near.iris","eye.far.iris")),
    "sourcePSDEyeIrisComponents45":all(next(x for x in tracks[k] if x["yaw"]==45)["source"]=="PSD_ALPHA_CONNECTED_COMPONENT"
        for k in ("eye.near.iris","eye.far.iris")),
    "nearEyePhysicalXMileage":near[0]["xy"][0]<near[1]["xy"][0]<near[2]["xy"][0],
    "nosePhysicalXMileage":nose[0]["xy"][0]<nose[1]["xy"][0]<nose[2]["xy"][0],
    "profileFarEyeHidden":not far90["visible"],
    "profileGoldClipHidden":not clip90["visible"],
    "twoHoldoutsRegistered":len(mid["22.5"])>=7 and len(mid["67.5"])>=7
 }
 doc={
    "schema":"KOMA-P0-P5-IMAGE-DERIVED-PHYSICAL-LANDMARK-CORRESPONDENCE-V1",
    "characterId":"p0_character_001",
    "referencedPSDViewAngles":[0,45],
    "originalGIFViewAngles":[0,45,90],
    "landmarks":tracks,"holdoutPredictions":mid,
    "sourceFiles":{str(y):{"path":original[y]["path"],"sha256":original[y]["sha256"]} for y in (0,45,90)},
    "contactSheet":str(sheet.relative_to(root)),
    "contactSHA256":hashfile(sheet),
    "qaGates":gates,
    "status":"IMAGE_DERIVED_LANDMARKS_REGISTERED" if all(gates.values()) else "LANDMARK_QA_REVIEW",
    "visualAcceptance":"PENDING_MANUAL_IMAGE_INSPECTION",
    "nextAction":"Use source landmarks as semantic VDD control handles before full texture blending"
 }
 (out/"landmark-qa.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":doc["status"],"landmarkCount":len(tracks),
     "holdoutCounts":{x:len(y) for x,y in mid.items()},
     "passed":sum(gates.values()),"failed":len(gates)-sum(gates.values()),
     "qaGates":gates,"contactSHA256":doc["contactSHA256"]},ensure_ascii=False,indent=2))
 return doc

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--root",required=True)
 p.add_argument("--out",required=True)
 a=p.parse_args()
 make(a.root,a.out)
