#!/usr/bin/env python3
"""Verify Codex model origin, bounded ArtMesh repair and deterministic HTML evidence."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';C=R/'private-assets/p15-91-codex'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
class P1591(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.codex=json.loads((C/'codex-closeup-result.json').read_text())
  cls.q=json.loads((R/'evidence/p15-91-codex-qa.json').read_text())
  cls.hair=json.loads((R/'evidence/p15-91-hair-ownership-qa.json').read_text())
  cls.motion=json.loads((R/'evidence/p15-91-temporal-qa.json').read_text())
  cls.flow=json.loads((R/'evidence/p15-91-flow-qa.json').read_text())
 def test_native_model(self):self.assertTrue(self.codex['actual_image_tool_used'])
 def test_model_image(self):
  with Image.open(C/'codex-closeup-candidate.png') as image:
   self.assertEqual(image.size,(1254,1254))
  self.assertEqual(self.q['rawGeneratedSHA256'],sha(C/'codex-closeup-candidate.png'))
 def test_semantic_hair_alpha(self):
  source=Image.open(P/'p15-81-image-layered/sam3-027-hair-rgba.png').convert('RGBA')
  candidate=Image.open(P/'p15-91-hair-ownership/tight-front-hair.png').convert('RGBA')
  self.assertEqual(source.getchannel('A').tobytes(),candidate.getchannel('A').tobytes())
 def test_spatial_containment(self):
  for item in self.hair['variants'].values():
   for f in item['frames'].values():self.assertEqual(f['outsidePermittedPixels'],0)
 def test_source_rest(self):
  ref=sha(P/'p15-82-rest-underpaint/candidate-00.png')
  self.assertEqual(ref,self.motion['frames']['0']['sha256'])
  self.assertTrue(self.motion['zeroPoseExact'])
 def test_keyframe_9(self):
  a=sha(P/'p15-91-flow-transition/blend-09.png')
  b=sha(P/'p15-91-hair-ownership/tight-09.png')
  self.assertEqual(a,b)
 def test_keyframe_18(self):
  a=sha(P/'p15-91-flow-transition/blend-18.png')
  b=sha(P/'p15-91-hair-ownership/tight-18.png')
  self.assertEqual(a,b)
 def test_flow_first(self):self.assertLess(self.flow['modes']['blend']['firstRatio'],1.3)
 def test_flow_max(self):self.assertLess(self.flow['modes']['blend']['max'],4.2)
 def test_motion_19(self):self.assertEqual(self.flow['modes']['blend']['totalFrames'],19)
 def test_hair_component(self):
  for dx in ('9','18'):
   f=self.hair['variants']['tight']['frames'][dx]
   self.assertEqual(f['fringeAfter'],0)
   self.assertEqual(f['newHoles'],0)
 def test_image_hashes(self):
  for dx in (0,9,18):
   self.assertEqual(sha(P/f'p15-91-temporal-motion/frame-{dx:02}.png'),self.motion['frames'][str(dx)]['sha256'])
 def test_html_controls(self):
  h=(P/'p15-91-flow-transition/index.html').read_text()
  self.assertIn('id="shift"',h)
  self.assertIn('id="candidate"',h)
 def test_review_candidate(self):self.assertFalse(self.hair['formalArtMeshAccepted'])
if __name__=='__main__':unittest.main()
