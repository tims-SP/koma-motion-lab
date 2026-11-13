#!/usr/bin/env python3
"""Verify P0 source-owned radial three-view mesh, RGBA, geometry, VDD and browser evidence."""
import unittest,json,hashlib,math
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
class P15106(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=json.loads((P/'p15-106-three-key-mesh/garment-three-key-mesh.json').read_text())
  cls.mq=json.loads((R/'evidence/p15-106-mesh-qa.json').read_text())
  cls.r=json.loads((R/'evidence/p15-106-render-qa.json').read_text())
  cls.v=json.loads((R/'evidence/p15-106-review-qa.json').read_text())
  cls.b=json.loads((R/'evidence/p15-106-browser-qa.json').read_text())
  cls.native=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
 def test_character_and_sources(self):
  self.assertEqual(self.m['characterId'],'p0_character_001')
  self.assertEqual(self.mq['sourceAngles'],[60,67.5,75])
  self.assertEqual(self.m['viewKeys'],['60','67.5','75'])
  self.assertEqual(self.r['sourceAngles'],[60,67.5,75])
 def test_native_mid_registered_source(self):
  self.assertEqual(self.r['native67p5SourceSha256'],sha(R/self.native['nativePath']))
  self.assertEqual(self.mq['sourceRegSHA256'],sha(R/self.native['registeredPath']))
 def test_mesh_sha_identity(self):
  path=P/'p15-106-three-key-mesh/garment-three-key-mesh.json'
  self.assertEqual(self.mq['meshSHA256'],sha(path))
  self.assertEqual(self.r['meshSHA256'],sha(path))
 def test_semantic_part_count(self):
  self.assertEqual(len(self.m['roles']),4)
  self.assertEqual(set(self.m['roles']),{'shoulder.left','collar','bow','jewel'})
 def test_vertices_and_triangles(self):
  self.assertEqual(sum(len(x['vertices']) for x in self.m['roles'].values()),132)
  self.assertEqual(sum(len(x['triangles']) for x in self.m['roles'].values()),192)
  for role,x in self.m['roles'].items():
   self.assertEqual(len(x['vertices']),33)
   self.assertEqual(len(x['triangles']),48)
   self.assertEqual(len(set(tuple(tri) for tri in x['triangles'])),48)
 def test_three_view_uvs(self):
  for role,x in self.m['roles'].items():
   for v in x['vertices']:
    self.assertEqual(set(v['sourcePosition']),{'60','67.5','75'})
    self.assertEqual(set(v['viewUV']),{'60','67.5','75'})
    for uv in v['viewUV'].values():
     self.assertTrue(all(0<=x<=1 for x in uv))
 def test_nonfolding_both_segments(self):
  for role,q in self.mq['parts'].items():
   self.assertEqual(len(q['sampledGeometry']),18)
   self.assertEqual(len({tuple(x['segment']) for x in q['sampledGeometry']}),2)
   for sample in q['sampledGeometry']:
    self.assertEqual(sample['negativeTriangles'],0)
    self.assertGreater(sample['minSignedArea'],0)
 def test_source_role_files(self):
  for role,entry in self.m['roles'].items():
   for view,file in entry['viewSourceImages'].items():
    with Image.open(R/file) as f:
     self.assertEqual(f.mode,'RGBA')
     self.assertEqual(f.size,(1024,1024))
 def test_garment_exact_partition(self):
  self.assertTrue(self.mq['sourcePixelReconstruction'])
  for view in ('60','67p5','75'):
   folder=P/f'p15-106-three-key-mesh/yaw{view}'
   base=np.asarray(Image.open(folder/'remainder.png').convert('RGBA'))
   occupied=np.zeros(base.shape[:2],bool)
   result=base.copy()
   for role in self.m['roles']:
    ar=np.asarray(Image.open(folder/(role.replace('.','_')+'.png')).convert('RGBA'))
    mask=ar[:,:,3]>0
    self.assertFalse(np.any(mask&occupied))
    occupied|=mask
    result[mask]=ar[mask]
   self.assertTrue(np.any(result[:,:,3]>100))
 def test_endpoints_pixel_exact(self):
  for mode,frames in self.r['methods'].items():
   for angle,view in [('60','60'),('75','75')]:
    self.assertEqual(frames[angle]['sha256'],self.top['views'][view]['sourceSHA256'])
 def test_middle_native_pixels(self):
  self.assertEqual(self.r['nativeMiddleRgbaExactFraction'],1.0)
 def test_frames(self):
  self.assertEqual(len(self.r['methods']),3)
  for mode,frames in self.r['methods'].items():
   self.assertEqual(len(frames),9)
   for angle,rec in frames.items():
    file=R/rec['path']
    self.assertEqual(rec['sha256'],sha(file))
    with Image.open(file) as im:
     self.assertEqual(im.mode,'RGBA')
     self.assertEqual(im.size,(1024,1024))
 def test_region_temporal_metrics(self):
  self.assertEqual(len(self.r['metrics']),5)
  for mode,regions in self.r['metrics'].items():
   for roi,rec in regions.items():
    self.assertEqual(len(rec['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) for x in rec['adjacentRGBMAE']))
 def test_review_gif_provenance(self):
  self.assertEqual(len(self.v['animations']),5)
  for rec in self.v['animations'].values():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_review_html(self):
  html=(P/'p15-106-three-key-render/index.html').read_text()
  for key in ('id="method"','id="yaw"','id="frame"','id="loop"'):
   self.assertIn(key,html)
 def test_browser_viewports(self):
  self.assertEqual(self.b['status'],'PASS')
  self.assertEqual(len(self.b['checks']),90)
  self.assertFalse(self.b['errors'])
 def test_visual_review_is_independent(self):
  self.assertFalse(self.m['formalArtistApproval'])
  self.assertFalse(self.r['continuousYawVisualAccepted'])
  self.assertFalse(self.v['continuousVisualAccepted'])
if __name__=='__main__':unittest.main()
