import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-44-control-inputs'
Q=R/'evidence/p15-44-control-conditions-qa.json'
class ControlInputs(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(Q.read_text())
 def test_source_hash(self):
  self.assertEqual(self.q['sourceRegisteredSHA256'],hashlib.sha256((R/'private-assets/p15-38-p0-registered-arc/yaw65/composite.png').read_bytes()).hexdigest())
 def test_identity_hash(self):
  self.assertEqual(self.q['sourceIdentitySHA256'],hashlib.sha256((R/'private-assets/p2-views/whole/yaw045.png').read_bytes()).hexdigest())
 def test_anchor_count(self):self.assertEqual(len(self.q['anchors']),6)
 def test_anchor_bounds(self):
  for anchor in self.q['anchors'].values():self.assertTrue(all(0<=v<1024 for v in anchor['xy']))
 def test_images_have_expected_dimensions(self):
  for n in self.q['artifacts']:
   with Image.open(D/n) as im:self.assertEqual(im.size,(1024,1024))
 def test_artifact_hashes(self):
  for n,v in self.q['artifacts'].items():self.assertEqual(v['sha256'],hashlib.sha256((D/n).read_bytes()).hexdigest())
 def test_html_links(self):
  s=(D/'index.html').read_text()
  for n in self.q['artifacts']:self.assertIn('src="'+n+'"',s)
 def test_approval_gate(self):
  self.assertFalse(self.q['acceptedAsAuthoredKeyframe'])
  self.assertFalse(self.q['backendAssessment']['generatedWithConditioning'])
  self.assertFalse(self.q['existingVDDArtModified'])
if __name__=='__main__':unittest.main()
