import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_171_paired_layer_flow.py')
spec=importlib.util.spec_from_file_location('p15_171_paired_layer_flow',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PairedLayerFlowTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.evaluate(save=False)
 def test_source_pair_reassembly(self):
  native,hair,crown,mask,details=m.prepare_layers()
  for angle in m.KEYS:
   image=crown[angle].copy();image[mask[angle]]=hair[angle][mask[angle]]
   self.assertTrue(np.array_equal(image,native[angle]))
   self.assertTrue(details[f'{angle:g}']['pairedReassemblyExact'])
   self.assertGreater(details[f'{angle:g}']['rootPixels'],0)
 def test_independent_flow_keyframes_exact(self):
  self.assertTrue(self.qa['gate']['sourcePairsExact'])
  self.assertTrue(self.qa['gate']['nativeKeysExact'])
  self.assertEqual(self.qa['renderAngles'],[90,101.25,112.5,123.75,135])
  for method in self.qa['methods'].values():
   self.assertTrue(method['sourceKeysPixelExact'])
 def test_frame_scope_and_topology(self):
  self.assertTrue(self.qa['gate']['deepBodyExact'])
  self.assertTrue(self.qa['gate']['midviewConnected'])
  for name in ('paired_crown','paired_root','paired_root_soft'):
   self.assertTrue(self.qa['methods'][name]['bodyBelowY125Exact'])
   self.assertEqual(self.qa['methods'][name]['topConnectedComponents'],[1,1,1,1,1])
   for info in self.qa['midframeChecks'][name].values():
    self.assertTrue(info['sourceBelowY125Exact'])
    self.assertGreater(info['pairedCrownRGBEditedPixels'],0)
 def test_best_candidate_is_not_above_reference(self):
  methods=self.qa['methods']
  self.assertLess(methods['paired_root_soft']['maxAdjacentRGBMAE'],methods['paired_crown']['maxAdjacentRGBMAE'])
  self.assertGreater(methods['paired_root_soft']['maxAdjacentRGBMAE'],methods['reference']['maxAdjacentRGBMAE'])
  self.assertFalse(self.qa['gate']['beatsReference'])
 def test_artist_and_production_gate(self):
  self.assertFalse(self.qa['artistApprovedUnderpaint'])
  self.assertFalse(self.qa['artistApprovedHairAttachment'])
  self.assertFalse(self.qa['continuousVisualAccepted'])
  self.assertFalse(self.qa['canonicalRendererUpdated'])
  self.assertFalse(self.qa['gate']['artistApproval'])
  self.assertFalse(self.qa['gate']['passes'])
if __name__=='__main__': unittest.main()
