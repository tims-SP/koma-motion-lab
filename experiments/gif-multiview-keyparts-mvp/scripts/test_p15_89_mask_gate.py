from pathlib import Path
from PIL import Image
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-89-masked-local-art'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class TestP1589(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.q=json.loads((R/'evidence/p15-89-final-qa.json').read_text())
  c.a=json.loads((R/'evidence/p15-89-masked-inference-qa.json').read_text())
  c.b=json.loads((R/'evidence/p15-89-sd-masked-qa.json').read_text())
 def test_source_sha(self):self.assertEqual(sha(D/'full-source-1024.png'),self.q['sourceSHA256'])
 def test_mask_sha(self):self.assertEqual(sha(D/'local-mask-1024.png'),self.q['maskSHA256'])
 def test_control_sha(self):self.assertEqual(sha(D/'control-lineart-1024.png'),self.a['controlSHA256'])
 def test_original_input_sha(self):
  self.assertEqual(self.a['sourceSHA256'],sha(R/'private-assets/exports/p15-86-semantic-ownership/hidden-face.reassigned.png'))
 def test_canvas(self):
  with Image.open(D/'full-source-1024.png') as img: self.assertEqual(img.size,(1024,1024))
 def test_mask_area(self):self.assertEqual(self.q['maskActivePixels'],2259)
 def test_mask_bbox(self):self.assertEqual(self.q['maskBBox'],[499,424,553,479])
 def test_explicit_model_mask(self):self.assertTrue(self.a['maskPassedAsTrueModelArgument'])
 def test_explicit_sd_mask(self):self.assertTrue(self.b['maskPassedAsTrueModelArgument'])
 def test_qwen_event(self):self.assertTrue(self.a.get('eventId'))
 def test_sd_event(self):self.assertTrue(self.b.get('eventId'))
 def test_no_formal_accept(self):self.assertFalse(self.q['formalArtMeshAccepted'])
 def test_no_keyframe(self):self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_no_auto_candidate(self):self.assertFalse(self.q['candidateAccepted'])
 def test_old_zero_sha(self):
  self.assertEqual(sha(R/'private-assets/exports/p15-86-semantic-ownership/frame-reassigned-00.png'),self.q['sourceZeroPoseReferenceSHA256'])
 def test_outside_mask_immutable(self):
  for c in self.q.get('modelCandidates',{}).values():self.assertEqual(c['outsideMaskChangedPixels'],0)
 def test_visual_held(self):self.assertFalse(self.q['newDynamicRenderAccepted'])
 def test_review(self):self.assertIn('正式视觉门禁',(D/'index.html').read_text())
if __name__=='__main__':unittest.main()
