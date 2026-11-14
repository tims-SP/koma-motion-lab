"""P15-09 P5 physical-anchor geometry, intermediate frame and browser checks."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
import p15_09_anchor_pose as pose
import p15_09_midarc as midarc
from p8_semantic_occlusion import output_frame_id

class P15NineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pose=json.loads((ROOT/"evidence/p15-09-anchor-pose-qa.json").read_text())
  cls.arc=json.loads((ROOT/"evidence/p15-09-midarc-qa.json").read_text())
  cls.browser=json.loads((ROOT/"private-assets/p15-09-midarc/browser/qa.json").read_text())

 def test_approved_p0_source_chain(self):
  _,landmarks,source=pose.source_checks()
  self.assertEqual(source["sha256"],self.pose["sourceArtworkSha256"])
  self.assertEqual(pose.sha(pose.LANDMARKS),self.pose["sourceLandmarksSha256"])
  self.assertEqual(len(pose.anchors(landmarks)),20)
  self.assertEqual(self.pose["characterId"],"p0_character_001")

 def test_two_eyes_and_hairclip_anchor_tracking(self):
  pts={x["semantic"]:x for x in self.pose["controlPoints"]}
  self.assertIn("eye.near.iris",pts)
  self.assertIn("eye.far.iris",pts)
  self.assertIn("hair.clip.center",pts)
  self.assertGreater(pts["hair.clip.center"]["target"][0],700)
  self.assertGreater(pts["eye.near.iris"]["target"][0],pts["eye.near.iris"]["source"][0])
  self.assertLess(pts["eye.far.iris"]["target"][0],pts["eye.far.iris"]["source"][0])
  self.assertGreater(pts["eye.far.iris"]["target"][0]-pts["eye.near.iris"]["target"][0],70)

 def test_anchor_55_reference_lineage(self):
  f=pose.DEST/"yaw055-p5-anchor-reference.png"
  self.assertEqual(pose.sha(f),self.pose["generatedImageSha256"])
  with Image.open(f) as im:
   self.assertEqual(im.size,(1024,1024))
   self.assertEqual(im.mode,"RGBA")
   self.assertGreater(np.count_nonzero(np.asarray(im)[:,:,3]>128),300000)
  self.assertEqual(self.pose["artisticStatus"],"POSE_REFERENCE_REQUIRES_VISUAL_APPROVAL")

 def test_arc_keyframe_exactness(self):
  p45=midarc.rgba(pose.SOURCE)
  p65=midarc.rgba(midarc.SOURCE65)
  a45=midarc.rgba(midarc.OUT/output_frame_id(45))
  a55=midarc.rgba(midarc.OUT/output_frame_id(55))
  a65=midarc.rgba(midarc.OUT/output_frame_id(65))
  self.assertTrue(np.array_equal(p45,a45))
  self.assertTrue(np.array_equal(p65,a65))
  self.assertTrue(np.array_equal(a55,midarc.rgba(pose.DEST/"yaw055-p5-anchor-reference.png")))
  self.assertEqual(len(self.arc["renderedFrames"]),9)
  for entry in self.arc["renderedFrames"]:
   f=midarc.OUT/output_frame_id(entry["yaw"])
   self.assertEqual(pose.sha(f),entry["sha256"])

 def test_local_pose_continuity_vs_baseline(self):
  before=[x for x in self.arc["adjacentGeometry"] if x["to"]<=55]
  after=[x for x in self.arc["adjacentGeometry"] if x["from"]>=55]
  self.assertEqual(len(before),4)
  self.assertEqual(len(after),4)
  self.assertGreater(min(x["anchorAlphaIoU"] for x in before),.98)
  self.assertTrue(all(x["anchorAlphaIoU"]>x["baselineAlphaIoU"] for x in before))
  self.assertTrue(any(x["anchorAlphaIoU"]<x["baselineAlphaIoU"] for x in after))
  self.assertEqual(self.arc["artisticStatus"],"NEEDS_INDEPENDENT_POSE_AND_OCCLUSION_ART")

 def test_chromium_source_loaded_and_screenshots_hashed(self):
  qa=self.browser
  self.assertEqual(qa["captureCount"],6)
  self.assertEqual(qa["sourceImagesLoaded"],18)
  self.assertEqual(qa["javascriptErrors"],[])
  self.assertEqual(qa["failedRequests"],[])
  self.assertEqual(qa["status"],"HTML_SOURCE_AND_RENDERED_FRAMES_VERIFIED")
  for frame in qa["screenshots"]:
   path=ROOT/frame["imagePath"]
   self.assertEqual(pose.sha(path),frame["sha256"])
   self.assertEqual(frame["imageCount"],3)

if __name__=="__main__":unittest.main()
