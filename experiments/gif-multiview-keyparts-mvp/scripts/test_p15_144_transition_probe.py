import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('p15_144_transition_probe.py')
s=importlib.util.spec_from_file_location('p15_144_transition_probe',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class RegisteredFringeYawTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.run(save=False)
 def test_native_endpoints(self):
  self.assertTrue(self.qa['original90And135PixelExact'])
  self.assertTrue(self.qa['native112p5ImagePreserved'])
 def test_real_midview_regression_recorded(self):
  self.assertEqual(len(self.qa['angles']),5)
  self.assertGreater(self.qa['maxAdjacentRGBMAE']['registered'],self.qa['maxAdjacentRGBMAE']['reference'])
 def test_quality_gated(self):
  self.assertFalse(self.qa['midway112p5SourcePixelExact'])
  self.assertFalse(self.qa['continuousVisualAccepted'])
  self.assertFalse(self.qa['realHairPartIdentityApproved'])
if __name__=='__main__':unittest.main()
