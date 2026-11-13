import importlib.util
import unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_140_contour_yaw_mesh.py')
spec=importlib.util.spec_from_file_location('p15_140_contour_yaw_mesh',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ContourYawMeshTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.run(save=False)
 def test_common_positive_triangle_geometry(self):
  self.assertEqual(self.qa['meshVertexCount'],73)
  self.assertEqual(self.qa['meshTriangleCount'],120)
  self.assertTrue(all(x>0 for x in self.qa['intermediateMinimumSignedArea'].values()))
  self.assertTrue(self.qa['metrics']['allTrianglesPositive'])
 def test_original_keys_preserved(self):
  self.assertTrue(self.qa['metrics']['nativeKeysPixelExact'])
  self.assertTrue(self.qa['sourceArtPreserved'])
  self.assertEqual(self.qa['samples'],[90,101.25,112.5,123.75,135])
 def test_no_false_visual_acceptance(self):
  self.assertFalse(self.qa['fullYawVisualAccepted'])
  self.assertFalse(self.qa['trueStrandIdentityVerified'])
  self.assertFalse(self.qa['paintedUnderlayPerViewAvailable'])
 def test_benchmark_regression_recorded(self):
  self.assertGreater(self.qa['metrics']['maxAdjacentCompositeRGBMAE'],
                     self.qa['metrics']['baselineMaxAdjacentCompositeRGBMAE'])
 def test_common_mesh_role_ids(self):
  role=m.load_roles(90.)[3]
  verts,faces,*_=m.contour_mesh(role)
  self.assertEqual(verts.shape,(73,2))
  self.assertEqual(faces.shape,(120,3))
  self.assertTrue(np.all(faces>=0))
  self.assertLess(int(faces.max()),len(verts))
if __name__=='__main__':unittest.main()
