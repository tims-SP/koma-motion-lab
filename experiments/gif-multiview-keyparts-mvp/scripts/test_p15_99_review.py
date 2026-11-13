#!/usr/bin/env python3
"""Verify actual SAM3 eye annotations, source-pixel topology and multi-view VDD QA."""
from pathlib import Path
from PIL import Image
import hashlib,json,math,unittest
import numpy as np
R=Path(__file__).resolve().parents[1]
P=R/'private-assets/exports'
D=P/'p15-99-topology';V=P/'p15-99-vdd-review'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Topology(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mask=json.loads((R/'evidence/p15-99-eye-mask-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
  cls.vdd=json.loads((R/'evidence/p15-99-topology-vdd-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-99-browser-qa.json').read_text())
 def test_model_eye_masks(self):
  self.assertTrue(self.mask['actualExternalModelOutput'])
  self.assertEqual(self.mask['model'],'prithivMLmods/SAM3-Demo')
  self.assertEqual(len(self.mask['viewResults']['60']['candidates']),8)
  self.assertEqual(len(self.mask['viewResults']['75']['candidates']),3)
 def test_real_mask_hashes(self):
  for view,rec in self.mask['viewResults'].items():
   for item in rec['candidates']:
    p=D/f'yaw{view}'
    self.assertEqual(item['maskSHA256'],sha(p/f"sam3-eye-mask-{item['index']}.png"))
    self.assertEqual(item['rawSHA256'],sha(p/f"sam3-eye-annotation-{item['index']}.png"))
 def test_roles_and_z_order(self):
  roles=self.top['roles'];self.assertEqual(len(roles),7)
  self.assertEqual(self.top['occlusionOrder'],roles)
  self.assertEqual(roles[-1],'hair.clip')
  self.assertEqual(roles[-2],'hair.front')
  self.assertTrue(all(a in roles and b in roles and roles.index(a)<roles.index(b) for a,b in self.top['occlusionEdges']))
 def test_partition_exhaustive(self):
  for view,q in self.top['views'].items():
   count=sum(rec['sourcePixelCount'] for rec in q['roleMasks'].values())
   self.assertEqual(count,1024*1024)
 def test_original_unchanged(self):
  for view,q in self.top['views'].items():
   source=R/q['sourcePath']
   reconstructed=D/f'yaw{view}/reconstructed.png'
   self.assertEqual(q['sourceSHA256'],sha(source))
   with Image.open(source) as orig, Image.open(reconstructed) as rec:
    self.assertEqual(orig.convert('RGBA').tobytes(),rec.convert('RGBA').tobytes())
 def test_layer_pixel_ownership(self):
  for view,q in self.top['views'].items():
   source=np.asarray(Image.open(R/q['sourcePath']).convert('RGBA'))
   assigned=np.zeros(source.shape[:2],dtype=np.uint8)
   for role,meta in q['roleMasks'].items():
    name=role.replace('.','_')
    mask=np.asarray(Image.open(D/f'yaw{view}/{name}-ownership.png').convert('L'))>128
    layer=np.asarray(Image.open(D/f'yaw{view}/{name}.png').convert('RGBA'))
    self.assertEqual(meta['sourceOwnedLayerSHA256'],sha(D/f'yaw{view}/{name}.png'))
    self.assertEqual(int(mask.sum()),meta['sourcePixelCount'])
    self.assertTrue(np.array_equal(layer[mask],source[mask]))
    assigned+=mask.astype(np.uint8)
   self.assertTrue(np.all(assigned==1))
 def test_far_eye_visibility(self):
  self.assertGreater(self.top['views']['60']['roleMasks']['eye.far']['opaquePixels'],500)
  self.assertEqual(self.top['views']['75']['roleMasks']['eye.far']['opaquePixels'],0)
 def test_gold_clip(self):
  for view,q in self.top['views'].items():
   self.assertGreater(q['roleMasks']['hair.clip']['sourcePixelCount'],500)
 def test_underpaint_provenance(self):
  for view,q in self.top['views'].items():
   self.assertTrue((R/q['modelUnderpaint']).is_file())
 def test_36_frames_hash(self):
  self.assertEqual(len(self.vdd['methods']),4)
  for method,results in self.vdd['methods'].items():
   self.assertEqual(len(results),9)
   for a,rec in results.items():
    file=R/rec['file']
    self.assertEqual(sha(file),rec['sha256'])
    with Image.open(file) as im:
     self.assertEqual(im.mode,'RGBA')
     self.assertEqual(im.size,(1024,1024))
 def test_endpoints_source_exact(self):
  for m,frames in self.vdd['methods'].items():
   for a,view in [('60','60'),('75','75')]:
    self.assertEqual(frames[a]['sha256'],self.vdd['sourceSHA256'][view])
 def test_motion_metrics(self):
  for name,rec in self.vdd['metrics'].items():
   self.assertEqual(len(rec['adjacentFaceMAE']),8)
   self.assertTrue(all(math.isfinite(n) and n>0 for n in rec['adjacentFaceMAE']))
 def test_animations(self):
  self.assertEqual(len(self.vdd['animations']),4)
  for m,rec in self.vdd['animations'].items():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html(self):
  html=(V/'index.html').read_text()
  for term in ('id="method"','id="yaw"','id="current"','id="animated"'):
   self.assertIn(term,html)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),72)
  self.assertFalse(self.browser['errors'])
 def test_approval_gate(self):
  self.assertFalse(self.top['semanticsArtistApproved'])
  self.assertFalse(self.vdd['continuousYawAccepted'])
  self.assertFalse(self.vdd['artistApproved'])
if __name__=='__main__':unittest.main()
