#!/usr/bin/env python3
"""Verify 60°-75° neck geometry, authentic eye/emblem data, render and browser evidence."""
import json,math,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class P15102(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mesh=json.loads((P/'p15-102-neck-shoulder-mesh/neck-shoulder-mesh.json').read_text())
  cls.mqa=json.loads((R/'evidence/p15-102-neck-mesh-qa.json').read_text())
  cls.render=json.loads((R/'evidence/p15-102-render-qa.json').read_text())
  cls.jewel=json.loads((R/'evidence/p15-102-jewel-qa.json').read_text())
  cls.review=json.loads((R/'evidence/p15-102-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-102-browser-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
 def test_neck_mesh_source_roles(self):
  self.assertEqual(self.mesh['schema'],'KOMA_P15_102_NECK_SHOULDER_MESH_V1')
  self.assertEqual(self.mesh['characterId'],'p0_character_001')
  self.assertEqual(len(self.mesh['vertices']),28)
  self.assertEqual(len(self.mesh['triangles']),36)
 def test_uv_provenance(self):
  for node in self.mesh['vertices']:
   self.assertEqual(set(node['viewUV']),{'60','75'})
   for v,uv in node['viewUV'].items():
    self.assertTrue(all(0<=u<=1 for u in uv))
  self.assertEqual(self.mqa['meshSHA256'],sha(P/'p15-102-neck-shoulder-mesh/neck-shoulder-mesh.json'))
 def test_nonfolded_triangles(self):
  self.assertTrue(self.mqa['nonfolding'])
  self.assertEqual(len(self.mqa['sampleAngles']),9)
  for rec in self.mqa['sampleAngles']:
   self.assertEqual(rec['foldCount'],0)
   self.assertGreater(rec['minimumArea'],0)
 def test_head_connection(self):
  self.assertTrue(self.mqa['headMeshLinked'])
  headqa=json.loads((R/'evidence/p15-101-mesh-qa.json').read_text())
  self.assertEqual(self.render['headMeshSHA256'],headqa['meshSha256'])
  self.assertEqual(self.render['bodyMeshSHA256'],self.mqa['meshSHA256'])
 def test_genuine_eye_model_provenance(self):
  q=json.loads((R/'evidence/p15-99-eye-mask-qa.json').read_text())
  self.assertTrue(q['actualExternalModelOutput'])
  self.assertEqual(set(self.render['eyeMasks']),{'60','75'})
  self.assertTrue(all(x>100 for x in self.render['eyeMasks'].values()))
 def test_genuine_emblem_center(self):
  for view,expected in [('60',(635,811)),('75',(645,808))]:
   record=self.jewel['sourceRealEmblemLandmarks'][view]
   self.assertLess(abs(record['centerMeasured'][0]-expected[0]),5)
   self.assertLess(abs(record['centerMeasured'][1]-expected[1]),5)
   self.assertGreater(record['sourceBlobArea'],200)
 def test_endpoints_exact(self):
  for collection in [self.render['methods'],self.jewel['methods']]:
   for method,frames in collection.items():
    for a,view in [('60','60'),('75','75')]:
     self.assertEqual(frames[a]['sha256'],self.top['views'][view]['sourceSHA256'])
 def test_frames(self):
  for collection in [self.render['methods'],self.jewel['methods']]:
   for frames in collection.values():
    self.assertEqual(len(frames),9)
    for rec in frames.values():
     p=R/rec['relativePath']
     self.assertEqual(rec['sha256'],sha(p))
     with Image.open(p) as image:self.assertEqual((image.size,image.mode),((1024,1024),'RGBA'))
 def test_metric_dimensions(self):
  for collection in [self.render,self.jewel]:
   for method,rois in collection['metrics'].items():
    for region in rois.values():
     self.assertEqual(len(region['adjacentRGBMAE']),8)
     self.assertTrue(all(math.isfinite(x) for x in region['adjacentRGBMAE']))
 def test_review_assets(self):
  self.assertEqual(len(self.review['methods']),8)
  self.assertEqual(len(self.review['angles']),9)
  for method,frames in self.review['methods'].items():
   self.assertEqual(len(frames),9)
   for ref in frames.values():self.assertTrue((P/'p15-102-neck-eye-profile'/ref).resolve().is_file())
 def test_gif_integrity(self):
  self.assertEqual(len(self.review['animations']),8)
  for record in self.review['animations'].values():
   self.assertEqual(record['sha256'],sha(R/record['path']))
 def test_html_controls(self):
  text=(P/'p15-102-neck-eye-profile/index.html').read_text()
  for item in ('id="method"','id="yaw"','id="frame"','id="motion"'):
   self.assertIn(item,text)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),144)
  self.assertFalse(self.browser['errors'])
 def test_visual_gate(self):
  self.assertFalse(self.mqa['artistApproved'])
  self.assertFalse(self.render['fullVisualAccepted'])
  self.assertFalse(self.jewel['visualAcceptance'])
  self.assertFalse(self.review['continuousVisualAccepted'])
if __name__=='__main__':unittest.main()
