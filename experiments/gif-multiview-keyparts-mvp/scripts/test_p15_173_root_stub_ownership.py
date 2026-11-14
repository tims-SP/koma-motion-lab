import importlib.util,unittest,hashlib
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_173_root_stub_ownership.py')
spec=importlib.util.spec_from_file_location('p15_173_root_stub_ownership',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class SourceRootStubOwnershipTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.evaluate(save=False)
 def test_original_keys_and_paired_source_exact(self):
  self.assertTrue(self.q['nativeKeyArtworkUnchanged'])
  self.assertTrue(self.q['gate']['sourcePairExact'])
  for a in m.KEYS:
   original,part,head,mask,info=m.source_layers(a)
   assembled=head.copy();assembled[mask]=part[mask]
   self.assertTrue(np.array_equal(original,assembled))
 def test_locality_and_provenance(self):
  self.assertTrue(self.q['gate']['deepHeadPixelExact'])
  for mode in ('narrow','wide','cap'):
   for a,diagnostic in self.q['methods'][mode].items():
    self.assertTrue(diagnostic['belowY125Exact'])
    self.assertEqual(diagnostic['sourceSHA256'],hashlib.sha256(m.source_layers(float(a))[0].tobytes()).hexdigest())
    self.assertGreater(diagnostic['paintPixels'],0)
 def test_crown_root_still_requires_artwork(self):
  self.assertGreater(self.q['methods']['narrow']['112.5']['alphaAboveCrownRemaining'],0)
  self.assertGreater(self.q['methods']['cap']['112.5']['alphaAboveCrownRemaining'],0)
  self.assertFalse(self.q['gate']['allAirPostsCleared'])
  self.assertFalse(self.q['gate']['rootStubVisuallyCleared'])
  self.assertFalse(self.q['gate']['sourceCrownContourVisuallyMatched'])
 def test_source_donor_suppresses_root_dark_pixels(self):
  self.assertLess(self.q['methods']['cap']['112.5']['darkRootPixelCount'],
                  self.q['methods']['narrow']['112.5']['darkRootPixelCount'])
  self.assertGreater(self.q['methods']['cap']['112.5']['paintPixels'],
                     self.q['methods']['narrow']['112.5']['paintPixels'])
 def test_production_not_admitted(self):
  self.assertFalse(self.q['sourceMatchedHiddenPaintApproved'])
  self.assertFalse(self.q['continuousMotionAccepted'])
  self.assertFalse(self.q['canonicalRendererUpdated'])
  self.assertFalse(self.q['gate']['passes'])
if __name__=='__main__':unittest.main()
