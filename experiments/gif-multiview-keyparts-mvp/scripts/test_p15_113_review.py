#!/usr/bin/env python3
"""P15-113 canonical 3-view UV topology, source ink and browser regression QA."""
from pathlib import Path
from hashlib import sha256
from PIL import Image
import unittest,json,math
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
class Canonical(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.render=json.loads((R/'evidence/p15-113-render-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-113-topology-qa.json').read_text())
  cls.review=json.loads((R/'evidence/p15-113-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-113-browser-qa.json').read_text())
  cls.native=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
  cls.mesh=json.loads((P/'p15-106-three-key-mesh/garment-three-key-mesh.json').read_text())
  cls.p107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
 def test_character_source(self):
  self.assertEqual(self.render['characterId'],'p0_character_001')
  self.assertEqual(self.render['canonicalTextureAngle'],67.5)
  self.assertEqual(self.render['sourceAngles'],[60,67.5,75])
 def test_source_canonical_registered_identity(self):
  path=R/self.render['canonicalSourceRGBA']
  self.assertEqual(self.render['canonicalSourceSHA256'],sha(path))
  self.assertEqual(self.native['views']['67.5']['sourceSHA256'],sha(path))
 def test_shared_mesh_manifest(self):
  self.assertEqual(self.render['sourceMeshSHA256'],sha(P/'p15-106-three-key-mesh/garment-three-key-mesh.json'))
  self.assertEqual(self.top['meshSHA256'],self.render['sourceMeshSHA256'])
  self.assertEqual(self.render['sharedMeshPerPart'],{'vertices':33,'triangles':48,'sourceUVCount':1})
 def test_connected_same_index_mesh(self):
  for role in ('bow','collar','jewel'):
   z=self.top['roleTopology'][role]
   self.assertEqual(z['vertexCount'],33)
   self.assertEqual(z['triangleCount'],48)
   self.assertEqual(len(z['sharedVertexIds']),33)
   self.assertEqual(len(z['triangleIndices']),48)
   self.assertEqual(len(set(z['sharedVertexIds'])),33)
 def test_canonical_material_texture_bytes(self):
  for role,z in self.top['roleTopology'].items():
   self.assertEqual(z['sourceCanonicalRGBA_SHA256'],sha(R/z['sourceCanonicalRGBA']))
 def test_no_original_source_mutation(self):
  for view in ('60','67.5','75'):
   self.assertEqual(self.native['views'][view]['sourceSHA256'],sha(R/self.native['views'][view]['source']))
  self.assertTrue(self.render['nativeOriginalArtPreservedOnDisk'])
  self.assertTrue(self.render['pixelSourceNativeKeyframesAlteredInCandidates'])
 def test_nofold_three_source_views(self):
  for role,z in self.top['roleTopology'].items():
   self.assertTrue(z['nonfoldingAllViews'])
   for view,value in z['minSignedTriangleArea1024'].items():self.assertGreater(value,0)
 def test_nonfolding_target_renders(self):
  for mode,frames in self.render['methods'].items():
   for view,q in frames.items():
    for role,z in q['geometry']['triangleGeometry'].items():
     self.assertEqual(z['negativeTargetTriangles'],0)
     self.assertGreater(z['minimumTriangleOrientation'],0)
 def test_real_bow_target_shape(self):
  self.assertGreater(self.top['actualTargetMaskIoU']['bow']['60']['IoU'],.6)
  self.assertGreater(self.top['actualTargetMaskIoU']['bow']['75']['IoU'],.6)
 def test_target_mask_audit_is_source_grounded(self):
  for role,rows in self.top['actualTargetMaskIoU'].items():
   for view,data in rows.items():
    self.assertGreaterEqual(data['IoU'],0)
    self.assertLessEqual(data['IoU'],1)
    self.assertGreater(data['nativeObservedPixels'],100)
    self.assertGreater(data['predictedPixels'],100)
    self.assertGreater(data['union'],0)
 def test_source_measured_path_audit(self):
  r=self.top['pathCorrespondence']
  self.assertIn('bow.left_inner_fold',r)
  self.assertLess(r['bow.left_inner_fold']['views']['60']['meanObservedDriftPx'],6)
  self.assertLess(r['bow.left_inner_fold']['views']['75']['meanObservedDriftPx'],6)
 def test_source_uv_position_count(self):
  for role,q in self.top['roleTopology'].items():
   for view in ('60','67.5','75'):
    self.assertEqual(len(q['viewSourcePosition'][view]),33)
 def test_actual_rendering_frames(self):
  self.assertEqual(len(self.render['methods']),3)
  for mode,frames in self.render['methods'].items():
   self.assertEqual(len(frames),9)
   for angle,z in frames.items():
    self.assertEqual(z['sha256'],sha(R/z['path']))
    with Image.open(R/z['path']) as image:
     self.assertEqual(image.mode,'RGBA')
     self.assertEqual(image.size,(1024,1024))
 def test_source_bow_single_owner_is_documented(self):
  self.assertIn('one 67.5° bow/jewel source UV',self.render['sourceColorAndInkIdentity'])
  for mode,frames in self.render['methods'].items():
   for view,rec in frames.items():
    self.assertEqual(rec['geometry']['sourceOwnerCount'],1)
    self.assertEqual(rec['geometry']['canonicalBowTextureSHA256'],self.native['views']['67.5']['layers']['bowFabric']['textureSHA256'])
 def test_target_luma_metrics(self):
  self.assertEqual(len(self.render['metrics']),6)
  for mode,regions in self.render['metrics'].items():
   for name,rec in regions.items():
    self.assertEqual(len(rec['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) and x>=0 for x in rec['adjacentRGBMAE']))
 def test_review_source_files(self):
  self.assertEqual(len(self.review['methodFrames']),6)
  for mode,frames in self.review['methodFrames'].items():
   self.assertEqual(len(frames),9)
   for relative in frames.values():
    self.assertTrue((P/'p15-113-canonical-topology'/relative).resolve().is_file())
 def test_review_gifs(self):
  self.assertEqual(len(self.review['animations']),6)
  for item in self.review['animations'].values():
   self.assertEqual(item['sha256'],sha(R/item['path']))
 def test_html_controls(self):
  html=(P/'p15-113-canonical-topology/index.html').read_text()
  for key in ('id="method"','id="yaw"','id="frame"','id="loop"'):
   self.assertIn(key,html)
 def test_browser_viewport_cases(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),108)
  self.assertEqual(self.browser['errors'],[])
 def test_artist_visual_gate_is_independent(self):
  self.assertFalse(self.top['artistTopologyApproved'])
  self.assertFalse(self.render['full360YawVisualAccepted'])
  self.assertFalse(self.review['fullYawArtistApproved'])
if __name__=='__main__':unittest.main()
