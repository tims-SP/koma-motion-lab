import hashlib,json,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-74-bangs-repair'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1574(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-74-qa.json').read_text())
 def test_source(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_base(self):self.assertEqual(sha(R/'private-assets/exports/p15-70-seam-repair/forehead-seam-repaired.png'),self.q['baseSHA256'])
 def test_hair_original(self):self.assertEqual(sha(R/'private-assets/exports/p15-73-interactive-sam/front-bangs-rgba.png'),self.q['hairSourceSHA256'])
 def test_eye(self):self.assertEqual(sha(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['eyeSourceSHA256'])
 def test_clip(self):self.assertEqual(sha(R/'private-assets/exports/p15-69-clip-separation/hair-clip-gold-independent.png'),self.q['clipSHA256'])
 def test_fixed_hair(self):self.assertEqual(sha(D/'hair.front.alpha-dedup.png'),self.q['repairedHairSHA256'])
 def test_alpha_dedup_exact_count(self):
  old=Image.open(R/'private-assets/exports/p15-73-interactive-sam/front-bangs-rgba.png').getchannel('A')
  new=Image.open(D/'hair.front.alpha-dedup.png').getchannel('A')
  vals=list(ImageChops.difference(old,new).getdata())
  self.assertEqual(sum(x>0 for x in vals),95)
  self.assertEqual(self.q['duplicateSemiTransparentPixelsRemoved'],95)
 def test_before_bbox(self):self.assertEqual(self.q['beforeZeroPoseDiffBBox'],[759,288,776,373])
 def test_real_animation_zero_pose_equal(self):
  old=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  new=Image.open(D/'eye-shift-00.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(old,new).getbbox())
  self.assertTrue(self.q['actualAnimationZeroPoseSourceExact'])
  self.assertIsNone(self.q['afterZeroPoseDiffBBox'])
 def test_frame_sha(self):
  self.assertEqual([x['dx'] for x in self.q['frameHashes']],[0,9,18])
  for item in self.q['frameHashes']:
   self.assertEqual(sha(D/f"eye-shift-{item['dx']:02d}.png"),item['sha256'])
   self.assertEqual(sha(D/f"eye.matte-{item['dx']:02d}.png"),item['eyeMatteSHA256'])
 def test_motion_no_holes(self):self.assertEqual(self.q['motionHoleCounts'],{'0':0,'9':0,'18':0})
 def test_rgba_dimensions(self):
  for dx in [0,9,18]:
   with Image.open(D/f'eye-shift-{dx:02d}.png') as x:self.assertEqual((x.mode,x.size),('RGBA',(1024,1024)))
 def test_fails_visual_gate(self):
  self.assertIn('VISUAL_FAIL',self.q['visualGate'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_html_candid(self):
  h=(D/'index.html').read_text()
  self.assertIn('动态画质仍 FAIL',h)
  self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
