import importlib.util
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).with_name('p15_177_crown_root_repaint.py')
spec=importlib.util.spec_from_file_location('p15_177_crown_root_repaint',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CrownRootRepaintTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.run(save=False)
 def test_three_native_view_sources_and_exported_rgba(self):
  self.assertTrue(self.q['gate']['threeViewsRepainted'])
  for angle in m.KEYS:
   folder=m.OUT/'local'/m.TAGS[angle]
   for name in ('ahoge.png','crown-motion-underpaint.png','crown-static-alpha-safe.png'):
    with Image.open(folder/name) as img:
     self.assertEqual(img.mode,'RGBA')
     self.assertEqual(img.size,(443,443))
 def test_alpha_ownership_and_deep_art_preservation(self):
  self.assertTrue(self.q['gate']['noDoubleAlphaOwnership'])
  self.assertTrue(self.q['gate']['originalAlphaOutsideRootAirPreserved'])
  self.assertTrue(self.q['gate']['belowY125PixelExact'])
  for angle in m.KEYS:
   src,strand,old,new,key,owner,mask,composite,info=m.repaint(angle,2)
   self.assertTrue(info['deepHeadExact'])
   self.assertTrue(info['sourceAlphaOutsideRootAirPreserved'])
   self.assertTrue(np.array_equal(new[125:],src[125:]))
   self.assertEqual(info['doubleAlphaPixels'],0)
 def test_repaint_scope_is_exact(self):
  self.assertTrue(self.q['gate']['inpaintInsideSourceRootMaskAndAir'])
  self.assertTrue(self.q['gate']['newCompositeDeltaLocalized'])
  for entries in self.q['methods'].values():
   for entry in entries.values():
    self.assertGreater(entry['seedPixels'],0)
    self.assertGreater(entry['paintPixels'],0)
    self.assertGreater(entry['actualEditedPixels'],0)
    self.assertEqual(entry['candidateDeltaOutsideRootRegion'],0)
    self.assertTrue(entry['underpaintChangedOnlyMaskAndRootAir'])
 def test_visual_gate_not_inferred_from_pixel_tests(self):
  self.assertFalse(self.q['gate']['rootlessCrownVisualAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['visualAccepted'])
  self.assertFalse(self.q['midYawRendered'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
