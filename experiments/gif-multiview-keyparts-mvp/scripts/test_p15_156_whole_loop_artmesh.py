import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_156_whole_loop_artmesh.py')
s=importlib.util.spec_from_file_location('p15_156_whole_loop_artmesh',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class WholeLoopTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.analyze(save=False)
 def test_one_connected_source_component(self):
  source=m.keyframes()[90.]
  parts,rest,info=m.extract(source)
  self.assertEqual(info['otherUpperPixels'],0)
  self.assertGreater(info['loopVisiblePixels'],1000)
  self.assertTrue(info['recompositionExact'])
 def test_zero_deformation_exact(self):
  self.assertTrue(self.q['zeroShiftPixelExact'])
  original=m.keyframes()[90.]
  parts,rest,_=m.extract(original)
  self.assertTrue(np.array_equal(m.warp_loop(parts['loop_visible'],0),parts['loop_visible']))
 def test_root_stays_fixed(self):
  for dx in (2,4,8):
   r=self.q['results'][f'anchored_{dx:02d}']
   self.assertTrue(r['rootBoundaryBelowExact'])
   self.assertTrue(r['sourcePartBelowRootExact'])
   self.assertEqual(r['exposedCrownPixels'],0)
   self.assertEqual(r['exposedFormerOpaquePixels'],r['exposedAirPixels'])
 def test_full_loop_more_continuous_than_rigid(self):
  for dx in (2,4,8):
   smooth=self.q['results'][f'anchored_{dx:02d}']
   rigid=self.q['results'][f'rigid_{dx:02d}']
   self.assertLess(smooth['rootRGBMAE'],rigid['rootRGBMAE'])
   self.assertLess(smooth['localRGBMAE'],rigid['localRGBMAE'])
 def test_art_and_crossview_remain_separate(self):
  self.assertFalse(self.q['independentHiddenRootAuthored'])
  self.assertFalse(self.q['artistApprovedPhysicalLoop'])
  self.assertFalse(self.q['continuousYawVisualAccepted'])
  self.assertTrue(self.q['nativeSourcePreserved'])
if __name__=='__main__':unittest.main()
