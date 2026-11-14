import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-83-eye-seam'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
class P1583(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-83-qa.json').read_text())
 def test_source(self):self.assertEqual(sha(P/'p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_base(self):self.assertEqual(sha(P/'p15-70-seam-repair/forehead-seam-repaired.png'),self.q['baseSHA256'])
 def test_hair(self):self.assertEqual(sha(P/'p15-82-rest-underpaint/part.source-bangs.png'),self.q['hairSHA256'])
 def test_clip(self):self.assertEqual(sha(P/'p15-82-rest-underpaint/part.source-clip.png'),self.q['clipSHA256'])
 def test_exact_rest_source(self):
  a=Image.open(D/'candidate-00.png').convert('RGBA').tobytes()
  b=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA').tobytes()
  self.assertTrue(all(a[i:i+4]==b[i:i+4] or b[i+3]==0 for i in range(0,len(a),4)))
 def test_proven_rest_from_prior_layers(self):self.assertEqual(sha(D/'candidate-00.png'),self.q['independentZeroPoseSHA256'])
 def test_variants(self):self.assertEqual(set(self.q['variants']),{'slender','upper','localized'})
 def test_mask_sha(self):
  for name,v in self.q['variants'].items():self.assertEqual(sha(D/f'mask-{name}.png'),v['maskSHA256'])
 def test_underpaint_sha(self):
  for name,v in self.q['variants'].items():self.assertEqual(sha(D/f'underpaint-{name}.png'),v['underpaintSHA256'])
 def test_frame_sha(self):
  for name,v in self.q['variants'].items():
   for dx,f in v['frames'].items():self.assertEqual(sha(D/f'candidate-{name}-{int(dx):02d}.png'),f['sha256'])
 def test_eye_holes(self):
  self.assertTrue(all(f['newTransparentHolesROI']==0 for v in self.q['variants'].values() for f in v['frames'].values()))
 def test_brow_damage(self):
  self.assertEqual([self.q['variants'][n]['browMaskOverlapPixels'] for n in ('slender','upper','localized')],[255,500,30])
 def test_changed_pixels(self):
  self.assertEqual([self.q['variants'][n]['frames']['18']['changedPixelsVsP1582'] for n in ('slender','upper','localized')],[1794,2900,1608])
 def test_formal_gate(self):
  self.assertIsNone(self.q['selectedForFormalPipeline'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_qa_failure(self):self.assertIn('FAIL',self.q['visualGate'])
 def test_html(self):
  h=(D/'index.html').read_text();self.assertIn('全部视觉门禁 FAIL',h);self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
