import unittest,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-75-eyebrow-seam'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
class P1575(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-75-qa.json').read_text())
 def test_source(self):self.assertEqual(self.q['sourceSHA256'],sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'))
 def test_base(self):self.assertEqual(self.q['baseSHA256'],sha(R/'private-assets/exports/p15-70-seam-repair/forehead-seam-repaired.png'))
 def test_eye(self):self.assertEqual(self.q['eyeSHA256'],sha(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'))
 def test_hair(self):self.assertEqual(self.q['hairSHA256'],sha(R/'private-assets/exports/p15-74-bangs-repair/hair.front.alpha-dedup.png'))
 def test_clip(self):self.assertEqual(self.q['clipSHA256'],sha(R/'private-assets/exports/p15-69-clip-separation/hair-clip-gold-independent.png'))
 def test_guard(self):self.assertEqual(self.q['guardSHA256'],sha(D/'dynamic-suppression-guard.png'))
 def test_actual_zero_pose_exact(self):
  a=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  b=Image.open(D/'eye-shift-00.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(a,b).getbbox())
  self.assertTrue(self.q['zeroPosePixelExact'])
 def test_frame_sha(self):
  self.assertEqual([f['dx'] for f in self.q['frameHashes']],[0,9,18])
  for f in self.q['frameHashes']:
   self.assertEqual(sha(D/f"eye-shift-{f['dx']:02d}.png"),f['sha256'])
   self.assertEqual(sha(D/f"hair.front.moving-{f['dx']:02d}.png"),f['hairSHA256'])
 def test_no_holes(self):self.assertEqual(self.q['transparentHoleCounts'],{'0':0,'9':0,'18':0})
 def test_actual_change(self):self.assertGreater(self.q['changedRGBOrAlphaPixelsAt18InDetail'],1000)
 def test_rgba(self):
  for d in [0,9,18]:
   with Image.open(D/f'eye-shift-{d:02d}.png') as im:self.assertEqual((im.size,im.mode),((1024,1024),'RGBA'))
 def test_gate(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertIn('VISUAL_FAIL',self.q['visualGate'])
 def test_undesired_paint_rejected(self):
  self.assertIn('solid_skin_color_patch_due_to_obvious_flat_polygon',self.q['rejectedCandidateExperiments'])
 def test_html(self):
  h=(D/'index.html').read_text()
  self.assertIn('正式视觉门禁未通过',h)
  self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
