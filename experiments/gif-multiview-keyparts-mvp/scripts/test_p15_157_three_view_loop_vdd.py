import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('p15_157_three_view_loop_vdd.py')
s=importlib.util.spec_from_file_location('p15_157_three_view_loop_vdd',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class CrossViewLoopTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.render(save=False)
 def test_original_art_preserved(self):
  self.assertTrue(self.q['viewSourceRecompositionExact'])
  self.assertTrue(all(v['nativeKeyframesPixelExact'] for v in self.q['methods'].values()))
 def test_connected_source_loop(self):
  self.assertEqual(self.q['methods']['reference']['topConnectedComponents'],[1,1,1,1,1])
  for name in ('flow_part','anchor_owner'):
   self.assertGreater(self.q['methods'][name]['topConnectedComponents'][1],1)
   self.assertGreater(self.q['methods'][name]['maxAdjacentRGBMAE'],self.q['methods']['reference']['maxAdjacentRGBMAE'])
 def test_source_crown_retained(self):
  self.assertTrue(all(v['sourceCrownBelowY54Exact'] for v in self.q['methods'].values()))
 def test_visual_acceptance(self):
  self.assertFalse(self.q['acceptanceGate']['passes'])
  self.assertFalse(self.q['sourceOwnedPhysicalCorrespondence'])
  self.assertFalse(self.q['visualAccepted'])
  self.assertFalse(self.q['selectedForProduction'])
if __name__=='__main__':unittest.main()
