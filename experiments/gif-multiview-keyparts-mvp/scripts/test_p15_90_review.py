#!/usr/bin/env python3
"""Hash and spatial-bound checks for P0 underpaint review evidence."""
from pathlib import Path
from PIL import Image
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
class ModelReview(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.model=json.loads((R/'evidence/p15-90-qwen-masked-inference-qa.json').read_text())
  cls.q=json.loads((R/'evidence/p15-90-precision-mask-qa.json').read_text())
 def test_model_actual(self):
  self.assertEqual(self.model['status'],'MODEL_RETURNED')
  self.assertTrue(self.model['modelOutputCreated'])
 def test_model_sha(self):
  self.assertEqual(sha(P/'p15-90-qwen-masked/returned-model-1024.png'),self.model['outputSHA256'])
 def test_mask_source(self):
  self.assertEqual(self.q['modelSHA256'],self.model['outputSHA256'])
 def test_three_variants(self):
  self.assertEqual(set(self.q['variants']),{'r4','r6','r8'})
 def test_r4_mask_sha(self):
  self.assertEqual(self.q['variants']['r4']['maskSHA256'],sha(P/'p15-90-precision-mask/r4-mask.png'))
 def test_r4_rest_exact(self):
  f=self.q['variants']['r4']['frames']['0']
  self.assertEqual(f['sha256'],sha(P/'p15-82-rest-underpaint/candidate-00.png'))
  self.assertEqual(f['changedPixels'],0)
 def test_all_frames_have_verified_hashes(self):
  for tag,data in self.q['variants'].items():
   for pose,frame in data['frames'].items():
    self.assertEqual(frame['sha256'],sha(P/f'p15-90-precision-mask/{tag}-{int(pose):02}.png'))
 def test_spatial_mask(self):
  for tag,data in self.q['variants'].items():
   for frame in data['frames'].values():self.assertEqual(frame['outsideMask'],0)
 def test_dark_residual(self):
  for pose in ['9','18']:
   f=self.q['variants']['r4']['frames'][pose]
   self.assertGreater(f['darkBefore'],0)
   self.assertEqual(f['darkAfter'],0)
 def test_native_layers(self):
  psd=P.parent/'p15-90-seethrough/p0-character-001-see-through.psd'
  self.assertTrue(psd.exists())
  self.assertGreater(psd.stat().st_size,1000000)
 def test_html_controls(self):
  h=(P/'p15-90-precision-mask/index.html').read_text()
  self.assertIn('id="shift"',h)
  self.assertIn('id="candidate"',h)
 def test_visual_status(self):
  self.assertFalse(self.q['candidateAccepted'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
if __name__=='__main__':unittest.main()
