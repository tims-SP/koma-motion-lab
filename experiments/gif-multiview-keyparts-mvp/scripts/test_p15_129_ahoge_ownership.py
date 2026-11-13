import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_129_ahoge_ownership.py')
s=importlib.util.spec_from_file_location('p15_129_ahoge_ownership',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class AhogeOwnerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.report=m.run(save=False)
 def test_native_keyframe_preservation(self):
  self.assertTrue(all(x['nativeKeyframesPixelExact'] for x in self.report['methods'].values()))
 def test_local_owner_effect(self):
  methods=self.report['methods']
  self.assertLess(methods['nearest_key_owner']['maxAdjacentCompositeRGBMAE'],methods['bidirectional_blend']['maxAdjacentCompositeRGBMAE'])
 def test_unchanged_lower_material(self):
  a=np.zeros((443,443,4),dtype=np.uint8);b=a.copy();b[...,0]=255;b[...,3]=255
  out=m.merge_top(a,b)
  self.assertTrue(np.array_equal(out[110:],a[110:]))
  self.assertTrue(np.array_equal(out[:70],b[:70]))
 def test_angle_coverage(self):
  self.assertEqual(len(m.ANGLES),5)
  self.assertEqual(list(m.KEYS),[90,112.5,135])
if __name__=='__main__':unittest.main()
