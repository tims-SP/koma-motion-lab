#!/usr/bin/env python3
"""P14 P0 painted key-view quality and ArtMesh source provenance assessment."""
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw

EVAL=(65,67.5,77.5)
W=400;H=436

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def load(file):return json.loads(Path(file).read_text(encoding="utf8"))

def analyze(root,out):
 root=Path(root).resolve();out=Path(out).resolve()
 out.mkdir(parents=True,exist_ok=True)
 p8=load(root/"p8-semantic-occlusion/selective-sequence/qa.json")
 art67=load(root/"p14-authored-candidates/yaw067p5-artmesh/qa.json")
 art72=load(root/"p14-authored-candidates/yaw072p5-artmesh/qa.json")
 semantic=load(root/"p14-authored-candidates/p14-vdd-smooth/qa.json")
 tex=load(root/"p14-authored-candidates/p14-vdd-smooth/texture-qa.json")
 temporal=load(root/"p14-authored-candidates/p14-vdd-smooth/temporal-qa.json")
 whole=load(root/"p14-authored-candidates/p14-whole-holdout/qa.json")
 browser=load(root/"p14-authored-candidates/p14-browser/browser-qa.json")
 source=load(root/"p5-see-through/mv-candidate/parts.json")
 assert all(x["characterId"]=="p0_character_001" for x in
   (p8,art67,art72,semantic,tex,temporal,whole,browser,source))
 assert semantic["frameCount"]==p8["frameCount"]==37
 assert art67["layerCount"]==art72["semanticLayerCount"]==13
 assert browser["screenshotCount"]==12 and not browser["javascriptErrors"] and not browser["failedRequests"]
 original={x["yawDeg"]:x for x in source["wholeViews"]}
 for angle in (0,45,90):
  p=root/original[angle]["path"]
  assert sha(p)==original[angle]["sha256"]
 P14={
  "67.5":art67["composite"],
  "72.5":art72["composite"]
 }
 images={};records={}
 for angle,qa,items in ((67.5,art67,art67["parts"]),(72.5,art72,art72["semanticLayerRecords"])):
  target=qa["composite"]
  assert sha(root/target["path"])==target["sha256"]
  known=set();canvas=Image.new("RGBA",(1024,1024),(0,0,0,0))
  for x in items:
   role=x["semanticId"]
   assert role not in known
   known.add(role)
   f=root/x["path"]
   assert sha(f)==x["sha256"]
   with Image.open(f) as im:
    assert im.mode=="RGBA" and im.size==(1024,1024)
    canvas.alpha_composite(im)
  assert len(known)==13
  for hidden in ("eye.far","ear.far","hair.clip.cross_gold"):
   x=next(p for p in items if p["semanticId"]==hidden)
   with Image.open(root/x["path"]) as im:
    assert int(np.max(np.asarray(im.getchannel("A"))))==0
  with Image.open(root/target["path"]) as im:
   assert np.array_equal(np.asarray(im.convert("RGBA")),np.asarray(canvas))
  records[str(angle)]={
   "sourceType":"PAINTED_P0_INDEPENDENT_CANDIDATE",
   "paintedPartCount":len(items),
   "sourceRGBAComposesPixelExact":True,
   "originalFarEyeHidden":True,
   "farEarHidden":True,
   "farSideGoldCrossClipHidden":True,
   "compositeSHA256":target["sha256"],
   "sourceQA_SHA256":sha(root/f"p14-authored-candidates/yaw{format(angle,'05.1f').replace('.','p')}-artmesh/qa.json")
  }
 contact=Image.new("RGB",(3*W,3*H),(25,36,52))
 draw=ImageDraw.Draw(contact)
 keys={
  "P8":{float(x["angle"]):x for x in p8["frames"]},
  "P14-ArtMesh":{float(x["angle"]):x for x in semantic["frames"]},
  "P14-Painted-Warp":{float(x["angle"]):x for x in whole["frames"]}
 }
 evaluations=[]
 for row,angle in enumerate(EVAL):
  entry={"angle":angle,"sourceFrameHashes":{}}
  for col,(method,available) in enumerate(keys.items()):
   frame=available[angle]
   path=root/frame["path"]
   assert sha(path)==frame["sha256"]
   with Image.open(path) as im:
    raw=np.asarray(im.convert("RGBA"))
    panel=Image.new("RGBA",(1024,1024),(49,62,78,255))
    panel.alpha_composite(im.convert("RGBA"))
   contact.paste(panel.convert("RGB").resize((W,W),Image.Resampling.LANCZOS),(col*W,row*H))
   draw.text((col*W+8,row*H+W+8),f"{method} · {angle}°",fill="white")
   mask=(raw[:,:,3]>=65).astype(np.uint8)
   # Alpha islands behind eyelids and hair are a secondary structural
   # proxy; artistic stroke continuity remains a human-reviewed gate.
   head=mask[145:740,170:850]
   crop=cv2.morphologyEx(head,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
   smallhole=int((crop>head).sum())
   entry["sourceFrameHashes"][method]=frame["sha256"]
   entry.setdefault("alphaGapPixels",{})[method]=smallhole
  evaluations.append(entry)
 image=out/"p14-p0-painted-vdd-visual-comparison.jpg"
 contact.save(image,quality=94)
 # The actual browser screenshots expose specific stroke-level artifacts
 # that generic temporal continuity and Canny max-edge thresholds do not.
 # Keep the visual adoption gate separate from programmatic QA.
 gate={
  "sourceRgbaPartInvariants":"PASS",
  "keyFrameSourceSHA256":"PASS",
  "P14MotionTemporalContinuity":temporal["status"],
  "P14FaceEdgeDiagnostic":tex["status"],
  "artifactEvidenceAngles":[65,77.5],
  "manualArtisticInspection":"REQUIRES_FACE_HAIR_STROKE_CORRESPONDENCE",
  "adoptedRenderer":"P8_SEMANTIC_OCCLUSION_ARTMESH",
  "paintedViewRoles":"CANDIDATE_UNTIL_ARTISTIC_ACCEPTANCE"
 }
 qa={
  "schema":"KOMA-P0-P14-PAINTED-VIEW-ARTMESH-QUALITY-GATES-V1",
  "characterId":"p0_character_001",
  "sourceKeyAngles":[0,45,90],
  "paintedCandidateAngles":[67.5,72.5],
  "sourceArtMeshViewSlots":39,
  "paintedSemanticRolesPerAngle":13,
  "paintedKeyQA":records,
  "fullRGBAFrames":37,
  "referenceP8SourceSHA256":sha(root/"p8-semantic-occlusion/selective-sequence/qa.json"),
  "sourcePaintedSequenceQA_SHA256":sha(root/"p14-authored-candidates/p14-vdd-smooth/qa.json"),
  "sourceP14TextureQA_SHA256":sha(root/"p14-authored-candidates/p14-vdd-smooth/texture-qa.json"),
  "sourceP14TemporalQA_SHA256":sha(root/"p14-authored-candidates/p14-vdd-smooth/temporal-qa.json"),
  "sourceBrowserQA_SHA256":sha(root/"p14-authored-candidates/p14-browser/browser-qa.json"),
  "textureRatios":{str(x["angle"]):x["edgeDensityRelativeToAdjacentMax"]
                   for x in tex["holdouts"]},
  "temporalMetrics":{
   "medianDelta":temporal["medianAdjacentMeanRGBDelta"],
   "maximumDelta":temporal["maxAdjacentMeanRGBDelta"],
   "outliers":temporal["outliers"]
  },
  "visualComparisonPath":str(image.relative_to(root)),
  "visualComparisonSHA256":sha(image),
  "reviewFrames":evaluations,
  "gate":gate,
  "artisticAcceptance":"PENDING",
  "status":"P14_PAINTED_P0_KEYVIEW_SOURCE_QA_COMPLETE"
 }
 (out/"quality-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 print(json.dumps({"status":qa["status"],"keyPaintedViews":2,"semanticParts":26,
  "fullRGBAFrames":37,"temporal":gate["P14MotionTemporalContinuity"],
  "visualAdoption":gate["manualArtisticInspection"],
  "comparisonSHA256":qa["visualComparisonSHA256"]},indent=2))
 return qa

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--root",required=True)
 parser.add_argument("--out",required=True)
 a=parser.parse_args()
 analyze(a.root,a.out)
