import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_155_anchored_crown_motion.py')
s=importlib.util.spec_from_file_location('p15_155_anchored_crown_motion',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CrownAnchorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.run(save=False)
 def test_zero_shift_reassembles_exact_source(self):
  self.assertTrue(self.q['zeroShiftSourceExact'])
  self.assertTrue(self.q['results']['anchored_00']['rootPixelExact'])
 def test_anchor_is_fixed_under_deformation(self):
  original=m.keyframes()[90.]
  assets,base,_=m.split(original)
  for dx in (2,4,8):
   transformed=m.anchor_warp(assets['left_fine_visible'],dx)
   self.assertTrue(np.array_equal(transformed[54:],assets['left_fine_visible'][54:]))
   self.assertTrue(self.q['results'][f'anchored_{dx:02}']['rootPixelExact'])
 def test_air_exposure_distinguished_from_crown_holes(self):
  for dx in (2,4,8):
   baseline=self.q['results'][f'rigid_{dx:02}']
   anchored=self.q['results'][f'anchored_{dx:02}']
   self.assertGreater(baseline['exposedCrownPixels'],0)
   self.assertEqual(anchored['exposedCrownPixels'],0)
   self.assertEqual(anchored['exposedFormerHairPixels'],anchored['exposedAirPixels'])
 def test_local_difference_reduced(self):
  for dx in (2,4,8):
   a=self.q['results'][f'anchored_{dx:02}']
   b=self.q['results'][f'rigid_{dx:02}']
   self.assertLess(a['localRGBMAE'],b['localRGBMAE'])
 def test_visual_acceptance_separate(self):
  self.assertFalse(self.q['physicalSecondStrandIdentityVerified'])
  self.assertFalse(self.q['continuousYawVisualAccepted'])
  self.assertFalse(self.q['artistApproved'])
if __name__=='__main__':unittest.main()
