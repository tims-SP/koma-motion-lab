import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_165_root_ink_ownership.py')
spec=importlib.util.spec_from_file_location('p15_165_root_ink_ownership',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LoopRootInkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.evaluate(save=False)
 def test_native_keyviews_exact(self):
  self.assertTrue(self.q['nativeArtPreserved'])
  self.assertTrue(self.q['gate']['nativeKeyframesExact'])
  for result in self.q['renderers'].values():
   self.assertTrue(result['nativeKeysExact'])
 def test_bounded_root_erase_crown_scope(self):
  original=m.keyframes()[90.]
  for radius in (8,12,16):
   cleaned,info=m.clean_old_loop(original,90.,radius)
   self.assertTrue(info['sourceBelowY96Exact'])
   self.assertTrue(info['alphaCrownPreserved'])
   self.assertGreater(info['freeLoopPixels'],500)
   self.assertGreater(info['rootInkPixels'],0)
   self.assertTrue(np.array_equal(cleaned[96:],original[96:]))
 def test_midframe_connectivity_and_alpha_mismatch(self):
  ref=self.q['renderers']['reference']
  self.assertEqual(ref['topConnectedComponents'],[1,1,1,1,1])
  for size in (8,12,16):
   value=self.q['renderers'][f'root_ink_{size}']
   self.assertEqual(value['topConnectedComponents'],[1,2,1,1,1])
   self.assertGreater(value['crownAlphaChangedPixels']['101.25'],0)
   self.assertGreater(value['crownAlphaChangedPixels']['123.75'],0)
   self.assertGreater(value['maxAdjacentRGBMAE'],ref['maxAdjacentRGBMAE'])
 def test_visual_and_asset_admission(self):
  self.assertFalse(self.q['gate']['midframesOneTopComponent'])
  self.assertFalse(self.q['gate']['crownAlphaUnchanged'])
  self.assertFalse(self.q['gate']['beatsReference'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['independentRootArtworkArtistApproved'])
  self.assertFalse(self.q['sourceMatchedScalpArtworkApproved'])
  self.assertFalse(self.q['continuousVisualAccepted'])
  self.assertFalse(self.q['productionSelected'])
if __name__=='__main__':unittest.main()
