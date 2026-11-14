from pathlib import Path
from PIL import Image
import json,hashlib,unittest
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-88-painted-hidden-edge'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class TestP1588(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((D/'provenance.json').read_text())
 def test_real_model(self):self.assertEqual(self.q['model'],'Qwen-Image-Edit-2511')
 def test_seed(self):self.assertEqual(self.q['seed'],887004)
 def test_output_exists(self):self.assertTrue((D/'qwen-edit-887004.png').is_file())
 def test_output_size(self):
  with Image.open(D/'qwen-edit-887004.png') as im:self.assertEqual(im.size,(1024,1024))
 def test_output_sha(self):self.assertEqual(sha(D/'qwen-edit-887004.png'),self.q['artifacts']['qwen-edit-887004.png']['sha256'])
 def test_source_crop_sha(self):self.assertEqual(sha(D/'source-target-crop-640.png'),self.q['artifacts']['source-target-crop-640.png']['sha256'])
 def test_identity_input_sha(self):self.assertEqual(sha(D/'input-identity-head.jpg'),self.q['artifacts']['input-identity-head.jpg']['sha256'])
 def test_three_alignments(self):
  for n in ('aligned-a.png','aligned-b.png','aligned-c.png'):self.assertTrue((D/n).is_file())
 def test_three_overlays(self):
  for n in ('overlay-a.png','overlay-b.png','overlay-c.png'):self.assertTrue((D/n).is_file())
 def test_geometry_fail(self):self.assertIn('GEOMETRY_DRIFT',self.q['visualGate'])
 def test_candidate_rejected(self):self.assertFalse(self.q['candidateAccepted'])
 def test_no_artmesh(self):self.assertFalse(self.q['formalArtMeshAccepted'])
 def test_no_keyframe(self):self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_report_exists(self):self.assertTrue((D/'index.html').is_file())
 def test_report_gate(self):self.assertIn('视觉门禁 FAIL',(D/'index.html').read_text())
 def test_original_p1586_stays(self):
  p=R/'private-assets/exports/p15-86-semantic-ownership/hidden-face.reassigned.png'
  self.assertTrue(p.is_file())
if __name__=='__main__':unittest.main()
