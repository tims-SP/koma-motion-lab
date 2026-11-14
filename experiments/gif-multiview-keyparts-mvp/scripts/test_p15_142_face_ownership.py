import importlib.util,unittest
from pathlib import Path
import numpy as np
path=Path(__file__).with_name('p15_142_face_ownership.py')
spec=importlib.util.spec_from_file_location('p15_142_face_ownership',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FaceOwnershipTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.run(save=False)
 def test_exact_source_recomposition(self):
  for a in m.KEYS:
   s,foreground,body,owner,protected=m.separate(a,1.25)
   rebuilt=body.copy();rebuilt[owner]=foreground[owner]
   self.assertTrue(np.array_equal(rebuilt,s))
   self.assertTrue(np.all(~owner|~protected))
 def test_native_keys_are_exact(self):
  self.assertTrue(self.q['sourceReconstructionExact'])
  for candidate in self.q['variants'].values():
   self.assertTrue(candidate['nativeKeyframesPixelExact'])
 def test_protection_changes_pixel_ownership(self):
  a=self.q['variants']['face_guard_075']['reassignedFacePixelsByYaw']
  b=self.q['variants']['face_guard_125']['reassignedFacePixelsByYaw']
  self.assertGreater(b['90.0'],a['90.0'])
  self.assertGreater(b['112.5'],a['112.5'])
 def test_diagnostic_quality_only(self):
  self.assertLess(self.q['variants']['face_guard_125']['maxAdjacentRGBMAE'],
                  self.q['referenceMaxAdjacentRGBMAE'])
  self.assertFalse(self.q['physicalSourceCorrespondenceValidated'])
  self.assertFalse(self.q['hiddenSurfaceRegistrationValidated'])
  self.assertFalse(self.q['visualAccepted'])
 def test_occluded_eye_has_no_135_source_marker(self):
  mask=m.protect_mask(135.)
  self.assertEqual(mask.shape,(443,443))
  self.assertIsNone(m.POINTS['eye.near.center']['135'])
if __name__=='__main__': unittest.main()
