import importlib.util,unittest,hashlib
from pathlib import Path
from p15_162_root_layers_qa import path as asset_path
p=Path(__file__).with_name('p15_163_canonical_registration.py')
spec=importlib.util.spec_from_file_location('p15_163_canonical_registration',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CanonicalRegistrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.run(save=False)
 def test_provenance_preserved(self):
  for angle in m.KEYS:
   _,meta=m.source(angle)
   self.assertEqual(meta['sha256'],hashlib.sha256(asset_path(angle).read_bytes()).hexdigest())
 def test_all_three_source_visible_loops_improved(self):
  q=self.qa
  self.assertEqual(set(q['views']),{'90','112.5','135'})
  for view in q['views'].values():
   self.assertGreater(view['registered']['sourceLoopMatch']['sourceVisibleLoopIoU'],view['original']['sourceVisibleLoopIoU'])
   self.assertGreaterEqual(view['registered']['sourceLoopMatch']['sourceVisibleLoopIoU'],.45)
   self.assertTrue(view['registered']['sourceLoopMatch']['rootAtActualY'])
  self.assertTrue(q['gate']['allLoopIoUImproved'])
  self.assertTrue(q['gate']['allVisibleLoopIoUOver0p45'])
 def test_native_keys_pixel_exact(self):
  self.assertTrue(self.qa['render']['registeredCandidate']['nativeKeyframesPixelExact'])
  self.assertTrue(self.qa['sourceKeyviewsPreserved'])
 def test_intermediate_visual_gate(self):
  base=self.qa['render']['reference']
  candidate=self.qa['render']['registeredCandidate']
  self.assertEqual(base['topComponents'],[1,1,1,1,1])
  self.assertEqual(candidate['topComponents'][1],2)
  self.assertGreater(candidate['maxAdjacentRGBMAE'],base['maxAdjacentRGBMAE'])
  self.assertFalse(self.qa['gate']['midYawSingleComponent'])
  self.assertFalse(self.qa['gate']['passes'])
 def test_root_underpaint_not_claimed(self):
  self.assertFalse(self.qa['matchedHiddenCrownVerified'])
  self.assertFalse(self.qa['physicalRootContinuityArtistApproved'])
  self.assertFalse(self.qa['fullYawVisualAccepted'])
  self.assertFalse(self.qa['productionAdmitted'])
if __name__=='__main__':unittest.main()
