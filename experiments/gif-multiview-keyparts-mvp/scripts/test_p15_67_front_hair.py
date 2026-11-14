import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-67-front-hair'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class FrontHair(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-67-front-hair-qa.json').read_text())
 def test_source_hash(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_old_source_hash(self):self.assertEqual(sha(R/'private-assets/exports/p15-41-profile-candidate/layers/hair.front.png'),self.q['oldHairSHA256'])
 def test_skin_hash(self):self.assertEqual(sha(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png'),self.q['underpaintSHA256'])
 def test_eye_hash(self):self.assertEqual(sha(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['eyeLayerSHA256'])
 def test_trial_hashes(self):
  self.assertEqual(sha(D/'hair.front.full-area-candidate.png'),self.q['fullHairCandidateSHA256'])
  self.assertEqual(sha(D/'hair.front.eye-excluded-v2.png'),self.q['refinedEyeExcludedSHA256'])
 def test_mask_hashes(self):
  self.assertEqual(sha(D/'hair.front.full-area-mask.png'),self.q['maskSHA256'])
  self.assertEqual(sha(D/'hair.front.eye-excluded-mask.png'),self.q['refinedMaskSHA256'])
 def test_real_transparent_png(self):
  for n in ['hair.front.full-area-candidate.png','hair.front.eye-excluded-v2.png']:
   with Image.open(D/n) as im:
    self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
    self.assertIsNotNone(im.getchannel('A').getbbox())
 def test_v2_less_contaminated(self):
  self.assertLess(self.q['eyeExcludedNonzeroAlphaPixels'],self.q['visiblePixels'])
  self.assertGreater(self.q['eyeExcludedNonzeroAlphaPixels'],50000)
 def test_partial_alpha(self):
  self.assertGreater(self.q['eyeExcludedPartialAlphaPixels'],1000)
 def test_v2_bbox_matches(self):
  with Image.open(D/'hair.front.eye-excluded-v2.png') as im:
   self.assertEqual(list(im.getchannel('A').getbbox()),self.q['eyeExcludedLayerBBox'])
 def test_motion_exists(self):
  self.assertEqual([x['dx'] for x in self.q['refinedFrames']],[0,9,18])
  for frame in self.q['refinedFrames']:
   with Image.open(D/frame['image']) as im:self.assertEqual(im.size,(1024,1024))
 def test_missing_hidden_underpaint(self):
  self.assertFalse(self.q['originalHiddenForeheadUnderpaintAvailable'])
  self.assertFalse(self.q['hiddenForeheadSkinIndependentlyReconstructed'])
 def test_hair_not_approved(self):
  self.assertFalse(self.q['trueIndependentPaintedHair'])
  self.assertFalse(self.q['fullHairTopologyMatched'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertTrue(self.q['visualGate'].startswith('FAIL_'))
 def test_visual_defects_recorded(self):self.assertEqual(len(self.q['actualVisualFailures']),4)
 def test_html(self):
  h=(D/'index.html').read_text()
  self.assertIn('id="shift"',h)
  self.assertIn('正式视觉门禁 FAIL',h)
if __name__=='__main__':unittest.main()
