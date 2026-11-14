#!/usr/bin/env python3
"""P15-193 three-source landmark VDD acceptance and 13-yaw regression."""
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-193-landmark-parameter-vdd-qa.json'
OUT=ROOT/'private-assets/exports/p15-193-landmark-parameter-vdd'
class LandmarkVDDTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_all_thirteen_angles_for_all_methods(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  for method in ('arc_linear','landmark_linear','landmark_pchip'):
   files=list((OUT/method).glob('yaw*.png'))
   self.assertEqual(len(files),13)
   for f in files:
    with Image.open(f) as im:self.assertEqual(im.size,(443,443))
 def test_native_control_landmarks_aligned_to_shared_coordinate(self):
  self.assertEqual(self.q['landmarkNode'],32)
  for data in self.q['sourceLandmarks'].values():
   self.assertEqual(data['newCrossingNode'],32)
   self.assertLess(data['landmarkResidualPixels'],1)
   self.assertTrue(data['freeTipExact'])
  self.assertTrue(self.q['gate']['allSourceLandmarksWithinPixel'])
 def test_source_keyframes_head_and_single_strand_preserved(self):
  for method in self.q['methods'].values():
   self.assertTrue(method['allNativeKeysExact'])
   self.assertTrue(method['allDeepBodyExact'])
   self.assertTrue(method['allMidframesSingleComponent'])
  self.assertTrue(self.q['gate']['allNativeKeysExact'])
 def test_geometry_improvement_must_include_root_motion(self):
  m=self.q['methods']
  self.assertEqual(self.q['selectedDiagnosticMethod'],'arc_linear')
  self.assertLess(m['landmark_linear']['maxAdjacentLocalRGBMAE'],m['arc_linear']['maxAdjacentLocalRGBMAE'])
  self.assertGreater(m['landmark_linear']['maxAdjacentRootCrossingStepPixels'],m['arc_linear']['maxAdjacentRootCrossingStepPixels'])
  self.assertGreater(m['landmark_pchip']['maxAdjacentRootCrossingStepPixels'],m['arc_linear']['maxAdjacentRootCrossingStepPixels'])
  self.assertFalse(self.q['gate']['crossingImprovedOverArc'])
 def test_global_gate_and_production_unapproved(self):
  self.assertTrue(self.q['gate']['localTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['globalTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['visualAccepted'])
  self.assertFalse(self.q['gate']['semanticCorrespondenceApproved'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
