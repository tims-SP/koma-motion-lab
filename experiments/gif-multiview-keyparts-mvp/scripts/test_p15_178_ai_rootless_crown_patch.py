import importlib.util
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).with_name('p15_178_ai_rootless_crown_patch.py')
spec=importlib.util.spec_from_file_location('p15_178_ai_rootless_crown_patch',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class AIRootlessCrownPatchTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.run(save=False)
 def test_three_registered_ai_sources_are_preserved(self):
  self.assertTrue(self.q['gate']['threeAIViewsAvailable'])
  for angle in m.KEYS:
   with Image.open(m.AI[angle]) as im:
    self.assertEqual(im.mode,'RGB')
    self.assertEqual(im.size,(1024,560))
   detail=self.q['perMode']['local'][f'{angle:g}']
   self.assertGreaterEqual(detail['registration']['inliers'],8)
 def test_root_air_and_double_ownership_are_cleared(self):
  self.assertTrue(self.q['gate']['rootAirAlphaCleared'])
  self.assertTrue(self.q['gate']['noDoubleAlpha'])
  for angle in m.KEYS:
   src,strand,motion,static,owner,weight,candidate,comp,info=m.make(angle,'local')
   self.assertTrue(info['rootAirAlphaCleared'])
   self.assertEqual(info['doubleAlphaPixels'],0)
   self.assertTrue(np.all(motion[weight>0,3]>=0))
 def test_only_root_patch_changes_canonical_rgb(self):
  self.assertTrue(self.q['gate']['outsidePatchRGBExact'])
  self.assertTrue(self.q['gate']['compositeDiffLocalized'])
  for angle in m.KEYS:
   src,strand,motion,static,owner,weight,candidate,comp,info=m.make(angle,'local')
   self.assertTrue(info['outsidePatchRGBExact'])
   self.assertEqual(info['compositeDiffOutsidePatch'],0)
 def test_native_alpha_and_deep_head_are_preserved(self):
  self.assertTrue(self.q['gate']['sourceAlphaExactOutsideRootAir'])
  self.assertTrue(self.q['gate']['deepHeadExact'])
  for angle in m.KEYS:
   src,strand,motion,static,owner,weight,candidate,comp,info=m.make(angle,'local')
   self.assertTrue(info['alphaExactOutsideRootAir'])
   self.assertTrue(info['deepHeadExact'])
   self.assertTrue(np.array_equal(candidate[125:],src[125:]))
 def test_visual_and_technical_gate(self):
  self.assertTrue(self.q['gate']['rootlessCrownVisualAccepted'])
  self.assertTrue(self.q['gate']['passes'])
  self.assertTrue(self.q['visualAccepted'])
  self.assertFalse(self.q['midYawRendered'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
