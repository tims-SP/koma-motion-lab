import hashlib,json,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-64-semantic-eye'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1564(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-64-semantic-eye-qa.json').read_text())
 def test_original_p1563_skin_unchanged(self):
  self.assertEqual(sha(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png'),self.q['originalLaMaUnderpaintSHA256'])
 def test_source_unchanged(self):
  self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_old_cutout_sha(self):
  self.assertEqual(sha(R/'private-assets/exports/p15-63-masked-lama/eye-near-cutout.png'),self.q['originalP1563CutoutSHA256'])
 def test_new_mask_hash(self):
  self.assertEqual(sha(D/'eye.near.tight-mask.png'),self.q['maskSHA256'])
 def test_new_eye_hash(self):
  self.assertEqual(sha(D/'eye.near.tight-layer.png'),self.q['eyeLayerSHA256'])
 def test_rgba_separation(self):
  with Image.open(D/'eye.near.tight-layer.png') as im:
   self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
   self.assertTrue(im.getchannel('A').getbbox())
 def test_reduced_roi(self):
  self.assertEqual(self.q['oldVisibleCutoutPixels'],11457)
  self.assertEqual(self.q['newVisibleCutoutPixels'],6995)
  self.assertEqual(self.q['reducedVisibleCutoutPixels'],4462)
 def test_all_motion_sha(self):
  self.assertEqual([f['dx'] for f in self.q['eyeShiftFrames']],[0,9,18])
  for f in self.q['eyeShiftFrames']:
   self.assertEqual(f['sha256'],sha(D/f['image']))
 def test_neural_underpaint_unchanged_output(self):
  under=Image.open(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png').convert('RGBA')
  sprite=Image.open(D/'eye.near.tight-layer.png').convert('RGBA')
  shifted=Image.new('RGBA',under.size);shifted.alpha_composite(sprite,(18,0))
  output=Image.open(D/'near-eye-shift-18.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(Image.alpha_composite(under,shifted),output).getbbox())
 def test_no_holes(self):self.assertEqual(self.q['shift18TransparentHolePixels'],0)
 def test_no_rectangular_hair_overlay(self):
  self.assertEqual(self.q['foregroundHairHandling'],'HAIR_REMAINS_IN_UNDERPAINT_NO_RECTANGULAR_HAIR_OVERLAY')
 def test_not_formally_accepted(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertFalse(self.q['semanticIdentityApproved'])
 def test_visual_review_declares_limits(self):
  h=(D/'index.html').read_text()
  self.assertIn('灰色晕边',h)
  self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
