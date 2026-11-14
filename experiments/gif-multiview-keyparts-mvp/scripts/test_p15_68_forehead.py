import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-68-forehead'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Forehead(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-68-forehead-qa.json').read_text())
 def test_original_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['inputSourceSHA256'])
 def test_mask_sha(self):self.assertEqual(sha(D/'mask-512.png'),self.q['maskSHA256'])
 def test_input_sha(self):self.assertEqual(sha(D/'input-512.png'),self.q['inputSHA256'])
 def test_genuine_model_result(self):
  self.assertEqual(self.q['modelStatus'],'SUCCESS')
  self.assertEqual(sha(D/'model-512.png'),self.q['modelSHA256'])
 def test_rgba_underpaint(self):
  with Image.open(D/'forehead-neural-underpaint.png') as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_exact_outside_mask(self):
  a=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA').tobytes()
  b=Image.open(D/'forehead-neural-underpaint.png').convert('RGBA').tobytes()
  m=Image.open(D/'mask-full.png').convert('L').tobytes()
  self.assertEqual(sum(a[i*4:i*4+4]!=b[i*4:i*4+4] for i,v in enumerate(m) if v==0),0)
 def test_inside_modified(self):self.assertGreater(self.q['changedInsideMaskPixels'],10000)
 def test_reuse_old_hair_unapproved(self):
  self.assertEqual(sha(R/'private-assets/exports/p15-67-front-hair/hair.front.eye-excluded-v2.png'),self.q['hairCandidateSHA256'])
  self.assertFalse(self.q['hairMattingPassed'])
 def test_frames(self):
  self.assertEqual(set(self.q['frameSHA256s'].keys()),{'0','9','18'})
  for dx,v in self.q['frameSHA256s'].items():self.assertEqual(v,sha(D/f'with-hair-eye-{int(dx):02d}.png'))
 def test_no_formal_approval(self):
  self.assertFalse(self.q['fullHiddenForeheadApproved'])
  self.assertFalse(self.q['finalArtMeshAccepted'])
  self.assertTrue(self.q['visualGate'].startswith('FAIL_'))
 def test_review(self):
  h=(D/'index.html').read_text();self.assertIn('id="shift"',h);self.assertIn('正式视觉门禁 FAIL',h)
if __name__=='__main__':unittest.main()
