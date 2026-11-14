import importlib.util,unittest,hashlib
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_172_crown_underpaint.py')
spec=importlib.util.spec_from_file_location('p15_172_crown_underpaint',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ThreeViewCrownUnderpaintTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.evaluate(save=False)
 def test_source_paired_art_recomposes_exactly(self):
  self.assertTrue(self.q['nativeSourceRecompositionExact'])
  for angle in m.KEYS:
   original,strand,crown,owned,details=m.source_layers(angle)
   assembled=crown.copy();assembled[owned]=strand[owned]
   self.assertTrue(np.array_equal(assembled,original))
 def test_source_provenance_and_crown_scope(self):
  for method in self.q['methods']:
   self.assertEqual(len(self.q['methods'][method]),3)
   for angle,data in self.q['methods'][method].items():
    self.assertTrue(data['headBelowY125Exact'])
    self.assertEqual(data['sourceSHA256'],hashlib.sha256(m.keyframes()[float(angle)].tobytes()).hexdigest())
    self.assertGreater(data['semanticRootPixels'],0)
 def test_reconstruction_is_bounded_to_crown(self):
  self.assertTrue(self.q['gate']['semanticPaintLocality'])
  for angle,data in self.q['methods']['semantic_patch'].items():
   self.assertGreater(data['paintMaskPixels'],40)
   self.assertLess(data['rgbEditedPixels'],1000)
  self.assertEqual(self.q['methods']['semantic_patch']['112.5']['paintMaskPixels'],342)
 def test_art_work_is_not_falsely_admitted(self):
  self.assertTrue(self.q['gate']['allViewsHavePaintMask'])
  self.assertFalse(self.q['gate']['rootStubsVisuallyCleared'])
  self.assertFalse(self.q['gate']['sourceCrownContourVisuallyMatched'])
  self.assertFalse(self.q['gate']['visualPaintApproved'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['hiddenRootAndCrownArtistApproved'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
