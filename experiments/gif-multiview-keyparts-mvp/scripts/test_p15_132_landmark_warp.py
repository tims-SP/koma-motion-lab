import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_132_landmark_warp.py')
spec=importlib.util.spec_from_file_location('p15_132_landmark_warp',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LandmarkVDDTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.compare(save=False)
 def test_all_native_keyframes_exact(self):
  self.assertTrue(all(v['nativeKeysPixelExact'] for v in self.q['methods'].values()))
 def test_local_variants(self):
  self.assertEqual(set(self.q['methods']),{'source_owned','localized_025','localized_050','localized_075'})
  self.assertLess(self.q['methods']['localized_025']['maxAdjacentCompositeRGBMAE'],self.q['methods']['source_owned']['maxAdjacentCompositeRGBMAE'])
 def test_no_false_art_acceptance(self):
  self.assertFalse(self.q['artistApprovedCorrespondence'])
  self.assertFalse(self.q['occludedUnderpaintAvailable'])
  self.assertFalse(self.q['visualAccepted'])
 def test_zero_strength_keeps_frame(self):
  f=m.baseline()[1]
  warped,_=m.remap_local(f,101.25,amount=0)
  self.assertTrue(np.array_equal(f,warped))
if __name__=='__main__':unittest.main()
