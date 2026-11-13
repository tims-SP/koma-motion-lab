import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_159_curve_controls.py')
s=importlib.util.spec_from_file_location('p15_159_curve_controls',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class FiveControlLoopTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.evaluate(save=False)
 def test_five_controls_are_valid_and_consistent(self):
  self.assertEqual(set(self.q['viewControls']),{'90','112.5','135'})
  for group in self.q['viewControls'].values():
   points=np.asarray(group,dtype=float)
   self.assertEqual(points.shape,(5,2))
   self.assertTrue(np.isfinite(points).all())
   self.assertTrue(np.all((points>=0)&(points<443)))
 def test_source_keyframes_preserved(self):
  self.assertTrue(self.q['sourceArtUnchanged'])
  self.assertEqual(self.q['sampleAngles'],[90,101.25,112.5,123.75,135])
  self.assertTrue(all(x['sourceKeyframesPixelExact'] for x in self.q['renderers'].values()))
 def test_intermediate_control_paths_contain_visible_art(self):
  for name in ('controls_only','controls_bridge'):
   samples=self.q['renderers'][name]['midview']
   self.assertGreater(samples['101.25']['upperPartPixels'],500)
   self.assertGreater(samples['123.75']['upperPartPixels'],500)
   self.assertEqual(len(samples['101.25']['curveControls']),5)
 def test_crown_and_continuity_gate(self):
  ref=self.q['renderers']['reference']
  self.assertEqual(ref['topConnectedComponents'],[1,1,1,1,1])
  for name in ('controls_only','controls_bridge'):
   v=self.q['renderers'][name]
   self.assertGreater(v['maxAdjacentRGBMAE'],ref['maxAdjacentRGBMAE'])
   self.assertGreater(v['topConnectedComponents'][1],1)
   self.assertGreater(v['topConnectedComponents'][3],1)
   self.assertFalse(v['crownBelowCutPixelExact'])
  self.assertFalse(self.q['acceptanceGate']['passes'])
 def test_anatomical_verification_not_inferred(self):
  self.assertFalse(self.q['realPhysicalStrandIdentityVerified'])
  self.assertFalse(self.q['hiddenScalpArtValidated'])
  self.assertFalse(self.q['artistCurveControlsApproved'])
  self.assertFalse(self.q['fullYawVisualAccepted'])
if __name__=='__main__':unittest.main()
