#!/usr/bin/env python3
"""Measured P15-195 regression and preservation checks."""
import json,unittest,sys
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'private-assets/exports/p15-195-width-curvature-regularization'
E=ROOT/'evidence/p15-195-width-curvature-regularization-qa.json'
class WidthCurvatureRegularizationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_all_thirteen_angle_outputs(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  for method in self.q['methods']:
   paths=list((OUT/method).glob('yaw*.png'))
   self.assertEqual(len(paths),13)
   for p in paths:
    with Image.open(p) as im:self.assertEqual(im.size,(443,443))
  self.assertTrue((OUT/'index.html').exists())
 def test_source_keys_strand_and_deep_body(self):
  self.assertTrue(self.q['gate']['allNativeKeysExact'])
  self.assertTrue(self.q['gate']['allDeepBodyExact'])
  self.assertTrue(self.q['gate']['allMidframesSingleComponent'])
  self.assertTrue(self.q['gate']['allMidframesHaveCrownCrossing'])
 def test_actual_smoothing_preserves_endpoints(self):
  sys.path.insert(0,str(ROOT/'scripts'))
  from p15_195_width_curvature_regularization import regularize
  from p15_187_full_skeleton_vdd import source_geometry
  from p15_129_ahoge_ownership import keyframes
  from p15_194_multifeature_correspondence import parameterize
  src=parameterize(source_geometry(keyframes()[112.5],112.5))[0]
  new=regularize(src,1.5,3)
  np.testing.assert_array_equal(src['curve'][0],new['curve'][0])
  np.testing.assert_array_equal(src['curve'][-1],new['curve'][-1])
  self.assertGreater(float(np.max(np.abs(src['curve'][1:-1]-new['curve'][1:-1]))),0)
  self.assertGreater(float(np.max(np.abs(src['width'][1:-1]-new['width'][1:-1]))),0)
 def test_diagnostic_choice_respects_seam_and_motion(self):
  metrics=self.q['methods']
  self.assertEqual(self.q['selectedDiagnosticMethod'],'curve_s1p5_width_s3')
  chosen=metrics['curve_s1p5_width_s3'];baseline=metrics['feature_linear']
  self.assertLess(chosen['maxAdjacentLocalRGBMAE'],baseline['maxAdjacentLocalRGBMAE'])
  self.assertLess(chosen['maxAdjacentRootCrossingStepPixels'],baseline['maxAdjacentRootCrossingStepPixels'])
  self.assertLess(chosen['maxAdjacentColorSeamChange'],baseline['maxAdjacentColorSeamChange'])
  self.assertGreater(metrics['curve_s3_width_s6']['maxAdjacentColorSeamChange'],baseline['maxAdjacentColorSeamChange'])
 def test_production_acceptance_is_not_claimed(self):
  self.assertFalse(self.q['gate']['globalTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['visualAccepted'])
  self.assertFalse(self.q['gate']['sourceShoulderSemanticIdentityApproved'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
