#!/usr/bin/env python3
"""P6 genuine P0 physical-flow ArtMesh correspondences and browser visual QA."""
import hashlib,json,math,unittest,zipfile
from pathlib import Path
from PIL import Image

BASE=Path(__file__).resolve().parents[1]
PRIVATE=BASE/"private-assets"
P5=PRIVATE/"p5-see-through/mv-candidate"
P6=PRIVATE/"p5-see-through/p6-motion"

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as fp:
  for block in iter(lambda:fp.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

@unittest.skipUnless((P5/"flow-vertex-correspondence.json").is_file(),
 "P0 private source-derived flow ArtMesh vertices")
class P6PhysicalFlow(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.flow=json.loads((P5/"flow-vertex-correspondence.json").read_text())
  cls.compare=json.loads((P6/"comparison-qa.json").read_text())

 def test_original_P0_source_and_model_anchor_provenance(self):
  f=self.flow
  self.assertEqual(f["characterId"],"p0_character_001")
  self.assertEqual(f["schema"],"KOMA-P0-P6-FLOW-CONSTRAINED-ARTMESH-MOTION-V1")
  self.assertEqual(f["nativeFlowCanvas"],[443,443])
  self.assertEqual(f["canvas"],[1024,1024])
  self.assertEqual(f["sourceManifestSHA256"],sha(P5/"parts.json"))
  self.assertEqual(f["landmarksSHA256"],sha(P5/"landmark-qa.json"))
  for yaw,sig in f["sourceP0SHA256"].items():
   path=PRIVATE/f"recovered-review/frames/head_8/yaw{int(yaw):03d}_whole.png"
   self.assertEqual(sha(path),sig)

 def test_2548_source_derived_control_vertices_and_stable_id(self):
  f=self.flow
  vertices=0
  for key in ("0-45","45-90"):
   for yaw in key.split("-"):
    motions=f["pairs"][key][yaw]
    self.assertEqual(len(motions),13)
    for semantic,points in motions.items():
     self.assertEqual(len(points),49)
     for pos in points:
      self.assertEqual(len(pos),2)
      self.assertTrue(all(isinstance(x,(float,int)) and math.isfinite(x) for x in pos))
      self.assertLessEqual(math.hypot(*pos),170.01)
      vertices+=1
  self.assertEqual(vertices,2548)
  self.assertEqual(f["qa"]["trackedSemanticSlots"],39)

 def test_html_source_flow_browser_true_frames(self):
  for folder,transition in (
   ("flow-mesh-browser","source-keyframe-select"),
   ("flow-blend-sequence","source-window-blend")):
   data=json.loads((P5/folder/"canvas-qa.json").read_text())
   self.assertEqual(data["characterId"],"p0_character_001")
   self.assertEqual(data["source"],"seethrough-paired")
   self.assertEqual(data["geometryWarp"],"physical-flow")
   self.assertEqual(data["transition"],transition)
   self.assertEqual(data["status"],"CAPTURED_FOR_ANATOMICAL_INSPECTION")
   for record in data["outputs"]:
    image=Path(record["path"])
    self.assertEqual(sha(image),record["sha256"])
    with Image.open(image) as pic:
     self.assertEqual(pic.mode,"RGBA")
     self.assertEqual(pic.size,(1024,1024))
   if folder=="flow-mesh-browser":self.assertEqual(len(data["outputs"]),5)
   else:self.assertEqual(len(data["outputs"]),37)

 def test_face_coverage_and_spatial_texture_improvement(self):
  methods=self.compare["methods"]
  old=methods["Original semantic mesh"]["holdoutTextureEdgeDensity"]
  new=methods["Physical-flow ArtMesh"]["holdoutTextureEdgeDensity"]
  for yaw in ("22.5","67.5"):
   self.assertLess(new[yaw],old[yaw])
  newqa=json.loads((P5/"flow-mesh-browser/texture-qa.json").read_text())
  self.assertEqual(newqa["status"],"PASS_TEXTURE_EDGE_DIAGNOSTIC")
  self.assertEqual(newqa["failed"],0)
  self.assertEqual(json.loads((P5/"flow-mesh-browser/holdout-qa.json").read_text())["status"],
                   "PASS_HOLDOUT_COVERAGE")
  self.assertEqual(json.loads((P5/"flow-blend-sequence/holdout-qa.json").read_text())["status"],
                   "PASS_HOLDOUT_COVERAGE")

 def test_full_sequence_temporal_qa_alternatives(self):
  crisp=json.loads((P5/"flow-mesh-sequence/temporal-qa.json").read_text())
  blending=json.loads((P5/"flow-blend-sequence/temporal-qa.json").read_text())
  self.assertEqual(crisp["angles"],37)
  self.assertEqual(blending["angles"],37)
  self.assertEqual(len(crisp["outliers"]),2)
  self.assertEqual(len(blending["outliers"]),0)
  self.assertEqual(blending["status"],"PASS_TEMPORAL_CONTINUITY")
  self.assertLess(blending["maxAdjacentMeanRGBDelta"],
                  crisp["maxAdjacentMeanRGBDelta"])
  self.assertEqual(self.compare["qualityDecision"]["productionArtAcceptance"],
                   "PENDING_SOURCE_CONSISTENT_TEXTURE_CORRESPONDENCE")

 def test_three_gif_outputs_have_independent_sha256_records(self):
  for name,metadata in (
   ("p0-psd-paired-vdd-turn.gif","turn-gif-qa.json"),
   ("p0-physical-flow-vdd-turn.gif","p0-physical-flow-vdd-turn.qa.json"),
   ("p0-flow-transition-review.gif","p0-flow-transition-review.qa.json")):
   qa=json.loads((P5/metadata).read_text())
   self.assertEqual(qa["GIFFrames"],72)
   self.assertEqual(qa["sourceFrameCount"],37)
   self.assertEqual(qa["GIFSHA256"],sha(P5/name))
  self.assertEqual(sha(PRIVATE/self.compare["contactSheet"]),
                   self.compare["contactSHA256"])

 @unittest.skipUnless((P6/"package-qa.json").is_file(),"P0 P6 package generated")
 def test_standalone_review_zip_integrity(self):
  info=json.loads((P6/"package-qa.json").read_text())
  self.assertEqual(info["characterId"],"p0_character_001")
  f=Path(info["archivePath"])
  self.assertEqual(sha(f),info["sha256"])
  self.assertTrue(info["internalHashesVerified"])
  with zipfile.ZipFile(f) as z:
   self.assertIsNone(z.testzip())
   manifest=json.loads(z.read("package-manifest.json"))
   self.assertEqual(manifest["registeredArtMeshSlots"],39)
   self.assertEqual(manifest["PSDViewAngles"],[0,45])
   self.assertEqual(manifest["registeredPhysicalLandmarks"],13)
   self.assertEqual(manifest["flowMeshControlVertices"],2548)

if __name__=="__main__":
 unittest.main(verbosity=2)
