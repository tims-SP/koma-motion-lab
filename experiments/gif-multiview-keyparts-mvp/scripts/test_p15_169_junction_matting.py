import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('p15_169_junction_matting.py')
spec=importlib.util.spec_from_file_location('p15_169_junction_matting',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class JunctionMattingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.run(save=False)
 def test_source_keys_pixel_exact(self):
  self.assertTrue(self.q['gate']['nativeKeyviewsExact'])
  for v in self.q['methods'].values():
   self.assertTrue(v['nativeKeyviewsPixelExact'])
 def test_root_topology_is_connected(self):
  self.assertTrue(self.q['gate']['bothMidviewsTopologicallyConnected'])
  for name in ('crown_front','junction_06','junction_10','junction_14'):
   self.assertEqual(self.q['methods'][name]['topConnectedComponents'],[1,1,1,1,1])
 def test_strict_scope_and_alpha(self):
  self.assertTrue(self.q['gate']['deepBodyExact'])
  self.assertTrue(self.q['gate']['alphaRetained'])
  for name in ('junction_06','junction_10','junction_14'):
   for entry in self.q['localMaterialChecks'][name].values():
    self.assertTrue(entry['belowY125Exact'])
    self.assertTrue(entry['scalpAlphaIdenticalToBase'])
    self.assertGreater(entry['editedPixels'],0)
    self.assertLess(entry['editedPixels'],1000)
    self.assertLessEqual(entry['editBBox'][3],107)
 def test_bounded_patch_beats_unpatched_candidate(self):
  q=self.q['methods']
  self.assertLess(q['junction_06']['maxAdjacentRGBMAE'],q['crown_front']['maxAdjacentRGBMAE'])
  self.assertLess(q['junction_06']['maxAdjacentRGBMAE'],q['junction_14']['maxAdjacentRGBMAE'])
  self.assertGreater(q['junction_06']['maxAdjacentRGBMAE'],q['reference']['maxAdjacentRGBMAE'])
 def test_visual_gate_is_not_inferred(self):
  self.assertFalse(self.q['gate']['noMotionRegression'])
  self.assertFalse(self.q['gate']['visualApproval'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['hiddenCrownPaintArtistApproved'])
  self.assertFalse(self.q['rootAttachmentArtistApproved'])
  self.assertFalse(self.q['fullYawVisualAccepted'])
  self.assertFalse(self.q['canonicalRendererUpdated'])
if __name__=='__main__':unittest.main()
