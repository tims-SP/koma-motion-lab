import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_144_bangs_registration.py')
s=importlib.util.spec_from_file_location('p15_144_bangs_registration',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class BangsRegistrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.evaluate(save=False)
 def test_native_source_provenance(self):
  self.assertEqual(self.qa['nativeAssetSHA256'],m.sha(m.PNG))
  self.assertTrue(self.qa['nativeGeneratedArtUnmodified'])
 def test_eye_owner_protected(self):
  self.assertEqual(self.qa['afterEyeOwnerOpaquePixels'],0)
  self.assertLess(self.qa['registeredEyeOpaquePixels'],20)
 def test_affine_position_near_original_source(self):
  self.assertGreater(self.qa['registeredMaskIoU'],.5)
  self.assertLess(self.qa['registeredOffSilhouettePixels'],2000)
 def test_visible_art_acceptance_not_assumed(self):
  self.assertFalse(self.qa['artisticBangsIdentityApproved'])
  self.assertFalse(self.qa['fullYawVisualAccepted'])
  self.assertFalse(self.qa['sourceKeyframePixelExactAfterRegistration'])
 def test_changed_eye_compositing(self):
  metrics=self.qa['methods']
  self.assertLess(metrics['registered_eye_owned']['eyePatchRGBMAE'],metrics['direct_overlay']['eyePatchRGBMAE'])
  self.assertGreater(metrics['registered_eye_owned']['alphaHolesOverOriginal'],0)
if __name__=='__main__':unittest.main()
