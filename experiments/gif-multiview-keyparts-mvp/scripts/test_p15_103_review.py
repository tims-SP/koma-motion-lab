#!/usr/bin/env python3
"""Native P0 garment layer exactness, shared mesh UV, actual renders and Chromium."""
import unittest,json,hashlib,math
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Garment(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.parts=json.loads((R/'evidence/p15-103-parts-qa.json').read_text())
  cls.mesh=json.loads((P/'p15-103-part-mesh/garment-parts-mesh.json').read_text())
  cls.meshqa=json.loads((R/'evidence/p15-103-mesh-qa.json').read_text())
  cls.render=json.loads((R/'evidence/p15-103-render-qa.json').read_text())
  cls.flow=json.loads((R/'evidence/p15-103-flow-qa.json').read_text())
  cls.rev=json.loads((R/'evidence/p15-103-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-103-browser-qa.json').read_text())
 def test_source_pixel_reconstruction(self):
  self.assertTrue(self.parts['sourceReassemblyExact'])
  for view,info in self.parts['views'].items():
   original=np.asarray(Image.open(R/info['source']).convert('RGBA'))
   rec=np.asarray(Image.open(P/f'p15-103-parts/yaw{view}/reconstructed.png').convert('RGBA'))
   self.assertTrue(np.array_equal(original,rec))
 def test_layer_one_owner(self):
  for view in ('60','75'):
   count=np.zeros((1024,1024),dtype=np.uint8)
   for role in self.parts['partOrder']:
    mask=np.asarray(Image.open(P/f'p15-103-parts/yaw{view}/{role.replace(".","_")}-ownership.png').convert('L'))>128
    count+=mask.astype(np.uint8)
   self.assertTrue(np.all(count==1))
 def test_source_layer_hashes(self):
  for view,info in self.parts['views'].items():
   for role,record in info['partStats'].items():
    stem=role.replace('.','_');p=P/f'p15-103-parts/yaw{view}'
    self.assertEqual(record['textureSHA256'],sha(p/f'{stem}.png'))
    self.assertEqual(record['maskSHA256'],sha(p/f'{stem}-ownership.png'))
 def test_semantic_part_masks(self):
  self.assertEqual(self.parts['partOrder'],['jacket','shoulder.left','collar','bow','jewel'])
  for v,data in self.parts['views'].items():
   self.assertGreater(data['partStats']['bow']['opaquePixels'],10000)
   self.assertGreater(data['partStats']['jewel']['opaquePixels'],1500)
 def test_mesh_identity(self):
  self.assertEqual(self.mesh['characterId'],'p0_character_001')
  self.assertEqual(self.meshqa['meshSHA256'],sha(P/'p15-103-part-mesh/garment-parts-mesh.json'))
  self.assertEqual(self.render['meshSHA256'],self.meshqa['meshSHA256'])
 def test_mesh_topology(self):
  self.assertEqual(self.meshqa['vertexCount'],36)
  self.assertEqual(self.meshqa['triangleCount'],32)
  for role,data in self.mesh['roles'].items():
   self.assertEqual(len(data['vertices']),9)
   self.assertEqual(len(data['triangles']),8)
   for vertex in data['vertices']:
    for view,uv in vertex['viewUV'].items():
     self.assertTrue(all(0<=a<=1 for a in uv))
 def test_geometry_nonfolding(self):
  self.assertEqual(self.meshqa['negativeTriangleCount'],0)
  for role,item in self.mesh['roles'].items():
   self.assertEqual(len(item['geometry']),9)
   for point in item['geometry']:
    self.assertEqual(point['folds'],0)
    self.assertGreater(point['minimumSignedArea'],0)
 def test_render_frames(self):
  self.assertEqual(len(self.render['methods']),5)
  self.assertEqual(len(self.flow['methods']),2)
  for q in (self.render,self.flow):
   for m,frames in q['methods'].items():
    self.assertEqual(len(frames),9)
    for key,rec in frames.items():
     file=R/rec['relativePath']
     self.assertEqual(sha(file),rec['sha256'])
     with Image.open(file) as im:
      self.assertEqual(im.size,(1024,1024))
      self.assertEqual(im.mode,'RGBA')
 def test_endpoint_pixel_exact(self):
  for q in (self.render,self.flow):
   for m,frames in q['methods'].items():
    for a,view in [('60','60'),('75','75')]:
     self.assertEqual(frames[a]['sha256'],self.parts['views'][view]['sourceSHA256'])
 def test_flow_metrics(self):
  self.assertGreater(self.flow['flowMagnitudeMeanPx'],0)
  self.assertEqual(len(self.flow['localFlowROI']),4)
  for q in (self.render,self.flow):
   for m,regions in q['metrics'].items():
    for r,s in regions.items():
     self.assertEqual(len(s['adjacentMAE']),8)
     self.assertTrue(all(math.isfinite(n) for n in s['adjacentMAE']))
 def test_animations(self):
  self.assertEqual(len(self.rev['animations']),8)
  for m,info in self.rev['animations'].items():
   self.assertEqual(sha(R/info['path']),info['sha256'])
 def test_html(self):
  h=(P/'p15-103-render/index.html').read_text()
  for x in ('id="method"','id="yaw"','id="current"','id="loop"'):
   self.assertIn(x,h)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),144)
  self.assertFalse(self.browser['errors'])
 def test_artistic_gate(self):
  self.assertFalse(self.mesh['artistApproved'])
  self.assertFalse(self.render['fullContinuityAccepted'])
  self.assertFalse(self.flow['visualAccepted'])
  self.assertFalse(self.rev['visualAccepted'])
if __name__=='__main__':unittest.main()
