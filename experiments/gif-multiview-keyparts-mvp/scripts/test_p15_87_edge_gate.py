from pathlib import Path
from PIL import Image
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-87-hair-face-seam'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1587(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-87-qa.json').read_text())
 def test_source_sha(self):self.assertEqual(sha(P/'p15-56-edge-matting/candidate-erode-2.png'),self.q['inputSHA256']['source'])
 def test_underpaint_sha(self):self.assertEqual(sha(P/'p15-86-semantic-ownership/hidden-face.reassigned.png'),self.q['inputSHA256']['underpaint'])
 def test_donor_sha(self):self.assertEqual(sha(P/'p15-70-seam-repair/forehead-seam-repaired.png'),self.q['inputSHA256']['donor'])
 def test_hair_sha(self):self.assertEqual(sha(P/'p15-86-semantic-ownership/bangs.without-source-eyelash.png'),self.q['inputSHA256']['hair'])
 def test_clip_sha(self):self.assertEqual(sha(P/'p15-82-rest-underpaint/part.source-clip.png'),self.q['inputSHA256']['clip'])
 def test_exact_six_variants(self):self.assertEqual(len(self.q['proposals']),6)
 def test_poses(self):self.assertTrue(all(set(v['frames'])=={'9','18'} for v in self.q['proposals'].values()))
 def test_variant_mask_sha(self):
  for k,v in self.q['proposals'].items():self.assertEqual(sha(D/f'{k}-mask.png'),v['maskSHA256'])
 def test_variant_underpaint_sha(self):
  for k,v in self.q['proposals'].items():self.assertEqual(sha(D/f'{k}-underpaint.png'),v['underpaintSHA256'])
 def test_variant_motion_sha(self):
  for k,v in self.q['proposals'].items():
   for dx,f in v['frames'].items():self.assertEqual(sha(D/f'{k}-{int(dx):02d}.png'),f['sha256'])
 def test_edge_still_present(self):
  for v in self.q['proposals'].values():
   for dx in ['9','18']:self.assertEqual(v['frames'][dx]['darkDangling'],self.q['baseline'][dx]['darkDangling'])
 def test_no_new_holes(self):self.assertTrue(all(f['faceHoles']==0 for v in self.q['proposals'].values() for f in v['frames'].values()))
 def test_zero_rest_source_recompose(self):
  a=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA').tobytes()
  b=Image.open(D/'frame-00-from-source-layers.png').convert('RGBA').tobytes()
  self.assertTrue(all(a[i:i+4]==b[i:i+4] or a[i+3]==0 for i in range(0,len(a),4)))
 def test_rest_sha(self):self.assertEqual(sha(D/'frame-00-from-source-layers.png'),self.q['restSHA256'])
 def test_not_accepted(self):self.assertFalse(self.q['candidateAccepted']);self.assertFalse(self.q['formalArtMeshAccepted']);self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_visual_fail(self):self.assertTrue(self.q['visualGate'].startswith('FAIL_'))
 def test_review(self):
  h=(D/'index.html').read_text();self.assertIn('正式视觉门禁 FAIL',h);self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
