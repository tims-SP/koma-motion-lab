"""P15-12 P0 camera calibration, generated art and Chromium QA."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

BASE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(BASE/"scripts"))
import p15_12_camera_proxy as camera
import p15_12_guided_qa as guided


class CameraProxyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.camera=json.loads(camera.QA.read_text())
  cls.art=json.loads((BASE/"evidence/p15-12-guided-candidate-qa.json").read_text())
  cls.browser=json.loads((camera.OUT/"browser/qa.json").read_text())
  cls.p5=json.loads(camera.REG.read_text())

 def test_identity_source(self):
  self.assertEqual(self.camera["characterId"],"p0_character_001")
  self.assertEqual(self.camera["sourceLandmarkSHA256"],camera.sha(camera.REG))
  self.assertEqual(self.camera["sourcePartRegistrySHA256"],camera.sha(camera.PARTS))
  self.assertEqual(self.camera["status"],"NUMERIC_CAMERA_PROXY_VERIFIED")

 def test_exact_registered_45_and_90_anchor_projection(self):
  for row in self.camera["frames"]:
   if row["yaw"] not in (45,90):continue
   for role,record in row["anchors"].items():
    original=camera.obs(self.p5["landmarks"][role],row["yaw"])
    if original and original.get("visible") and record["xy"] is not None:
     self.assertLessEqual(abs(record["xy"][0]-original["xy"][0]),0.002,role)
     self.assertLessEqual(abs(record["xy"][1]-original["xy"][1]),0.002,role)

 def test_12_role_projection_camera_order(self):
  self.assertEqual(self.camera["roleCount"],12)
  frames=[r for r in self.camera["frames"] if 45<=r["yaw"]<=65]
  self.assertEqual(len(frames),6)
  gaps=[r["eyeNoseGap"] for r in frames]
  self.assertTrue(all(a>b for a,b in zip(gaps,gaps[1:])),gaps)
  self.assertTrue(all(r["clipX"]>700 for r in frames))
  self.assertTrue(all(r["anchors"]["eye.near.iris"]["xy"][0] <
                      r["anchors"]["nose"]["xy"][0] <
                      r["anchors"]["eye.far.iris"]["xy"][0] for r in frames))

 def test_visibility_uncertainty_is_explicit(self):
  frame=next(r for r in self.camera["frames"] if r["yaw"]==60)
  far=frame["anchors"]["eye.far.iris"]
  self.assertLess(far["visibility"],1)
  self.assertGreater(far["visibility"],0)
  self.assertIn("heuristic",self.camera["visibilityUncertainty"])
  self.assertFalse(self.camera["originalHeroSHA256Verified"])

 def test_guides_and_generated_paintings_sha(self):
  for row in self.camera["frames"]:
   if "guide" not in row:continue
   for field in ("conditioning","annotated","sourceGeometry"):
    self.assertEqual(camera.sha(camera.PRIVATE/row["guide"][field+"Path"]),
                     row["guide"][field+"SHA256"])
  self.assertEqual(self.art["generatedCount"],2)
  for row in self.art["generated"]:
   f=camera.PRIVATE/row["sourcePath"]
   self.assertEqual(camera.sha(f),row["sourceSHA256"])
   self.assertEqual(len(row["sourceGitBlob"]),40)
   with Image.open(f) as im:
    self.assertEqual(im.size,(1024,1024))
    self.assertEqual(im.mode,"RGB")

 def test_painting_quality_independent_from_silhouette(self):
  self.assertEqual(self.art["independentlyPaintedKeyframesAdmitted"],0)
  self.assertEqual(self.art["paintedSemanticLayersAdmitted"],0)
  for row in self.art["generated"]:
   self.assertGreater(row["silhouetteIoUWithPoseGuide"],0.5)
   self.assertTrue(row["requiredQualitativeCheck"])
   self.assertFalse(row["acceptedAsIndependentKeyframe"])
  contact=camera.PRIVATE/self.art["contactPath"]
  self.assertEqual(camera.sha(contact),self.art["contactSHA256"])

 def test_real_browser_preview(self):
  b=self.browser
  self.assertEqual(b["status"],"INTERACTIVE_CAMERA_PROXY_HTML_VERIFIED")
  self.assertEqual(b["screenshotCount"],4)
  self.assertEqual(b["sourceImageLoads"],12)
  self.assertEqual(b["javascriptErrors"],[])
  self.assertEqual(b["failedRequests"],[])
  for record in b["captures"]:
   self.assertEqual(record["sourceCount"],3)
   self.assertEqual(camera.sha(BASE/record["relativePath"]),record["sha256"])

if __name__=="__main__":unittest.main()
