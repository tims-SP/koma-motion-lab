import importlib.util
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).with_name('p15_179_rootless_crown_mid_yaw_vdd.py')
spec=importlib.util.spec_from_file_location('p15_179_rootless_crown_mid_yaw_vdd',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RootlessCrownMidYawVDDTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.evaluate(save=False)
 def test_native_keyviews_are_pixel_exact(self):
  self.assertTrue(self.q['gate']['allNativeKeyframesExact'])
  for method in self.q['methods'].values():
   self.assertTrue(method['nativeKeyframesPixelExact'])
 def test_deep_body_is_unchanged(self):
  self.assertTrue(self.q['gate']['allDeepBodyExact'])
  for method in self.q['methods'].values():
   self.assertTrue(method['bodyBelowY125Exact'])
 def test_selected_midviews_have_one_connected_top(self):
  selected=self.q['selectedCandidate']
  self.assertEqual(selected,'root_local__anchor_owner')
  self.assertTrue(self.q['methods'][selected]['midframesConnected'])
  self.assertEqual(self.q['methods'][selected]['topConnectedComponents'][1],1)
  self.assertEqual(self.q['methods'][selected]['topConnectedComponents'][3],1)
 def test_loop_area_and_root_patch_are_bounded(self):
  self.assertTrue(self.q['gate']['selectedLoopAreaWithin25Percent'])
  self.assertTrue(self.q['gate']['selectedRootPatchRGBMAEWithin5'])
  for angle,ratio in self.q['selectedAirLoopAreaRatio'].items():
   self.assertGreaterEqual(ratio,.70)
   self.assertLessEqual(ratio,1.30)
  for value in self.q['selectedRootPatchRGBMAE'].values():
   self.assertLessEqual(value,5.0)
 def test_visual_candidate_accepted_without_production_adoption(self):
  self.assertTrue(self.q['gate']['agentVisualReviewPassed'])
  self.assertTrue(self.q['gate']['passes'])
  self.assertTrue(self.q['visualAccepted'])
  self.assertFalse(self.q['productionRendererUpdated'])
  self.assertTrue(self.q['gate']['temporalMetricRegressionRecorded'])
 def test_selected_render_assets_exist(self):
  folder=m.OUT/self.q['selectedCandidate']
  for angle in m.ANGLES:
   path=folder/(f'yaw{angle:06.2f}'.replace('.','p')+'.png')
   with Image.open(path) as im:
    self.assertEqual(im.mode,'RGBA')
    self.assertEqual(im.size,(443,443))
if __name__=='__main__':unittest.main()
