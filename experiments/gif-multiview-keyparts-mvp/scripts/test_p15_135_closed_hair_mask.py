import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_135_closed_hair_mask.py')
s=importlib.util.spec_from_file_location('p15_135_closed_hair_mask',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class ClosedHairMaskTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.result=m.assess(save=False)
 def test_exact_pixel_reassembly(self):
  self.assertTrue(self.result['sourceRGBAExactAfterSplit'])
  self.assertTrue(self.result['pixelOwnershipExclusive'])
 def test_closed_candidate_mass(self):
  self.assertEqual(self.result['maskInfo']['contourCount'],1)
  self.assertEqual(len(self.result['connectedRegionsOver20Pixels']),1)
  self.assertGreater(self.result['connectedRegionsOver20Pixels'][0],40000)
 def test_displacement_comparison(self):
  a=self.result['displacementRGBMAE']
  self.assertLess(a['closed']['12'],a['pigment']['12'])
  self.assertLess(a['closed']['24'],a['pigment']['24'])
 def test_hidden_geometry_requires_review(self):
  self.assertFalse(self.result['semanticArtMeshGeometryApproved'])
  self.assertFalse(self.result['physicalUnderpaintRegistrationApproved'])
  self.assertFalse(self.result['visualAccepted'])
if __name__=='__main__':unittest.main()
