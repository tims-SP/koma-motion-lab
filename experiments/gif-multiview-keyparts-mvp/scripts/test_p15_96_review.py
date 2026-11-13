#!/usr/bin/env python3
"""P0 local ArtMesh source identity, constrained deformation and browser evidence tests."""
from pathlib import Path
from PIL import Image
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports';D=P/'p15-96-yaw060-root-artmesh'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class P1596(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=json.loads((R/'evidence/p15-96-motion-qa.json').read_text())
  cls.r=json.loads((R/'evidence/p15-96-root-pinned-qa.json').read_text())
  cls.d=json.loads((R/'evidence/p15-96-disocclusion-qa.json').read_text())
  cls.b=json.loads((R/'evidence/p15-96-browser-qa.json').read_text())
 def test_source_identity(self):
  self.assertEqual(self.m['sourceSHA256'],sha(P/'p15-92-angle-keyart/yaw060-registered.png'))
 def test_model_origin(self):
  self.assertEqual(self.m['modelSHA256'],sha(P/'p15-95-yaw060-motion/generated-face-aligned.png'))
 def test_hair_source(self):
  self.assertEqual(self.m['hairSHA256'],sha(P/'p15-95-yaw060-motion/inset-front-hair.png'))
 def test_all_frames_sha(self):
  self.assertEqual(self.m['frameCount'],13)
  for dx in range(13):
   self.assertEqual(self.m['frames'][str(dx)]['sha256'],sha(D/f'frame-{dx:02}.png'))
 def test_zero_pose_exact(self):
  self.assertTrue(self.m['zeroPoseSourceOwnedExact'])
  self.assertEqual(self.m['frames']['0']['sha256'],self.m['sourceSHA256'])
 def test_root_pixels_unchanged(self):
  self.assertEqual(self.m['foreheadTriangleChangedPixels'],0)
  for frame in self.m['frames'].values():self.assertEqual(frame['foreheadTriangleChangedPixels'],0)
 def test_actual_tip_motion(self):
  self.assertGreater(self.m['frames']['12']['tipChangedPixels'],3000)
 def test_no_outside_or_holes(self):
  self.assertEqual(self.m['changedOutsideHairSupports'],0)
  self.assertEqual(self.m['newTransparentHoles'],0)
 def test_temporal_metric(self):
  self.assertLess(self.m['maxAdjacentLocalRGBMAE'],0.5)
  self.assertLess(self.m['firstStepToLaterMedianRatio'],1.4)
 def test_variant_comparison(self):
  self.assertEqual(set(self.r['modes']),{'full','root390','root420','root445'})
  self.assertEqual(self.r['modes']['root420']['frames']['12']['topRegionChangedPixels'],0)
 def test_disocclusion_ownership(self):
  for variant in self.d['methods'].values():
   self.assertEqual(variant['frames']['0']['changedPixels'],0)
   self.assertEqual(variant['frames']['12']['changedOutsideHairSupports'],0)
 def test_gif_digest(self):
  self.assertEqual(self.m['gifSHA256'],sha(D/'root-pinned-13-poses.gif'))
 def test_browser(self):
  self.assertEqual(self.b['status'],'PASS')
  self.assertEqual(len(self.b['checks']),26)
  self.assertFalse(self.b['errors'])
 def test_html(self):
  html=(D/'index.html').read_text()
  self.assertIn('id="pose"',html)
  self.assertIn('id="candidate"',html)
 def test_formal_gate(self):
  self.assertFalse(self.m['formalArtMeshAccepted'])
  self.assertFalse(self.m['semanticLayerApproved'])
if __name__=='__main__':unittest.main()
