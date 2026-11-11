import unittest,hashlib,json
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-71-sam-semantic'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1571(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-71-source-gate-qa.json').read_text())
 def test_source_sha(self):
  self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['currentSourceSHA256'])
 def test_prior_layer_hashes(self):
  paths={'yaw045':R/'private-assets/p15-20-canonical-source-views/yaw045/hair.front.png',
         'yaw090':R/'private-assets/p15-20-canonical-source-views/yaw090/hair.front.png',
         'prior41':R/'private-assets/exports/p15-41-profile-candidate/layers/hair.front.png'}
  for k,p in paths.items():self.assertEqual(self.q['legacyIndependentHairSHA256'][k],sha(p))
 def test_existing_chroma_sha(self):
  self.assertEqual(self.q['colorLayerSHA256'],sha(R/'private-assets/exports/p15-69-clip-separation/hair-front-no-gold-candidate.png'))
 def test_review_source_image(self):
  with Image.open(D/'current-right-source.png') as im:self.assertEqual(im.size,(690,795))
 def test_sam_input_sha(self):
  self.assertEqual(self.q['sam2InputSHA256'],sha(D/'input-512.png'))
 def test_sam_call_records(self):
  self.assertEqual(self.q['sam2EndpointStatus']['on_image_select'],'FAILED')
  self.assertEqual(self.q['sam2EndpointStatus']['segment_everything'],'FAILED')
 def test_zero_gpu_failure_grounded(self):
  self.assertIn('ZeroGPU quota exceeded',self.q['sam2SegmentEverythingError'])
 def test_no_model_output(self):
  self.assertFalse(self.q['sam2VisibleCutoutProduced'])
 def test_no_same_view(self):
  self.assertFalse(self.q['legacySourcesAreSameP156Source'])
  self.assertFalse(self.q['sameViewCleanFrontHairAvailable'])
 def test_no_artmesh_approval(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_gate_fails(self):
  self.assertTrue(self.q['visualGate'].startswith('FAIL_'))
 def test_motion_review(self):
  for dx in (0,9,18):
   p=D/('p15-70-composite.png' if dx==18 else f'p15-70-eye-shift-{dx:02d}.png')
   with Image.open(p) as im:self.assertEqual(im.size,(1024,1024))
 def test_html_discloses_failed_semantics(self):
  h=(D/'index.html').read_text()
  self.assertIn('正式门禁 FAIL',h)
  self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
