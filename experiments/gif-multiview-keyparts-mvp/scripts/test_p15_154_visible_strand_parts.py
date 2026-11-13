import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_154_visible_strand_parts.py')
s=importlib.util.spec_from_file_location('p15_154_visible_strand_parts',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class VisibleStrandPartsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.evaluate(save=False)
 def test_canonical_reconstruction(self):
  src=m.keyframes()[90.]
  parts,rest,info=m.split(src)
  rebuilt=rest.copy()
  for part in parts.values():
   on=part[...,3]>24
   rebuilt[on]=part[on]
  self.assertTrue(np.array_equal(rebuilt,src))
  self.assertTrue(info['exclusive'])
  self.assertTrue(info['sourceExact'])
 def test_diagnostic_region_bounds(self):
  info=self.qa['sourcePixelOwnership']
  self.assertEqual(info['fineBBox'],[184,27,190,54])
  self.assertEqual(info['finePixels'],55)
  self.assertGreater(info['loopPixels'],1000)
 def test_moving_region_exposes_unpainted_pixels(self):
  self.assertEqual(self.qa['motionStress']['0']['newAlphaHoles'],0)
  for delta in ('2','4','8'):
   self.assertGreater(self.qa['motionStress'][delta]['newAlphaHoles'],0)
   self.assertGreater(self.qa['motionStress'][delta]['rootROIAlphaHoles'],0)
   self.assertFalse(self.qa['motionStress'][delta]['sourceExact'])
 def test_acceptance_gates_remain_unverified(self):
  self.assertFalse(self.qa['rootGeometryVerified'])
  self.assertFalse(self.qa['physicalStrandIdentityArtistApproved'])
  self.assertFalse(self.qa['independentMotionVisuallyApproved'])
  self.assertFalse(self.qa['crossViewCorrespondenceVerified'])
  self.assertFalse(self.qa['fullYawVisualAccepted'])
if __name__=='__main__':unittest.main()
