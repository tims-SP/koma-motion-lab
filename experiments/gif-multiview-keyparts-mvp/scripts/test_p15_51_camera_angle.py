import hashlib,json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'private-assets';D=P/'exports/p15-51-camera-angle-review'
class CameraAngleCandidate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-51-camera-angle-qa.json').read_text())
 def test_source_identity_is_approved_p0_45(self):
  p=P/'exports/p15-38-original-p0-arc-review/p0-yaw45-original.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['source']['sha256'])
 def test_positive20_is_real_output(self):
  p=P/'exports/p15-51-qwen-angle-plus20deg.webp'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['positive20']['sha256'])
  self.assertEqual(self.q['positive20']['seed'],65451)
 def test_negative20_rejected(self):
  self.assertIn('closer to frontal',self.q['negative20']['interpretation'])
 def test_not_formal_keyframe(self):
  self.assertFalse(self.q['formalArtMeshModified'])
  self.assertFalse(self.q['formal65Accepted'])
 def test_output_opaque(self):
  from PIL import Image
  im=Image.open(P/'exports/p15-51-qwen-angle-plus20deg.webp')
  self.assertEqual(im.mode,'RGB');self.assertEqual(im.size,(1024,1024))
 def test_review_assets(self):
  h=(D/'index.html').read_text()
  for n in ['source45.png','camera_right20.webp','camera_left20.webp']:self.assertIn(n,h);self.assertTrue((D/n).is_file())
if __name__=='__main__':unittest.main()
