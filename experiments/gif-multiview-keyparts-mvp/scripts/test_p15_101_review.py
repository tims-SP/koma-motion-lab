#!/usr/bin/env python3
"""Verify P0 head/hair mesh topology, native source pixels, actual render and browser QA."""
import unittest,json,hashlib,math
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class HeadHair(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mesh=json.loads((P/'p15-101-shared-head-mesh/head-hair-shared-mesh.json').read_text())
  cls.geo=json.loads((R/'evidence/p15-101-mesh-qa.json').read_text())
  cls.render=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
  cls.b=json.loads((R/'evidence/p15-101-browser-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
 def test_mesh_provenance(self):
  self.assertEqual(self.mesh['characterId'],'p0_character_001')
  self.assertEqual(self.mesh['schema'],'KOMA_P15_101_SOURCE_HEAD_HAIR_MESH_V1')
  self.assertEqual(self.render['meshSHA256'],sha(P/'p15-101-shared-head-mesh/head-hair-shared-mesh.json'))
 def test_semantic_vertex_count(self):
  self.assertEqual(self.geo['vertexCount'],59)
  self.assertEqual(self.mesh['headOuterVertexCount'],23)
  self.assertEqual(self.mesh['hairInteriorVertexCount'],14)
  self.assertEqual(self.mesh['faceVertexCount'],22)
 def test_shared_triangles(self):
  self.assertEqual(self.geo['triangleCount'],90)
  self.assertEqual(len(self.mesh['triangles']),90)
  self.assertEqual(len(self.mesh['omitted']),self.geo['omittedTriangleCount'])
  for tri in self.mesh['triangles']:
   self.assertEqual(len(set(tri)),3)
   self.assertTrue(all(0<=n<len(self.mesh['vertices']) for n in tri))
 def test_view_dependent_uvs(self):
  for node in self.mesh['vertices']:
   self.assertEqual(set(node['viewUV']),{'60','75'})
   for uv in node['viewUV'].values():
    self.assertTrue(all(0<=x<=1 for x in uv))
 def test_no_flips(self):
  self.assertTrue(self.geo['nonfolding'])
  self.assertEqual(self.render['headMeshFolds'],0)
  self.assertEqual(len(self.geo['sampledGeometry']),9)
  for p in self.geo['sampledGeometry']:
   self.assertEqual(p['negativeTriangleCount'],0)
   self.assertGreater(p['minimumSignedArea'],0)
 def test_frames_exist(self):
  self.assertEqual(len(self.render['methods']),6)
  self.assertEqual(len(self.render['angles']),9)
  for method,angles in self.render['methods'].items():
   self.assertEqual(len(angles),9)
   for point in angles.values():
    file=R/point['relativePath']
    self.assertEqual(sha(file),point['sha256'])
    with Image.open(file) as art:
     self.assertEqual(art.size,(1024,1024))
     self.assertEqual(art.mode,'RGBA')
 def test_endpoints_source_owned(self):
  for method,frames in self.render['methods'].items():
   for k,view in [('60','60'),('75','75')]:
    self.assertEqual(frames[k]['sha256'],self.top['views'][view]['sourceSHA256'])
 def test_head_uv_coverage(self):
  for frames in self.render['methods'].values():
   for item in frames.values():
    if item['diagnostics'].get('source'):continue
    self.assertGreater(item['diagnostics']['coverage60'],.99)
    self.assertGreater(item['diagnostics']['coverage75'],.99)
    self.assertLess(item['diagnostics']['meshCracks60'],500)
    self.assertLess(item['diagnostics']['meshCracks75'],500)
 def test_temporal_metrics(self):
  for name,metric in self.render['metrics'].items():
   self.assertEqual(len(metric['adjacentFaceRGBMAE']),8)
   self.assertTrue(all(math.isfinite(x) and x>=0 for x in metric['adjacentFaceRGBMAE']))
 def test_improvement_over_face_only(self):
  a=self.render['metrics']['head_alpha_blend']
  b=self.render['metrics']['p15-100-mesh_source_blend']
  self.assertLess(a['maxAdjacentMAE'],b['maxAdjacentMAE'])
  self.assertLess(a['midpointJumpMAE'],b['midpointJumpMAE'])
 def test_gif_sha(self):
  self.assertEqual(len(self.render['animations']),6)
  for method,info in self.render['animations'].items():
   self.assertEqual(info['sha256'],sha(R/info['relativePath']))
 def test_html_controls(self):
  html=(P/'p15-101-head-render/index.html').read_text()
  for x in ('id="method"','id="yaw"','id="frame"','id="motion"'):
   self.assertIn(x,html)
 def test_browser(self):
  self.assertEqual(self.b['status'],'PASS')
  self.assertEqual(len(self.b['checks']),108)
  self.assertFalse(self.b['errors'])
 def test_signoff_boundary(self):
  self.assertFalse(self.mesh['artistApproved'])
  self.assertFalse(self.render['headTexelTopologyArtistApproved'])
  self.assertFalse(self.render['continuousYawVisualAccepted'])
if __name__=='__main__':unittest.main()
