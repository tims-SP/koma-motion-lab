import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_153_source_topology.py')
s=importlib.util.spec_from_file_location('p15_153_source_topology',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CanonicalHairSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.render(save=False)
 def test_native_source_reassembly(self):
  for angle in m.VIEWS:
   original=m.keyframes()[angle]
   assets,rest,detail=m.extract(original)
   recovered=rest.copy()
   mask=assets['loop_visible'][...,3]>24
   recovered[mask]=assets['loop_visible'][mask]
   self.assertTrue(np.array_equal(recovered,original))
   self.assertTrue(detail['recompositionExact'])
 def test_connected_strand_identity_not_assumed(self):
  self.assertFalse(self.qa['separateSecondaryStrand'])
  for detail in self.qa['perView'].values():
   self.assertEqual(len(detail['components']),1)
   self.assertEqual(detail['otherUpperPixels'],0)
   self.assertGreater(detail['loopVisiblePixels'],900)
 def test_all_keyviews_and_render_study(self):
  self.assertEqual(self.qa['sourceAngles'],[90,112.5,135])
  self.assertEqual(len(self.qa['renderAngles']),5)
  self.assertGreater(self.qa['motionComparison']['sourceOwnedMotionMaxAdjacentRGBMAE'],
                     self.qa['motionComparison']['canonicalMaxAdjacentRGBMAE'])
 def test_no_unverified_art_admission(self):
  self.assertTrue(self.qa['pixelExactPartRecomposition'])
  self.assertFalse(self.qa['artistApprovedRootTopology'])
  self.assertFalse(self.qa['crossViewPhysicalCorrespondence'])
  self.assertFalse(self.qa['selectedForProduction'])
if __name__=='__main__':unittest.main()
