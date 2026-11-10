"""P15-13 structural source and local alignment acceptance regression."""
import json,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
import p15_13_structural_condition as source
import p15_13_local_alignment as align

class P15ThirteenTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=json.loads(source.REPORT.read_text())
  cls.a=json.loads(align.QA.read_text())
  cls.b=json.loads((source.OUT/"browser/qa.json").read_text())
  cls.camera=json.loads((source.ROOT/"evidence/p15-12-camera-proxy-qa.json").read_text())

 def test_character_source_sha(self):
  self.assertEqual(self.d["characterId"],"p0_character_001")
  self.assertEqual(self.d["sourceCameraSHA256"],source.sha(source.CAMERA))
  self.assertEqual(self.d["sourcePaintedCandidatesSHA256"],source.sha(source.ART))
  self.assertEqual(self.d["sourceSemanticArcSHA256"],source.sha(source.SEM))
  self.assertEqual(self.a["sourceConditionSHA256"],source.sha(source.REPORT))

 def test_camera_iris_calibration(self):
  self.assertEqual(self.d["angles"],[57.5,60.0])
  self.assertEqual(len(self.d["detectorBiasPerEye"]),2)
  for f in self.d["frames"]:
   self.assertEqual(len(f["actualIrisColorFeatures"]),2)
   self.assertEqual(len(f["cameraProjectedIrisTargets"]),2)
   self.assertTrue(all(0<e<150 for e in f["irisFeatureDeviationPixels"]))
   self.assertFalse(f["isAnatomicalLandmarkDetection"])

 def test_generated_conditions_have_exact_sha(self):
  for f in self.d["frames"]:
   self.assertEqual(len(f["outputs"]),4)
   for role,detail in f["outputs"].items():
    image=source.PRIVATE/detail["path"]
    self.assertEqual(source.sha(image),detail["sha256"])
    with Image.open(image) as img:
     self.assertEqual(img.size,(1024,1024))
     self.assertEqual(img.mode,"L" if role in ["owner","lineart"] else "RGB")

 def test_per_role_owner_counts_and_masks(self):
  self.assertEqual(len(self.d["sourceRoleOrder"]),13)
  for f in self.d["frames"]:
   self.assertEqual(f["artmeshRoleCount"],13)
   owner=source.load(source.PRIVATE/f["outputs"]["owner"]["path"],"L")
   self.assertGreaterEqual(int(owner.max()),10)
   self.assertLessEqual(int(owner.max()),13)
   self.assertGreater(int(np.count_nonzero(owner)),180000)
   for role,info in f["semanticLayers"].items():
    self.assertEqual(source.sha(source.PRIVATE/info["path"]),info["sha256"])
    self.assertGreaterEqual(info["visiblePixels"],0)

 def test_heatmaps_have_distinct_feature_groups(self):
  for f in self.d["frames"]:
   heat=source.load(source.PRIVATE/f["outputs"]["heatmap"]["path"])
   self.assertTrue(all(np.max(heat[:,:,c])>100 for c in range(3)))
   self.assertLess(np.count_nonzero(heat),150000)
   edge=source.load(source.PRIVATE/f["outputs"]["lineart"]["path"],"L")
   self.assertGreater(np.count_nonzero(edge),2000)

 def test_registered_paintings_improve_color_feature_location(self):
  self.assertEqual(len(self.a["frames"]),2)
  for row in self.a["frames"]:
   self.assertEqual(source.sha(source.PRIVATE/row["output"]["path"]),row["output"]["sha256"])
   self.assertLess(row["sum"] if "sum" in row else sum(row["registeredErrorsPixels"]),
                   sum(row["originalErrorsPixels"])*.85)
   self.assertGreater(row["aggregateErrorReductionFraction"],.15)
   self.assertEqual(len(row["detectedIrisComponents"]),2)
   self.assertLess(row["maximumPixelRemap"],130)
   with Image.open(source.PRIVATE/row["output"]["path"]) as image:
    self.assertEqual(image.mode,"RGB")
    self.assertEqual(image.size,(1024,1024))

 def test_independent_painting_gate_remains_explicit(self):
  self.assertEqual(self.d["approvedIndependentKeyPaintings"],0)
  self.assertEqual(self.d["approvedHiddenUnderpainting"],0)
  self.assertFalse(self.d["imageEndpointWithHardConditioningVerified"])
  self.assertEqual(self.a["independentPaintingsApproved"],0)

 def test_chromium_desktop_mobile_sources(self):
  b=self.b
  self.assertEqual(b["status"],"STRUCTURAL_CHANNELS_HTML_VERIFIED")
  self.assertEqual(b["captureCount"],10)
  self.assertEqual(b["totalImageLoads"],40)
  self.assertEqual(b["javascriptErrors"],[])
  self.assertEqual(b["failedRequests"],[])
  self.assertEqual({s["viewport"] for s in b["captures"]},{"desktop","mobile"})
  for capture in b["captures"]:
   self.assertEqual(capture["sourceCount"],4)
   self.assertEqual(source.sha(ROOT/capture["relativePath"]),capture["sha256"])

if __name__=="__main__":unittest.main()
