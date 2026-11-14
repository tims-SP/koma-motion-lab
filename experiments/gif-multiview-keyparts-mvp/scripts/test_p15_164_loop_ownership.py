import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_164_loop_ownership.py')
spec=importlib.util.spec_from_file_location('p15_164_loop_ownership',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CanonicalLoopOwnershipTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.evaluate(save=False)
 def test_source_partition_is_exact(self):
  for angle in m.KEYS:
   source=m.keyframes()[angle]
   part,remaining,info=m.owned_key(source)
   owned=part[...,3]>24
   reconstruct=remaining.copy()
   reconstruct[owned]=part[owned]
   self.assertTrue(np.array_equal(reconstruct,source))
   self.assertTrue(info['recompositionExact'])
 def test_bounded_underpaint_scope(self):
  for detail in self.qa['sourceDetails'].values():
   self.assertTrue(detail['sourceBelowY91Unmodified'])
   self.assertTrue(detail['sourceAlphaBelowY54Unmodified'])
   self.assertTrue(detail['sourceHeadExactBeforeInpaint'])
   self.assertGreater(detail['syntheticCrownPixels'],50)
 def test_original_keys_preserved(self):
  self.assertTrue(self.qa['sourceKeyArtUnchanged'])
  for method in self.qa['methods'].values():
   self.assertTrue(method['keyframesPixelExact'])
 def test_continuity_and_alpha_gate(self):
  self.assertEqual(self.qa['methods']['reference']['topConnectedComponents'],[1,1,1,1,1])
  self.assertEqual(self.qa['methods']['source_owned']['topConnectedComponents'],[1,2,1,3,1])
  self.assertEqual(self.qa['methods']['registered_owned']['topConnectedComponents'],[1,2,1,1,1])
  self.assertFalse(self.qa['gate']['bothIntermediateConnected'])
  self.assertFalse(self.qa['gate']['sourceCrownAlphaPreserved'])
  self.assertFalse(self.qa['gate']['beatsReference'])
  self.assertFalse(self.qa['gate']['passes'])
 def test_painter_approval_is_separate(self):
  self.assertFalse(self.qa['actualScalpPaintingApproved'])
  self.assertFalse(self.qa['physicalRootIdentityVerified'])
  self.assertFalse(self.qa['continuousVisualAccepted'])
  self.assertFalse(self.qa['productionSelected'])
if __name__=='__main__':unittest.main()
