import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('p15_170_semantic_ink.py')
s=importlib.util.spec_from_file_location('p15_170_semantic_ink',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class SemanticInkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.q=m.run(save=False)
 def test_source_keyframes_exact(self):
  self.assertEqual(self.q['renderAngles'],[90,101.25,112.5,123.75,135])
  self.assertTrue(self.q['gate']['allKeyviewsExact'])
  self.assertTrue(all(v['nativeKeysExact'] for v in self.q['methods'].values()))
 def test_topology_and_scope(self):
  self.assertTrue(self.q['gate']['allMidviewsConnected'])
  self.assertTrue(self.q['gate']['bodyExact'])
  self.assertTrue(self.q['gate']['alphaExactToCrownFront'])
  for name in ('ink_10','ink_18','ink_26'):
   self.assertEqual(self.q['methods'][name]['topConnectedComponents'],[1,1,1,1,1])
   self.assertTrue(self.q['methods'][name]['belowY125Exact'])
   for info in self.q['pixelDiagnostics'][name].values():
    self.assertTrue(info['sourceAlphaExact'])
    self.assertTrue(info['sourceBodyY125Exact'])
    self.assertGreater(info['editPixels'],0)
    self.assertLessEqual(info['editBBox'][3],115)
 def test_source_line_response_locality(self):
  for angle in ('101.25','123.75'):
   self.assertGreater(self.q['pixelDiagnostics']['ink_10'][angle]['semanticInkPixels'],
                      self.q['pixelDiagnostics']['ink_26'][angle]['semanticInkPixels'])
 def test_best_diagnostic_not_better_than_canonical(self):
  q=self.q['methods']
  self.assertLess(q['ink_10']['maxAdjacentRGBMAE'],q['crown_front']['maxAdjacentRGBMAE'])
  self.assertLess(q['ink_10']['maxAdjacentRGBMAE'],q['ink_26']['maxAdjacentRGBMAE'])
  self.assertGreater(q['ink_10']['maxAdjacentRGBMAE'],q['reference']['maxAdjacentRGBMAE'])
 def test_visual_and_art_approval_independent(self):
  self.assertFalse(self.q['gate']['beatsBaseline'])
  self.assertFalse(self.q['gate']['artistApproved'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['painterApprovedSourceLineOwnership'])
  self.assertFalse(self.q['painterApprovedRootlessCrown'])
  self.assertFalse(self.q['continuousYawVisuallyAccepted'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
