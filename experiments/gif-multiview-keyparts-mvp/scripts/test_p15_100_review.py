#!/usr/bin/env python3
"""Source identity, shared-mesh topology, view-dependent UVs, and image QA."""
import unittest,json,math,hashlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Mesh(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mesh=json.loads((P/'p15-100-shared-face-mesh/face-shared-mesh.json').read_text())
  cls.geo=json.loads((R/'evidence/p15-100-mesh-qa.json').read_text())
  cls.render=json.loads((R/'evidence/p15-100-render-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-100-browser-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
 def test_mesh_uuid(self):
  self.assertEqual(self.mesh['schema'],'KOMA_P15_100_FACE_CORRESPONDENCE_MESH_V1')
  self.assertEqual(self.mesh['characterId'],'p0_character_001')
 def test_source_landmarks(self):
  for v in self.mesh['vertices']:
   self.assertEqual(set(v['sourcePosition']),{'60','75'})
   self.assertEqual(len(v['canonicalUV']),2)
   for view,uv in v['viewUV'].items():
    self.assertTrue(all(0<=u<=1 for u in uv))
 def test_mesh_index_topology(self):
  self.assertEqual(len(self.mesh['vertices']),22)
  self.assertEqual(len(self.mesh['triangles']),28)
  self.assertEqual(len(self.mesh['excludedTriangles']),1)
  for tri in self.mesh['triangles']:
   self.assertEqual(len(set(tri)),3)
   self.assertTrue(all(0<=n<22 for n in tri))
 def test_shared_mesh_hash(self):
  self.assertEqual(self.render['meshSHA256'],sha(P/'p15-100-shared-face-mesh/face-shared-mesh.json'))
  self.assertEqual(self.geo['meshSHA256'],self.render['meshSHA256'])
 def test_positive_signed_areas(self):
  self.assertTrue(self.geo['meshTrianglesNonFolded'])
  self.assertEqual(len(self.geo['signedTriangleAreas']),9)
  for frame in self.geo['signedTriangleAreas']:
   self.assertGreater(frame['minSignedTriangleArea'],0)
   self.assertEqual(frame['foldedTriangleCount'],0)
  self.assertEqual(self.render['geometryFoldCount'],0)
 def test_surface_coverage(self):
  for frames in self.render['methods'].values():
   for x in frames.values():
    if x['geometry'].get('endpoint'):continue
    self.assertGreater(x['geometry']['maskCoverage'],.99)
 def test_source_integrity(self):
  for method,frames in self.render['methods'].items():
   for a,v in [('60','60'),('75','75')]:
    self.assertEqual(frames[a]['sha256'],self.top['views'][v]['sourceSHA256'])
 def test_all_frames_sha(self):
  self.assertEqual(len(self.render['methods']),4)
  for mode,frames in self.render['methods'].items():
   self.assertEqual(len(frames),9)
   for angle,item in frames.items():
    path=R/item['path']
    self.assertEqual(sha(path),item['sha256'])
    with Image.open(path) as img:
     self.assertEqual(img.size,(1024,1024))
     self.assertEqual(img.mode,'RGBA')
 def test_quantitative_comparison(self):
  for name,record in self.render['metrics'].items():
   self.assertEqual(len(record['adjacentFaceMAE']),8)
   self.assertTrue(all(math.isfinite(x) and x>=0 for x in record['adjacentFaceMAE']))
  self.assertLess(self.render['metrics']['mesh_source_blend']['midpointJumpMAE'],
     self.render['metrics']['p15-99-topology_staged']['midpointJumpMAE'])
 def test_animations(self):
  self.assertEqual(len(self.render['animations']),4)
  for method,item in self.render['animations'].items():
   self.assertEqual(sha(R/item['relativePath']),item['sha256'])
 def test_html(self):
  txt=(P/'p15-100-mesh-vdd/index.html').read_text()
  for s in ('id="method"','id="yaw"','id="current"','id="motion"'):
   self.assertIn(s,txt)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),72)
  self.assertFalse(self.browser['errors'])
 def test_review_boundary(self):
  self.assertFalse(self.mesh['artistApproved'])
  self.assertFalse(self.render['texelsArtistApproved'])
  self.assertFalse(self.render['continuousYawVisualAccepted'])
if __name__=='__main__':unittest.main()
