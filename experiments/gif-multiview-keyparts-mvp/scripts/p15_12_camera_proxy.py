#!/usr/bin/env python3
"""Camera-indexed 2.5D landmark proxy for P0 yaw 45–65 pose guidance.

Original 0/45/90 P5 anchors determine the projection curve. Incomplete
two-view anchors use extrapolation with explicit visibility uncertainty.
The source frame remains a geometric guide, not an independently drawn key.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/"private-assets"
REG=PRIVATE/"p5-see-through/mv-candidate/landmark-qa.json"
PARTS=PRIVATE/"p5-see-through/mv-candidate/parts.json"
OUT=PRIVATE/"p15-12-camera-proxy"
QA=ROOT/"evidence/p15-12-camera-proxy-qa.json"
ANGLES=(45.,55.,57.5,60.,62.5,65.,90.)
ROLES=("face.chin","face.jaw.near","eye.near.iris","eye.far.iris",
       "ear.near","nose","mouth","hair.ahoge.root","hair.clip.center",
       "hair.front","hair.side","hair.back")

def sha(f):
 h=hashlib.sha256()
 with Path(f).open("rb") as fp:
  for chunk in iter(lambda:fp.read(1048576),b""):h.update(chunk)
 return h.hexdigest()

def obs(rows,yaw):
 return next((r for r in rows if float(r["yaw"])==yaw),None)

def fit(rows):
 p0,p45,p90=(obs(rows,y) for y in (0,45,90))
 if not p45 or not p45.get("visible"):return {"mode":"hidden"}
 if p0 and p0.get("visible") and p90 and p90.get("visible"):
  x0,x45,x90=(float(p["xy"][0]) for p in (p0,p45,p90))
  c=(x45-(x0+x90)/math.sqrt(2))/(1-math.sqrt(2))
  return {"mode":"three_view_orthographic_proxy","c":c,"X":x0-c,"Z":x90-c,
          "reprojection45Error":abs(c+(x0-c+x90-c)/math.sqrt(2)-x45)}
 if p0 and p0.get("visible"):
  return {"mode":"two_view_linear_extrapolation","x45":float(p45["xy"][0]),
          "dxPerDegree":(p45["xy"][0]-p0["xy"][0])/45.}
 return {"mode":"fixed_45_anchor","x45":float(p45["xy"][0])}

def project(rows,params,yaw):
 p45,p90=(obs(rows,y) for y in (45,90))
 if params["mode"]=="hidden":return None
 mode=params["mode"]
 if mode=="three_view_orthographic_proxy":
  t=math.radians(yaw)
  x=params["c"]+params["X"]*math.cos(t)+params["Z"]*math.sin(t)
 elif mode=="two_view_linear_extrapolation":
  x=params["x45"]+(yaw-45)*params["dxPerDegree"]
 else:x=params["x45"]
 y=float(p45["xy"][1])
 if p90 and p90.get("visible") and p90.get("xy"):
  y+=(yaw-45)/45*(float(p90["xy"][1])-y)
 if not 0<=x<=1023 or not 0<=y<=1023:
  raise ValueError(f"anchor out of frame yaw {yaw}: {x,y}")
 return [round(x,3),round(y,3)]

def visibility(rows,yaw):
 p45,p90=(obs(rows,y) for y in (45,90))
 if not p45 or not p45.get("visible"):return 0.
 if p90 and not p90.get("visible"):
  return round(max(0.,math.cos(math.pi/2*(yaw-45)/45)),5)
 return 1.

def name(yaw):
 return "yaw"+(str(int(yaw)) if yaw.is_integer() else str(yaw).replace(".","p"))

def guide(yaw,anchors):
 rel="p15-09-midarc/"+name(yaw)+".png"
 if yaw in (45,90):rel="p2-views/whole/"+name(yaw)+".png"
 path=PRIVATE/rel
 if not path.is_file():return None
 with Image.open(path) as image:
  if image.size!=(1024,1024):raise ValueError("source canvas differs")
  bg=Image.new("RGBA",(1024,1024),"white")
  bg.alpha_composite(image.convert("RGBA"))
  portrait=bg.convert("RGB")
 (OUT/"conditioning").mkdir(parents=True,exist_ok=True)
 (OUT/"annotated").mkdir(parents=True,exist_ok=True)
 target=OUT/"conditioning"/(name(yaw)+"-pose.jpg")
 layer=OUT/"annotated"/(name(yaw)+"-anchor.png")
 portrait.save(target,quality=94,subsampling=0)
 annotated=portrait.copy();d=ImageDraw.Draw(annotated)
 for role,record in anchors.items():
  pt=record["xy"]
  if pt is None:continue
  x,y=pt
  color=(232,76,38) if record["visibility"]<.9 else (22,105,217)
  d.ellipse((x-6,y-6,x+6,y+6),fill=color,outline="white",width=2)
  d.text((x+8,y-17),role,fill=(20,31,48),stroke_width=1,stroke_fill="white")
 annotated.save(layer)
 return {"sourceGeometryPath":rel,"sourceGeometrySHA256":sha(path),
         "conditioningPath":str(target.relative_to(PRIVATE)),
         "conditioningSHA256":sha(target),
         "annotatedPath":str(layer.relative_to(PRIVATE)),
         "annotatedSHA256":sha(layer)}

def run():
 reg=json.loads(REG.read_text());parts=json.loads(PARTS.read_text())
 if reg["characterId"]!=parts["characterId"] or parts["characterId"]!="p0_character_001":
  raise AssertionError("P0 source identity changed")
 for yaw in (45,90):
  x=next(r for r in parts["wholeViews"] if r["yawDeg"]==yaw)
  if sha(PRIVATE/x["path"])!=x["sha256"]:
   raise AssertionError("Original source SHA differs")
 calibrations={role:fit(reg["landmarks"][role]) for role in ROLES}
 frames=[]
 for yaw in ANGLES:
  anchors={role:{"xy":project(reg["landmarks"][role],calibrations[role],yaw),
                 "visibility":visibility(reg["landmarks"][role],yaw),
                 "model":calibrations[role]["mode"]} for role in ROLES}
  eye1=anchors["eye.near.iris"]["xy"];eye2=anchors["eye.far.iris"]["xy"]
  nose=anchors["nose"]["xy"];clip=anchors["hair.clip.center"]["xy"]
  if not eye1[0]<nose[0]<eye2[0] or clip[0]<680:
   raise AssertionError(f"Physical camera-side coordinate order violated at {yaw}")
  record={"yaw":yaw,"anchors":anchors,
    "eyeNoseGap":round(eye2[0]-nose[0],3),
    "clipX":clip[0],
    "farEyeVisibilityProxy":anchors["eye.far.iris"]["visibility"]}
  rendered=guide(yaw,anchors)
  if rendered:record["guide"]=rendered
  frames.append(record)
 report={"schema":"KOMA-P15-12-CAMERA-PROXY-V1","characterId":"p0_character_001",
  "angles":list(ANGLES),"roleCount":len(ROLES),"roles":list(ROLES),
  "sourceLandmarkSHA256":sha(REG),"sourcePartRegistrySHA256":sha(PARTS),
  "calibration":calibrations,"frames":frames,
  "model":"screen x=c+X*cos(yaw)+Z*sin(yaw); y from registered 45-to-90 views",
  "visibilityUncertainty":"cosine taper for roles hidden by 90; heuristic, not measured art truth",
  "poseGuides":"P15-09 geometry reference registered separately from independent painting",
  "status":"NUMERIC_CAMERA_PROXY_VERIFIED","formalArtGate":"INDEPENDENT_MIDANGLE_PAINTINGS_REQUIRED",
  "originalHeroSHA256Verified":False}
 QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"roles":len(ROLES),
   "guides":sum(1 for r in frames if "guide" in r),
   "eyeNoseGapByAngle":{str(r["yaw"]):r["eyeNoseGap"] for r in frames}}))
 return report

if __name__=="__main__":run()
