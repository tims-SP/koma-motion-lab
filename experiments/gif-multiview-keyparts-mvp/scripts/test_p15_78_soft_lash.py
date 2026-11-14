import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-78-soft-lash'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1578(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-78-qa.json').read_text())
 def test_source_eye(self):self.assertEqual(sha(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['sourceEyeSHA256'])
 def test_source_frame(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_mask_sha(self):self.assertEqual(sha(D/'lash-soft-mask.png'),self.q['maskSHA256'])
 def test_upper_sha(self):self.assertEqual(sha(D/'eye.upper-lash.soft.png'),self.q['upperLashSHA256'])
 def test_lower_sha(self):self.assertEqual(sha(D/'eye.lower-eye.soft.png'),self.q['lowerEyeSHA256'])
 def test_reconstruction_exact(self):
  a=Image.open(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
  b=Image.alpha_composite(Image.open(D/'eye.lower-eye.soft.png').convert('RGBA'),Image.open(D/'eye.upper-lash.soft.png').convert('RGBA'))
  self.assertIsNone(ImageChops.difference(a,b).getbbox())
 def test_eye_dimensions(self):
  for f in ['eye.upper-lash.soft.png','eye.lower-eye.soft.png']:
   with Image.open(D/f) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_soft_mask_gray_edges(self):
  a=Image.open(D/'lash-soft-mask.png').convert('L')
  self.assertTrue(any(0<v<255 for v in a.getdata()))
 def test_zero_exact(self):
  a=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  b=Image.open(D/'frame-00.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(a,b).getbbox())
  self.assertTrue(self.q['zeroPoseSourceExact'])
 def test_frame_hashes(self):
  self.assertEqual([x['dx'] for x in self.q['frames']],[0,9,18])
  for x in self.q['frames']:self.assertEqual(sha(D/f"frame-{x['dx']:02d}.png"),x['sha256'])
 def test_offsets(self):self.assertEqual(self.q['motionOffsets'],[0,9,18])
 def test_formal_rejected(self):
  self.assertFalse(self.q['formalArtMeshAccepted']);self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_gate_admits_remaining_issue(self):self.assertIn('BROW_BANG',self.q['visualGate'])
 def test_review(self):
  h=(D/'index.html').read_text();self.assertIn('正式视觉门禁仍未通过',h);self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
