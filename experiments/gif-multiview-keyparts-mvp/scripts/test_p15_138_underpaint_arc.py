import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_138_underpaint_arc.py')
s=importlib.util.spec_from_file_location('p15_138_underpaint_arc',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class NativeRearScalpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.run(save=False)
 def test_native_provenance(self):
  self.assertEqual(self.qa['nativeImageSHA256'],m.sha(m.SRC))
  self.assertTrue(self.qa['nativeRGBA'])
  self.assertTrue(self.qa['sourcePaintingPreserved'])
 def test_new_painted_rear_coverage(self):
  a=self.qa['staticStress']['p15_137']['24']['alphaHoles']
  b=self.qa['staticStress']['new_painted']['24']['alphaHoles']
  self.assertLess(b['rear_scalp'],a['rear_scalp'])
  self.assertLess(b['all'],a['all'])
 def test_hybrid_tradeoff(self):
  a=self.qa['staticStress']['p15_137']['24']['alphaHoles']
  b=self.qa['staticStress']['hybrid_rear']['24']['alphaHoles']
  self.assertLess(b['all'],a['all'])
  self.assertGreater(b['neck'],a['neck'])
  self.assertGreater(b['ear'],a['ear'])
 def test_yaw_source_endpoint_identity(self):
  self.assertEqual(self.qa['yawAngles'],[90,101.25,112.5,123.75,135])
  self.assertTrue(all(x['nativeSource90And135PixelExact'] for x in self.qa['transition'].values()))
 def test_visual_acceptance_separate(self):
  self.assertFalse(self.qa['rearScalpArtistApproved'])
  self.assertFalse(self.qa['continuousVisualAccepted'])
  self.assertFalse(self.qa['facialIdentityApproved'])
 def test_merge_deterministic(self):
  a=np.zeros((443,443,4),np.uint8)
  b=a.copy()
  self.assertTrue(np.array_equal(m.merge_rear(a,b),a))
if __name__=='__main__':unittest.main()
