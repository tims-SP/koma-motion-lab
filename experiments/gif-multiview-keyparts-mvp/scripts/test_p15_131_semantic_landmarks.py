import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('p15_131_semantic_landmarks.py')
spec=importlib.util.spec_from_file_location('p15_131_semantic_landmarks',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SemanticLandmarkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.result=m.audit(save=False)
 def test_roles_and_foreground(self):
  self.assertEqual(self.result['manualProposalsCount'],12)
  self.assertEqual(self.result['warnings'],[])
  self.assertEqual(self.result['threeViewVisibleCount'],10)
 def test_visibility_is_explicit(self):
  self.assertIsNone(self.result['landmarks']['eye.near.center']['coordinates']['135'])
  self.assertIsNone(self.result['landmarks']['bow.center']['coordinates']['135'])
  self.assertEqual(self.result['landmarks']['eye.near.center']['visible'],[90,112.5])
 def test_deviation_exposes_hair_mismatch(self):
  metric=self.result['geometryDiagnostics']
  self.assertGreater(metric['hair.ahoge.root']['midpointDeviationPx'],40)
  self.assertGreater(metric['hair.ahoge.apex']['midpointDeviationPx'],40)
  self.assertFalse(self.result['physical3DAnchorVerified'])
 def test_input_raster_identity(self):
  self.assertEqual(len(self.result['nativeKeySHA256RGBA']),3)
  self.assertTrue(all(len(v)==64 for v in self.result['nativeKeySHA256RGBA'].values()))
if __name__=='__main__':unittest.main()
