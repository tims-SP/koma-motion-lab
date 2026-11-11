import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-63-masked-lama'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class NeuralInpaint(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-63-masked-lama-qa.json').read_text())
 def test_source_hash(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_model_returned(self):
  self.assertEqual(self.q['modelStatus'],'SUCCESS')
  self.assertEqual(self.q['provider'],'pg56714/Inpaint-Anything')
  self.assertEqual(sha(D/'model-512.png'),self.q['modelSHA256'])
 def test_mask_is_real_512(self):
  with Image.open(D/'mask-512.png') as im:
   self.assertEqual(im.size,(512,512))
   self.assertGreater(sum(px>0 for px in im.getdata()),1000)
  self.assertEqual(sha(D/'mask-512.png'),self.q['maskSHA256'])
 def test_crop_matches_input_sha(self):self.assertEqual(sha(D/'input-512.png'),self.q['cropInputSHA256'])
 def test_restricted_is_rgba(self):
  with Image.open(D/'underpaint-full.png') as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_strict_outside_mask_pixel_exact(self):
  a=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA').tobytes()
  b=Image.open(D/'underpaint-full.png').convert('RGBA').tobytes()
  m=Image.open(D/'mask-full.png').convert('L').tobytes()
  self.assertEqual(sum(a[i*4:i*4+4]!=b[i*4:i*4+4] for i,k in enumerate(m) if k==0),0)
  self.assertEqual(self.q['outsideMaskChangedPixels'],0)
 def test_neural_changed_pixels(self):self.assertGreater(self.q['insideMaskChangedPixels'],1000)
 def test_image_movement_no_holes(self):
  self.assertEqual(self.q['shift18TransparentHolePixels'],0)
  with Image.open(D/'eye-shift18.png') as im:self.assertEqual(im.size,(1024,1024))
 def test_provenance(self):
  for file,key in [('underpaint-full.png','underpaintSHA256'),('eye-near-cutout.png','eyeCutoutSHA256'),('eye-shift18.png','eyeShiftSHA256')]:
   self.assertEqual(sha(D/file),self.q[key])
 def test_not_formal_acceptance(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertFalse(self.q['independentNearEyePurityValidated'])
  self.assertEqual(self.q['visualGate'],'FAIL_EYE_CUTOUT_CONTAINS_HAIR_SKIN_EDGE_ARTIFACTS')
 def test_review(self):
  h=(D/'index.html').read_text()
  for f in ['source-face.png','underpaint-face.png','shift-face.png','mask-512.png','model-512.png']:
   self.assertIn('src="'+f+'"',h)
if __name__=='__main__':unittest.main()
