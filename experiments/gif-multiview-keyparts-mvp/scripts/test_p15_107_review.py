#!/usr/bin/env python3
"""Validate P0 source-owned garment ink TPS geometry and actual browser outputs."""
import unittest,math,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class P15107(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((R/'evidence/p15-107-ink-qa.json').read_text())
  cls.rv=json.loads((R/'evidence/p15-107-review-qa.json').read_text())
  cls.br=json.loads((R/'evidence/p15-107-browser-qa.json').read_text())
  cls.native=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
  cls.mesh=json.loads((R/'evidence/p15-106-mesh-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
 def test_native_source(self):
  self.assertEqual(self.q['sourceImageSHA256'],self.native['registeredSHA256'])
  self.assertEqual(sha(R/self.native['registeredPath']),self.native['registeredSHA256'])
 def test_shared_mesh_source(self):
  self.assertEqual(self.q['baseTopologySHA256'],self.mesh['meshSHA256'])
 def test_angles(self):
  self.assertEqual(len(self.q['angles']),9)
  self.assertEqual(len(self.q['maps']),7)
 def test_landmarks(self):
  for key,rec in self.q['maps'].items():
   self.assertGreater(rec['landmarks'],30)
   self.assertLess(rec['landmarks'],80)
   self.assertTrue(math.isfinite(rec['meanWarpPixelShift']))
 def test_nonfolding_tps(self):
  for rec in self.q['maps'].values():
   self.assertGreater(rec['minimumJacobian'],0)
   self.assertEqual(rec['negativeJacobianSamples'],0)
 def test_render_methods(self):
  self.assertEqual(len(self.q['methods']),3)
  for method,frames in self.q['methods'].items():
   self.assertEqual(len(frames),9)
 def test_source_endpoints(self):
  for method,frames in self.q['methods'].items():
   for a,view in [('60','60'),('75','75')]:
    self.assertEqual(frames[a]['sha256'],self.top['views'][view]['sourceSHA256'])
 def test_rgba_hash_and_dimensions(self):
  for mode,frames in self.q['methods'].items():
   for record in frames.values():
    f=R/record['path']
    self.assertEqual(record['sha256'],sha(f))
    with Image.open(f) as im:
     self.assertEqual(im.size,(1024,1024))
     self.assertEqual(im.mode,'RGBA')
 def test_metrics(self):
  for method,regions in self.q['metrics'].items():
   for name,data in regions.items():
    self.assertEqual(len(data['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) and x>=0 for x in data['adjacentRGBMAE']))
 def test_interior_frame_metric(self):
  for method,regions in self.q['metrics'].items():
   for region,rec in regions.items():
    self.assertLessEqual(rec['interiorMaxRGBMAE'],rec['maxAdjacentRGBMAE'])
 def test_review_files(self):
  self.assertEqual(len(self.rv['methods']),5)
  for m,frames in self.rv['methods'].items():
   self.assertEqual(len(frames),9)
   for p in frames.values():
    self.assertTrue((P/'p15-107-canonical-ink'/p).resolve().is_file())
 def test_gifs(self):
  self.assertEqual(len(self.rv['gifs']),5)
  for m,record in self.rv['gifs'].items():
   self.assertEqual(sha(R/record['relativePath']),record['sha256'])
 def test_html_controls(self):
  txt=(P/'p15-107-canonical-ink/index.html').read_text()
  for marker in ('id="method"','id="yaw"','id="frame"','id="motion"'):
   self.assertIn(marker,txt)
 def test_browser(self):
  self.assertEqual(self.br['status'],'PASS')
  self.assertEqual(len(self.br['checks']),90)
  self.assertFalse(self.br['errors'])
 def test_semantic_art_approval(self):
  self.assertFalse(self.q['sourceFoldArtistApproved'])
  self.assertFalse(self.q['fullYawVisualAccepted'])
  self.assertFalse(self.rv['sourceContinuityApproved'])
if __name__=='__main__':unittest.main()
