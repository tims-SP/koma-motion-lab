import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_161_root_source_extension.py')
s=importlib.util.spec_from_file_location('p15_161_root_source_extension',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class SourceRootExtensionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.evaluate(save=False)
 def test_exact_source_partition(self):
  src=m.keyframes()
  for angle in m.KEYS:
   loop,rest,info=m.extract_extended(src[angle],m.control_points(m.extract(src[angle])[0]['loop_visible'],angle)[0],19,.85)
   self.assertTrue(info['sourceRecompositionExact'])
   combined=rest.copy()
   mask=loop[...,3]>0
   combined[mask]=loop[mask]
   self.assertTrue(np.array_equal(combined,src[angle]))
 def test_root_pixels_are_not_yet_recovered(self):
  candidates=self.qa['rootCandidateSources']
  self.assertEqual(candidates['root_band_13']['90']['extensionBelowCutPixels'],0)
  self.assertEqual(candidates['root_band_19']['90']['extensionBelowCutPixels'],0)
  self.assertEqual(candidates['root_band_19']['135']['extensionBelowCutPixels'],0)
  self.assertLessEqual(candidates['root_band_19']['112.5']['extensionBelowCutPixels'],3)
  self.assertFalse(self.qa['gate']['realSourceRootPixelsRecovered'])
  self.assertFalse(self.qa['gate']['allViewRootPixelsRecovered'])
 def test_visual_topology_not_accepted(self):
  baseline=self.qa['methods']['reference']
  self.assertEqual(baseline['topConnectedComponents'],[1,1,1,1,1])
  for name in ('root_band_13','root_band_19'):
   v=self.qa['methods'][name]
   self.assertEqual(v['topConnectedComponents'],[1,2,1,3,1])
   self.assertGreater(v['maxAdjacentRGBMAE'],baseline['maxAdjacentRGBMAE'])
   self.assertTrue(v['nativeKeyframesPixelExact'])
  self.assertFalse(self.qa['gate']['allMidviewsConnected'])
  self.assertFalse(self.qa['gate']['passes'])
 def test_source_and_art_approval(self):
  self.assertTrue(self.qa['sourceMaterialPreserved'])
  self.assertFalse(self.qa['artistVerifiedRootOutline'])
  self.assertFalse(self.qa['hiddenCrownUnderpaintValidated'])
  self.assertFalse(self.qa['visualAccepted'])
  self.assertFalse(self.qa['selectedForProduction'])
if __name__=='__main__':unittest.main()
