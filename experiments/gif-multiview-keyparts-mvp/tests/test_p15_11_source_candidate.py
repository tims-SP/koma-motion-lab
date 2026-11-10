"""P15-11 independent artwork source, handedness and browser evidence QA."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
from p15_11_candidate_review import ASSETS, CANDIDATES, MANIFEST, OUT, sha, silhouette, gold_mark


class P15ElevenCandidateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.input=json.loads(MANIFEST.read_text())
  cls.qa=json.loads(OUT.read_text())
  cls.browser=json.loads((CANDIDATES/"browser/qa.json").read_text())

 def test_candidate_source_registry_and_hash(self):
  self.assertEqual(self.input["characterId"],"p0_character_001")
  self.assertEqual(len(self.input["candidates"]),4)
  for entry in self.input["candidates"]:
   self.assertEqual(sha(CANDIDATES/entry["file"]),entry["sha256"])
   self.assertEqual(entry["visualDisposition"],"REWORK_REQUIRED")
   self.assertEqual(len(entry["sourceBlobSHA"]),40)

 def test_original_reference_sources(self):
  self.assertEqual({r["yawDeg"] for r in self.input["referenceImages"]},{45,65})
  for entry in self.input["referenceImages"]:
   self.assertEqual(sha(ASSETS/entry["path"]),entry["sha256"])
  reference=Image.open(ASSETS/self.input["referenceImages"][0]["path"])
  self.assertTrue(gold_mark(reference)["present"])

 def test_all_four_candidate_canvases(self):
  for item in self.input["candidates"]:
   with Image.open(CANDIDATES/item["file"]) as picture:
    self.assertEqual(picture.mode,"RGB")
    self.assertEqual(picture.size,(1024,1024))
    coverage,bbox=silhouette(picture)
    self.assertGreater(coverage,60000)
    self.assertLess(coverage,850000)
    self.assertLess(bbox[0],bbox[2])
    self.assertLess(bbox[1],bbox[3])

 def test_quality_acceptance_is_independent(self):
  self.assertEqual(self.qa["generatedCandidateCount"],4)
  self.assertEqual(self.qa["independentPaintingAccepted"],0)
  self.assertEqual(self.qa["semanticPaintedLayersAccepted"],0)
  self.assertEqual(self.qa["formalArtGate"],"P15_11_IDENTITY_AND_POSE_REVIEW_REQUIRED")
  self.assertFalse(self.qa["originalHeroSHA256Verified"])
  for rec in self.qa["sourceRecords"]:
   self.assertFalse(rec["canBeUsedAsRendererKeyframe"])
   self.assertTrue(rec["manualVisualObservations"])

 def test_contact_is_traceable(self):
  p=ASSETS/self.qa["candidateContactPath"]
  self.assertEqual(sha(p),self.qa["candidateContactSHA256"])
  with Image.open(p) as im:
   self.assertEqual(im.size,(990,730))

 def test_chromium_two_viewports_source_images(self):
  browser=self.browser
  self.assertEqual(browser["status"],"SOURCE_PREVIEW_AND_BROWSER_VERIFIED")
  self.assertEqual(browser["captureCount"],2)
  self.assertEqual(browser["sourceImageLoads"],12)
  self.assertFalse(browser["javascriptErrors"])
  self.assertFalse(browser["requestFailures"])
  for shot in browser["screenshots"]:
   self.assertEqual(shot["sourceCount"],6)
   self.assertEqual(sha(ROOT/shot["path"]),shot["sha256"])

if __name__=="__main__":unittest.main()
