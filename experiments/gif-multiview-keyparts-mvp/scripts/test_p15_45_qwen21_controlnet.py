import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets';D=P/'exports/p15-45-qwen21-controlnet-review'
class Qwen21Controlnet(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-45-qwen21-controlnet-qa.json').read_text())
 def test_model_output_hash(self):
  p=P/'exports/p15-45-qwen21-controlnet-candidate.png';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['outputSHA256'])
 def test_output_dimensions(self):
  with Image.open(P/'exports/p15-45-qwen21-controlnet-candidate.png') as im:self.assertEqual(im.size,(1024,1024));self.assertEqual(im.mode,'RGBA')
 def test_control_image_was_fed(self):self.assertEqual(self.q['backend'],'hugging-apps/qwen-image-2-1-controlnet-union-demo');self.assertEqual(self.q['controlContextScale'],1.0)
 def test_fixed_seed(self):self.assertEqual(self.q['seed'],65445);self.assertNotEqual(self.q['secondSeedAttempt']['status'],'SUCCESS')
 def test_face_and_identity_review_assets(self):
  for n in ['registered-65.png','identity-45.png','candidate.png','control-fed.png','candidate-anchor-overlay.png']:self.assertTrue((D/n).is_file())
 def test_all_review_asset_hashes(self):
  for n,v in self.q['images'].items():self.assertEqual(hashlib.sha256((D/n).read_bytes()).hexdigest(),v['sha256'])
 def test_candidate_not_formally_accepted(self):self.assertFalse(self.q['candidateAcceptedAsFormalKeyframe']);self.assertFalse(self.q['exactYawAccepted'])
 def test_artmesh_not_modified(self):self.assertFalse(self.q['artMeshModified'])
if __name__=='__main__':unittest.main()
