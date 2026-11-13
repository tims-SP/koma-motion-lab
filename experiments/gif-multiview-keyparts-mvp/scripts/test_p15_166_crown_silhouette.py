import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_166_crown_silhouette.py')
spec=importlib.util.spec_from_file_location('p15_166_crown_silhouette',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CrownSilhouetteTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.qa=m.evaluate(save=False)
 def test_crown_separation_is_reversible_outside_air(self):
  original=m.keyframes()[112.5]
  for radius in (5,9,13):
   separated,crown,air,edge=m.separate(original,radius)
   self.assertTrue(np.array_equal(crown[~air],original[~air]))
   self.assertTrue(np.array_equal(separated[~air],original[~air]))
   self.assertEqual(len(edge),443)
   self.assertGreater(int(air.sum()),1000)
 def test_native_keys_and_retained_crown_exact(self):
  self.assertTrue(self.qa['gate']['allFiveFrameSourceKeysExact'])
  self.assertTrue(self.qa['gate']['crownPixelsPreserved'])
  for candidate in ('crown_05','crown_09','crown_13'):
   self.assertTrue(self.qa['methods'][candidate]['nativeKeysPixelExact'])
   for meta in self.qa['crownBoundaries'][candidate].values():
    self.assertTrue(meta['preservedCrownPixels'])
    self.assertEqual(meta['crownAlphaChangedPixels'],0)
 def test_intermediate_connectivity_not_accepted(self):
  self.assertEqual(self.qa['methods']['reference']['topComponents'],[1,1,1,1,1])
  for candidate in ('crown_05','crown_09','crown_13'):
   self.assertEqual(self.qa['methods'][candidate]['topComponents'],[1,2,1,1,1])
   self.assertGreater(self.qa['methods'][candidate]['maxAdjacentRGBMAE'],self.qa['methods']['reference']['maxAdjacentRGBMAE'])
  self.assertFalse(self.qa['gate']['allMidviewLoopsConnected'])
  self.assertFalse(self.qa['gate']['candidateImprovesMotion'])
 def test_art_acceptance_is_separate(self):
  self.assertFalse(self.qa['originalRootlessCrownPaintApproved'])
  self.assertFalse(self.qa['physicallyMatchedHairRootsApproved'])
  self.assertFalse(self.qa['continuousVisualAccepted'])
  self.assertFalse(self.qa['productionSelected'])
  self.assertFalse(self.qa['gate']['passes'])
if __name__=='__main__': unittest.main()
