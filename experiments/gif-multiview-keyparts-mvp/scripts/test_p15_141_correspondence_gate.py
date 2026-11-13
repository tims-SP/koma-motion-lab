import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_141_correspondence_gate.py')
spec=importlib.util.spec_from_file_location('p15_141_correspondence_gate',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CrossViewCorrespondenceGateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=m.audit(save=False)
 def test_both_original_source_pairs(self):
  self.assertEqual(set(self.r['pairs']),{'90-112.5','112.5-135'})
  self.assertEqual(len(self.r['comparisonRois']),4)
  for pair in self.r['pairs'].values():
   self.assertEqual(len(pair['directionalHairAgreement']['forward']),4)
   self.assertEqual(len(pair['directionalHairAgreement']['reverse']),4)
 def test_invalid_correspondences_detected(self):
  results=self.r['pairs']
  self.assertGreater(results['90-112.5']['directionalHairAgreement']['forward']['ahoge_crown']['rgbMAE'],15)
  self.assertGreater(results['112.5-135']['directionalHairAgreement']['forward']['rear_hair']['rgbMAE'],15)
  self.assertFalse(self.r['artistVerifiedStrandIdentity'])
  self.assertFalse(self.r['productionVDDApproved'])
  self.assertFalse(self.r['gateResults']['sourceVisibilityAndIdentityGatePassed'])
  self.assertGreaterEqual(len(self.r['gateResults']['regionsOverThreshold']),5)
 def test_diagnostics_finite(self):
  for pair in self.r['pairs'].values():
   for direction in ('forward','reverse'):
    for region in pair['directionalHairAgreement'][direction].values():
     self.assertGreaterEqual(region['alphaIoU'],0)
     self.assertLessEqual(region['alphaIoU'],1)
     self.assertGreaterEqual(region['rgbMAE'],0)
     self.assertTrue(np.isfinite(region['rgbMAE']))
     self.assertGreaterEqual(region['foregroundXorPixels'],0)
 def test_repeated_diagnostics_deterministic(self):
  x=m.audit(save=False)
  self.assertEqual(x['pairs'],self.r['pairs'])
if __name__=='__main__': unittest.main()
