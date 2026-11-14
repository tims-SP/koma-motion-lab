import importlib.util,unittest
from pathlib import Path
s=Path(__file__).with_name('p15_133_part_motion_probe.py')
spec=importlib.util.spec_from_file_location('p15_133_part_motion_probe',s)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SemanticMotionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.compare(save=False)
 def test_pixel_exact_keyframes(self):self.assertTrue(self.qa['nativeKeyframePixelExact'])
 def test_current_candidate_not_accepted(self):
  self.assertFalse(self.qa['visualAcceptance'])
  self.assertFalse(self.qa['semanticArtMeshVerified'])
  self.assertFalse(self.qa['hiddenUnderpaintVerified'])
 def test_morph_worse_than_benchmark(self):
  self.assertGreater(self.qa['candidateMaxAdjacentCompositeRGBMAE'],self.qa['baselineMaxAdjacentCompositeRGBMAE'])
if __name__=='__main__':unittest.main()
