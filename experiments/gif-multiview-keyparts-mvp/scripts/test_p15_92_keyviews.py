#!/usr/bin/env python3
"""Verify original keyart model provenance, native raster identity and browser outputs."""
import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];A=R/'private-assets';P=A/'exports/p15-92-angle-keyart'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1592(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((R/'evidence/p15-92-native-keyart-qa.json').read_text())
  cls.flow=json.loads((R/'evidence/p15-92-view-flow-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-92-browser-qa.json').read_text())
 def test_two_native_image_tools(self):
  for p in (A/'p15-92-codex/generation-result.json',A/'p15-92-yaw075/generation-result.json'):
   meta=json.loads(p.read_text());self.assertEqual(meta['tool'] if 'tool' in meta else meta['actual_image_tool_used'],'image_gen.imagegen')
 def test_native60_hash(self):
  self.assertEqual(self.q['nativeOutputSHA256'],sha(A/'p15-92-codex/yaw060-native.png'))
 def test_native75_hash(self):
  self.assertEqual(self.q['nativeYaw75SHA256'],sha(A/'p15-92-yaw075/yaw075-native.png'))
 def test_native_dimensions(self):
  for a,p in [(60,A/'p15-92-codex/yaw060-native.png'),(75,A/'p15-92-yaw075/yaw075-native.png')]:
   with Image.open(p) as im:self.assertEqual(im.size,(1254,1254))
 def test_rgba_registered(self):
  for a in [60,75]:
   with Image.open(P/f'yaw{a:03d}-registered.png') as im:self.assertEqual((im.size,im.mode),((1024,1024),'RGBA'))
 def test_registered_hashes(self):
  self.assertEqual(self.q['registeredOutputSHA256'],sha(P/'yaw060-registered.png'))
  self.assertEqual(self.q['registeredYaw75SHA256'],sha(P/'yaw075-registered.png'))
 def test_source_endpoints(self):
  self.assertEqual(sha(P/'yaw045-reference.png'),self.q['inputSourceHashes']['yaw045'])
  self.assertEqual(sha(P/'yaw090-reference.png'),self.q['inputSourceHashes']['yaw090'])
 def test_declared_views(self):
  self.assertEqual(self.flow['sourceAngles'],[45,60,75,90])
  self.assertEqual(self.flow['interpolationOnlyAngles'],[52.5,67.5,82.5])
 def test_all_seven_outputs(self):
  self.assertEqual(len(self.flow['frames']),7)
  for sample,info in self.flow['frames'].items():self.assertEqual(sha(R/info['path']),info['sha256'])
 def test_independent_keyframe_exact(self):
  for x,p in [(45,'yaw045-reference.png'),(60,'yaw060-registered.png'),(75,'yaw075-registered.png'),(90,'yaw090-reference.png')]:
   frame=R/self.flow['frames'][str(x)]['path']
   with Image.open(frame) as a, Image.open(P/p) as b:
    self.assertEqual(a.convert('RGBA').tobytes(),b.convert('RGBA').tobytes())
 def test_silhouette_positive(self):
  for angle in ['45','60','75','90']:
   m=self.q['sourceMetrics'][angle];self.assertGreater(m['alpha128Pixels'],300000)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),14)
  self.assertFalse(self.browser['errors'])
 def test_html(self):
  html=(P/'index.html').read_text()
  self.assertIn('id="angle"',html);self.assertIn('id="pose-image"',html)
 def test_visual_status(self):
  self.assertFalse(self.q['actualYawVerified'])
  self.assertFalse(self.flow['formalArtMeshAccepted'])
  self.assertFalse(self.flow['formalKeyframeAccepted'])
if __name__=='__main__':unittest.main()
