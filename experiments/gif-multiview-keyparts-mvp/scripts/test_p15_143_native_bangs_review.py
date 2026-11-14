import importlib.util, unittest
from pathlib import Path
p=Path(__file__).with_name('p15_143_native_bangs_review.py')
spec=importlib.util.spec_from_file_location('p15_143_native_bangs_review',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class NativeBangsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.trial()
 def test_native_rgba_provenance(self):
  self.assertEqual(self.q['nativeFileSHA256'],m.sha(m.PNG))
  self.assertEqual(self.q['nativeDimensions'],[1254,1254])
  self.assertTrue(self.q['nativeRGBA'])
 def test_independent_material_limited_to_head(self):
  self.assertGreater(self.q['occupiedRois']['front_fringe'],10000)
  self.assertLess(self.q['opaquePixelsBelowY320'],100)
 def test_compositing_gate_identifies_displaced_asset(self):
  self.assertGreater(self.q['nearEyeOpaqueCandidatePixels'],300)
  self.assertGreater(self.q['opaquePixelsOutsideSourceSilhouette'],5000)
  self.assertFalse(self.q['directOverlayRegistrationGatePassed'])
 def test_preserve_unapproved_status(self):
  self.assertFalse(self.q['partIdentityArtistVerified'])
  self.assertFalse(self.q['spatialRegistrationApproved'])
  self.assertFalse(self.q['fullYawVisualAccepted'])
if __name__=='__main__':unittest.main()
