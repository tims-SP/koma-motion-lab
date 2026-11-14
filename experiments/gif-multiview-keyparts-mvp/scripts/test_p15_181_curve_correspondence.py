#!/usr/bin/env python3
"""Regression tests for P15-181 single-strand curve correspondence."""
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-181-curve-correspondence-qa.json'
OUT=ROOT/'private-assets/exports/p15-181-curve-correspondence'
ANGLES=(90.,101.25,112.5,123.75,135.)
class CurveCorrespondenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_five_view_render_artifacts(self):
  for name in ('whole_frame_DIS','curve_correspondence'):
   files=list((OUT/name).glob('yaw*.png'))
   self.assertEqual(len(files),5)
   for f in files:
    with Image.open(f) as im:self.assertEqual(im.size,(443,443))
 def test_source_keyframes_and_deep_body_are_exact(self):
  self.assertTrue(self.q['metrics']['nativeKeyframesPixelExact'])
  self.assertTrue(self.q['metrics']['belowY125Exact'])
  self.assertTrue(self.q['gate']['nativeKeyframesPixelExact'])
  self.assertTrue(self.q['gate']['deepBodyExact'])
 def test_curve_interpolation_keeps_single_connected_strand(self):
  self.assertTrue(self.q['metrics']['midframesSingleComponent'])
  self.assertTrue(self.q['gate']['allMidframesSingleComponent'])
  for angle in ('101.25','123.75'):
   self.assertEqual(self.q['intermediateDiagnostics'][angle]['topConnectedComponents'],1)
   self.assertGreater(self.q['intermediateDiagnostics'][angle]['rootExtensionPixels'],0)
 def test_core_loop_area_is_bounded_and_extension_is_separate(self):
  self.assertTrue(self.q['gate']['loopAreaWithin25Percent'])
  self.assertIn('excludes added root-extension pixels',self.q['areaMetricDefinition'])
  for ratio in self.q['loopAreaRatios'].values():self.assertGreaterEqual(ratio,.75);self.assertLessEqual(ratio,1.25)
 def test_temporal_regression_and_visual_gate_are_not_hidden(self):
  self.assertTrue(self.q['gate']['temporalRegressionRecorded'])
  self.assertFalse(self.q['gate']['temporalNoWorseThanBaseline'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['visualAccepted'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
