#!/usr/bin/env python3
"""Check model provenance, independent raw keyart, and view interpolation evidence."""
from pathlib import Path
from PIL import Image
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1]
A=R/'private-assets';D=A/'exports/p15-93-yaw0525-review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class P1593(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((R/'evidence/p15-93-native52-qa.json').read_text())
  cls.a=json.loads((R/'evidence/p15-93-flow-ablation-qa.json').read_text())
  cls.b=json.loads((R/'evidence/p15-93-boundary-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-93-browser-qa.json').read_text())
 def test_model_origin(self):
  meta=json.loads((A/'p15-93-yaw0525/generation-result.json').read_text())
  self.assertTrue(meta['actual_image_tool_used'])
  self.assertEqual(meta['sha256'],sha(A/'p15-93-yaw0525/yaw0525-native.png'))
 def test_native_image(self):
  with Image.open(A/'p15-93-yaw0525/yaw0525-native.png') as im:
   self.assertEqual(im.size,(1254,1254))
   self.assertIn('A',im.getbands())
 def test_registered(self):
  self.assertEqual(self.q['registeredSourceSHA256'],sha(D/'yaw052p5-registered.png'))
  with Image.open(D/'yaw052p5-registered.png') as im:self.assertEqual(im.size,(1024,1024))
 def test_interpolated_sha(self):
  for p in self.q['frames'].values():
   self.assertEqual(sha(R/p['path']),p['sha256'])
 def test_flow_ablations(self):
  self.assertEqual(len(self.a['frames']),3)
  for ang,modes in self.a['frames'].items():
   self.assertEqual(set(modes),{'blend','forward','backward'})
   for it in modes.values():self.assertEqual(sha(R/it['path']),it['sha256'])
 def test_boundary(self):
  self.assertEqual(len(self.b['segments']),3)
  for result in self.b['segments'].values():
   self.assertGreater(result['forward']['boundaryToInternalRatio'],result['blend']['boundaryToInternalRatio'])
 def test_html(self):
  s=(D/'index.html').read_text()
  self.assertIn('id="angle"',s);self.assertIn('id="current"',s)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),10)
  self.assertFalse(self.browser['errors'])
 def test_fidelity_pending(self):
  self.assertFalse(self.q['actualYawVerified'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
if __name__=='__main__':unittest.main()
