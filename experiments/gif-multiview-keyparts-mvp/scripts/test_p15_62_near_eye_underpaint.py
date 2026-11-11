import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-62-near-eye-underpaint'
class EyeUnderpaint(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-62-near-eye-underpaint-qa.json').read_text())
 def test_candidate_sha(self):
  p=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['sourceSHA256'])
 def test_cutout_rgba(self):
  with Image.open(D/'eye.near.cutout.png') as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_underpaint_rgba(self):
  with Image.open(D/'skin.underpaint.png') as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_shifted_rgba(self):
  with Image.open(D/'eye-shift-18px.png') as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_eye_shift_exactly_18(self):self.assertEqual(self.q['eyeMovePx'],[18,0])
 def test_no_transparent_holes(self):self.assertEqual(self.q['transparentHolePixelsNearEyeROI'],0)
 def test_mask_area_opaque(self):self.assertEqual(self.q['opaqueCoverageMissingPixelsInEyePolygon'],0)
 def test_outside_mask_unchanged(self):self.assertEqual(self.q['outsideMaskChangedPixels'],0)
 def test_method_not_true_art(self):
  self.assertFalse(self.q['hiddenSkinAuthenticallyReconstructed'])
  self.assertFalse(self.q['methodIsIndependentOriginalPainting'])
 def test_not_accepted(self):
  self.assertEqual(self.q['visualGate'],'FAIL_LOCAL_TEXTURE_CLONE_VISIBLE_SEAM')
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_review(self):
  h=(D/'index.html').read_text()
  for f in ['source-face.png','underpaint-face.png','shifted-face.png','eye.near.cutout.png','skin.underpaint.png']:
   self.assertIn('src="'+f+'"',h)
if __name__=='__main__':unittest.main()
