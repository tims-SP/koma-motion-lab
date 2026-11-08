#!/usr/bin/env python3
"""P5 P0 45-degree real PSD and source-derived landmark quality regression."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image

BASE=Path(__file__).resolve().parents[1]
PRIVATE=BASE/"private-assets"
P5=PRIVATE/"p5-see-through"
VIEW=P5/"yaw045"
MV=P5/"mv-candidate"
PSD=VIEW/"p0-character-001-see-through.psd"

def sha(file):
 h=hashlib.sha256()
 with Path(file).open("rb") as fp:
  for chunk in iter(lambda:fp.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

@unittest.skipUnless(PSD.is_file(),"P5 reference PSD is in private assets")
class P5TwoSourcePSDViews(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.psdQA=json.loads((VIEW/"inference-qa.json").read_text())
  cls.export=json.loads((VIEW/"exported/layer-qa.json").read_text())
  cls.parts=json.loads((VIEW/"integrated/parts.json").read_text())
  cls.qa=json.loads((VIEW/"integrated/qa.json").read_text())
  cls.multi=json.loads((MV/"parts.json").read_text())
  cls.multiqa=json.loads((MV/"qa.json").read_text())
  cls.landmark=json.loads((MV/"landmark-qa.json").read_text())

 def test_45_real_psd_source_identity(self):
  with PSD.open("rb") as fp:self.assertEqual(fp.read(4),b"8BPS")
  self.assertEqual(self.psdQA["characterId"],"p0_character_001")
  self.assertEqual(self.psdQA["status"],"PSD_RECEIVED_AWAITING_LAYER_INSPECTION")
  self.assertEqual(self.psdQA["outputFiles"][0]["sha256"],sha(PSD))
  self.assertEqual(self.export["psdSHA256"],sha(PSD))
  self.assertEqual(self.export["viewYawDeg"],45)
  self.assertEqual(self.export["modelCanvas"],[768,768])
  self.assertEqual(self.export["exportCanvas"],[1024,1024])

 def test_45_13_model_layers_rgba_with_source_provenance(self):
  self.assertEqual(self.export["totalLayers"],13)
  self.assertEqual(len(self.export["layers"]),13)
  roles={x["semanticCandidateId"] for x in self.export["layers"]}
  self.assertTrue({"hair.back","hair.front","face.skin","eye.iris.pair",
                  "ear.pair","hair.clip.cross_gold"}<=roles)
  for ent in self.export["layers"]:
   f=VIEW/"exported"/ent["outputPath"]
   self.assertEqual(sha(f),ent["outputSha256"])
   with Image.open(f) as im:
    self.assertEqual(im.mode,"RGBA")
    self.assertEqual(im.size,(1024,1024))

 def test_45_static_composition_source_fidelity(self):
  self.assertEqual(self.qa["yaw"],45)
  self.assertEqual(self.qa["registeredParts"],13)
  self.assertEqual(self.qa["transparentHolesOnOpaqueSource"],0)
  self.assertEqual(self.qa["originalWholeSilhouetteIoU"],1)
  self.assertLessEqual(self.qa["changedSourceVisiblePixels"],60)
  self.assertGreater(self.qa["sumAddedInferredHiddenPixels"],250000)

 def test_registered_semantics_physical_visibility_and_provenance(self):
  layers={p["semanticId"]:p for p in self.parts["parts"]}
  self.assertEqual(len(layers),13)
  for semantic,p in layers.items():
   f=VIEW/"integrated"/p["path"]
   self.assertEqual(p["frameSha256"],sha(f),semantic)
   self.assertEqual(len(p["mesh"]["vertexIds"]),49)
   self.assertEqual(len(p["mesh"]["triangles"]),72)
   with Image.open(f) as im:
    self.assertEqual(im.mode,"RGBA")
    self.assertEqual(im.size,(1024,1024))
  self.assertEqual(layers["ear.far"]["visibility"],"hidden")
  self.assertEqual(layers["eye.near"]["visibility"],"visible")
  self.assertEqual(layers["eye.far"]["visibility"],"visible")
  self.assertEqual(layers["hair.clip.cross_gold"]["visibility"],"visible")

 def test_multiview_0_45_PSD_90_original_stable_39(self):
  self.assertEqual(self.multiqa["PSDViewAngles"],[0,45])
  self.assertEqual(self.multiqa["originalP0ViewAngles"],[90])
  self.assertEqual(len(self.multi["parts"]),39)
  self.assertEqual(self.multiqa["registeredSemanticViews"],39)
  canonical=json.loads((PRIVATE/"parts.json").read_text())
  for p in self.multi["parts"]:
   f=PRIVATE/p["path"]
   self.assertEqual(p["frameSha256"],sha(f))
   c=next(x for x in canonical["parts"]
          if x["yawDeg"]==p["yawDeg"] and x["semanticId"]==p["semanticId"])
   self.assertEqual(c["mesh"]["vertexIds"],p["mesh"]["vertexIds"])
   self.assertEqual(c["mesh"]["triangles"],p["mesh"]["triangles"])
   if p["yawDeg"]==90:self.assertEqual(c["frameSha256"],p["frameSha256"])

 def test_real_image_derived_correspondence(self):
  j=self.landmark
  self.assertEqual(j["status"],"IMAGE_DERIVED_LANDMARKS_REGISTERED")
  self.assertEqual(len(j["landmarks"]),13)
  self.assertTrue(all(j["qaGates"].values()))
  self.assertTrue(len(j["holdoutPredictions"]["22.5"])>=10)
  self.assertTrue(len(j["holdoutPredictions"]["67.5"])>=8)
  near=j["landmarks"]["eye.near.iris"]
  self.assertEqual(near[0]["source"],"PSD_ALPHA_CONNECTED_COMPONENT")
  self.assertEqual(near[1]["source"],"PSD_ALPHA_CONNECTED_COMPONENT")
  self.assertLess(near[0]["xy"][0],near[1]["xy"][0])
  self.assertFalse(j["landmarks"]["eye.far.iris"][2]["visible"])
  self.assertFalse(j["landmarks"]["hair.clip.center"][2]["visible"])
  self.assertEqual(sha(PRIVATE/j["contactSheet"]),j["contactSHA256"])

 def test_browser_source_and_heldout_art_status(self):
  f=MV/"vdd-canvas/canvas-qa.json"
  obj=json.loads(f.read_text())
  self.assertEqual(obj["source"],"seethrough-paired")
  self.assertEqual(obj["status"],"CAPTURED_FOR_ANATOMICAL_INSPECTION")
  self.assertEqual(len(obj["outputs"]),5)
  for rec in obj["outputs"]:self.assertEqual(sha(rec["path"]),rec["sha256"])
  opacity=json.loads((MV/"holdout-qa.json").read_text())
  edges=json.loads((MV/"texture-qa.json").read_text())
  self.assertEqual(opacity["status"],"PASS_HOLDOUT_COVERAGE")
  self.assertEqual(edges["status"],"REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE")
  self.assertEqual(edges["failed"],2)

 @unittest.skipUnless((MV/"turn-gif-qa.json").is_file(),"P5 actual browser frames and GIF")
 def test_p5_animated_motion_preview(self):
  j=json.loads((MV/"turn-gif-qa.json").read_text())
  self.assertEqual(j["sourceFrameCount"],37)
  self.assertEqual(j["GIFFrames"],72)
  self.assertEqual(sha(MV/"p0-psd-paired-vdd-turn.gif"),j["GIFSHA256"])

 @unittest.skipUnless((P5/"p5-package-qa.json").is_file(),"P5 packager completed")
 def test_p5_review_archive(self):
  import zipfile
  data=json.loads((P5/"p5-package-qa.json").read_text())
  file=Path(data["archivePath"])
  self.assertEqual(sha(file),data["sha256"])
  self.assertTrue(data["internalHashesVerified"])
  with zipfile.ZipFile(file) as z:
   self.assertIsNone(z.testzip())
   doc=json.loads(z.read("package-manifest.json"))
   self.assertEqual(doc["characterId"],"p0_character_001")
   self.assertEqual(doc["PSDViewAngles"],[0,45])
   self.assertEqual(doc["registeredSemanticViews"],39)

if __name__=="__main__":
 unittest.main(verbosity=2)
