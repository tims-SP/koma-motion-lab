import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-79-brow-split'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1579(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-79-qa.json').read_text())
 def test_base_source_sha(self):self.assertEqual(sha(P/'p15-70-seam-repair/forehead-seam-repaired.png'),self.q['baseSHA256'])
 def test_brow_sha(self):self.assertEqual(sha(D/'eyebrow.same-view.png'),self.q['eyebrowSHA256'])
 def test_underpaint_sha(self):self.assertEqual(sha(D/'forehead.without-eyebrow.png'),self.q['underpaintSHA256'])
 def test_mask_sha(self):self.assertEqual(sha(D/'eyebrow-mask.png'),self.q['maskSHA256'])
 def test_brow_pixel_count(self):self.assertEqual(sum(v>0 for v in Image.open(D/'eyebrow.same-view.png').getchannel('A').getdata()),500)
 def test_brow_bbox(self):self.assertEqual(Image.open(D/'eyebrow.same-view.png').getchannel('A').getbbox(),(582,414,634,433))
 def test_base_reconstruction_exact(self):
  a=Image.open(P/'p15-70-seam-repair/forehead-seam-repaired.png').convert('RGBA')
  b=Image.alpha_composite(Image.open(D/'forehead.without-eyebrow.png').convert('RGBA'),Image.open(D/'eyebrow.same-view.png').convert('RGBA'))
  self.assertIsNone(ImageChops.difference(a,b).getbbox())
 def test_0px_exact(self):
  a=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  b=Image.open(D/'frame-00.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(a,b).getbbox())
 def test_9px_matches_reference(self):
  a=Image.open(D/'frame-09.png').convert('RGBA');b=Image.open(P/'p15-75-eyebrow-seam/eye-shift-09.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(a,b).getbbox())
 def test_18px_matches_reference(self):
  a=Image.open(D/'frame-18.png').convert('RGBA');b=Image.open(P/'p15-75-eyebrow-seam/eye-shift-18.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(a,b).getbbox())
 def test_no_transparent_holes(self):
  for dx in (0,9,18):
   a=Image.open(D/f'frame-{dx:02d}.png').getchannel('A').crop((510,425,685,530))
   self.assertFalse(any(v==0 for v in a.getdata()))
 def test_frame_hashes(self):
  for x in self.q['frames']:self.assertEqual(sha(D/f"frame-{x['dx']:02d}.png"),x['sha256'])
 def test_brow_stays_anchored(self):self.assertTrue(self.q['browAnchoredToHead'])
 def test_bangs_above_brow(self):self.assertTrue(self.q['bangsRemainAboveBrow'])
 def test_gate_rejected(self):self.assertFalse(self.q['formalArtMeshAccepted']);self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_review(self):
  h=(D/'index.html').read_text();self.assertIn('正式视觉门禁仍未通过',h);self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
