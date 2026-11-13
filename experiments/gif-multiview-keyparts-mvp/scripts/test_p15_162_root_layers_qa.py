import importlib.util,unittest,hashlib
from pathlib import Path
p=Path(__file__).with_name('p15_162_root_layers_qa.py')
spec=importlib.util.spec_from_file_location('p15_162_root_layers_qa',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class NativeRootArtworkQATests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.prepare(save=False)
 def test_all_three_provenance_accurate(self):
  self.assertEqual(len(self.q['producedSources']),3)
  self.assertEqual(self.q['currentGenerationSourceCount'],2)
  for yaw in m.KEYS:
   part,meta=m.source(yaw)
   self.assertEqual(part.shape,(443,443,4))
   self.assertEqual(meta['sha256'],hashlib.sha256(m.path(yaw).read_bytes()).hexdigest())
  self.assertEqual(self.q['producedSources']['135']['assetOrigin'],'P15-150 verified source reuse')
 def test_alpha_and_root_geometry_gates(self):
  self.assertFalse(self.q['gate']['allViewsNewlyGenerated'])
  self.assertFalse(self.q['gate']['allRootsReachY75'])
  self.assertFalse(self.q['producedSources']['90']['diagnostics']['rootAtY75'])
  self.assertGreater(self.q['producedSources']['90']['diagnostics']['rootRegionPixels'],150)
 def test_real_yaw_has_key_preservation_and_failure(self):
  q=self.q['yaw']
  self.assertEqual(len(q['angles']),5)
  self.assertTrue(q['nativeKeyviewsPixelExact'])
  self.assertGreater(q['candidateMaxAdjacentRGBMAE'],q['baselineMaxAdjacentRGBMAE'])
  self.assertGreater(q['candidateTopComponents'][1],1)
 def test_production_gate_separate_from_generation(self):
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionAdmitted'])
  self.assertFalse(self.q['rootCorrespondenceVerified'])
  self.assertFalse(self.q['sourceUnderpaintArtistApproved'])
  self.assertFalse(self.q['fullVisualAccepted'])
if __name__=='__main__':unittest.main()
