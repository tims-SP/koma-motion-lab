#!/usr/bin/env python3
"""Verify native imagegen/SAM3 provenance, source pixels and 39-frame 3-view motion."""
from pathlib import Path
from PIL import Image
import hashlib,json,unittest
R=Path(__file__).resolve().parents[1];P=R/'private-assets';E=P/'exports'
D=E/'p15-97-multiview-motion'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class P1597(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((R/'evidence/p15-97-multiview-motion-qa.json').read_text())
  cls.b=json.loads((R/'evidence/p15-97-browser-qa.json').read_text())
 def test_three_source_views(self):
  self.assertEqual(set(self.q['views']),{'52p5','60','75'})
 def test_native_art_reconstruction_provenance(self):
  for view in ('52p5','75'):
   d=P/('p15-97-underpaint-'+view)
   meta=json.loads((d/'generation-result.json').read_text())
   reg=json.loads((R/'evidence'/('p15-97-underpaint-yaw'+view+'.json')).read_text())
   self.assertTrue(meta['actual_image_tool_used'])
   self.assertEqual(meta['tool'],'image_gen.imagegen')
   self.assertEqual(meta['sha256'],sha(d/'model-native.png'))
   with Image.open(d/'model-native.png') as native:self.assertEqual(native.size,(1254,1254))
   self.assertEqual(reg['registeredSourceSHA256'],sha(d/'model-registered-source.png'))
 def test_sam3_annotated_masks(self):
  for view in ('52p5','75'):
   r=json.loads((R/'evidence'/('p15-97-sam3-yaw'+view+'.json')).read_text())
   self.assertEqual(r['status'],'MODEL_RETURNED')
   self.assertTrue(r['sourceRGBPreserved'])
   for entry in r['annotations']:
    p=E/('p15-97-sam3-yaw'+view)
    self.assertEqual(entry['maskSHA256'],sha(p/f"mask-{entry['index']}-1024.png"))
 def test_all_39_frames_hash(self):
  for view,q in self.q['views'].items():
   self.assertEqual(len(q['frames']),13)
   for offset in range(13):
    self.assertEqual(q['frames'][str(offset)]['sha256'],sha(D/f'yaw{view}-frame-{offset:02}.png'))
 def test_zero_pose_pixel_exact(self):
  for q in self.q['views'].values():
   self.assertEqual(q['sourceSHA256'],q['frames']['0']['sha256'])
   self.assertTrue(q['restPoseSourcePixelExact'])
 def test_fixed_root_and_owned_pixels(self):
  for q in self.q['views'].values():
   for frame in q['frames'].values():
    self.assertEqual(frame['rootChangedPixels'],0)
    self.assertEqual(frame['changedOutsideHairSupports'],0)
    self.assertEqual(frame['newHoles'],0)
 def test_visible_motion_all_views(self):
  for q in self.q['views'].values():self.assertGreater(q['frames']['12']['tipChangedPixels'],300)
 def test_60_degree_baseline_reuse(self):
  for dx in range(13):
   path=E/'p15-96-yaw060-root-artmesh'/f'frame-{dx:02}.png'
   self.assertEqual(sha(path),sha(D/f'yaw60-frame-{dx:02}.png'))
 def test_local_motion_temporal(self):
  for q in self.q['views'].values():
   self.assertLess(q['maxAdjacentRGBMAE'],.6)
   self.assertLess(q['firstStepRatio'],1.8)
 def test_synchronized_gif(self):
  self.assertEqual(self.q['animatedPreviewSHA256'],sha(D/'three-view-motion.gif'))
 def test_browser(self):
  self.assertEqual(self.b['status'],'PASS')
  self.assertEqual(len(self.b['checks']),78)
  self.assertFalse(self.b['errors'])
 def test_html(self):
  html=(D/'index.html').read_text()
  for name in ('id="angle"','id="offset"','id="candidate"','id="source"'):
   self.assertIn(name,html)
 def test_formal_gate(self):
  self.assertFalse(self.q['formalFullArtMeshAccepted'])
  self.assertFalse(self.q['continuousVddAccepted'])
if __name__=='__main__':unittest.main()
