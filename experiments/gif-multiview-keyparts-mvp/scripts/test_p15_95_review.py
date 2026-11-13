#!/usr/bin/env python3
"""Verify P0 original pixels, native generation provenance, bounded motion and QA files."""
import unittest,json,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1]
A=R/'private-assets';P=A/'exports'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Underpaint(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.model=json.loads((R/'evidence/p15-95-model-registration-qa.json').read_text())
  cls.dynamic=json.loads((R/'evidence/p15-95-underpaint-motion-qa.json').read_text())
  cls.elastic=json.loads((R/'evidence/p15-95-elastic-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-95-browser-qa.json').read_text())
  cls.inpaint=json.loads((R/'evidence/p15-95-inpaint-qa.json').read_text())
 def test_native_generation(self):
  meta=json.loads((A/'p15-95-underpaint/generation-result.json').read_text())
  self.assertTrue(meta['actual_image_tool_used'])
  self.assertEqual(meta['tool'],'image_gen.imagegen')
  self.assertEqual(meta['sha256'],sha(A/'p15-95-underpaint/face-underpaint-native.png'))
 def test_model_dimensions(self):
  with Image.open(A/'p15-95-underpaint/face-underpaint-native.png') as art:self.assertEqual(art.size,(1254,1254))
 def test_registration(self):
  self.assertEqual(self.model['registeredSHA256'],sha(A/'p15-95-underpaint/registered-translation.png'))
  self.assertLess(self.model['registeredOutsideMaskMAE'],7)
 def test_identity_inputs(self):
  self.assertEqual(self.model['sourceSHA256'],sha(P/'p15-92-angle-keyart/yaw060-registered.png'))
  self.assertEqual(self.model['sam3MaskSHA256'],sha(P/'p15-94-sam3-yaw060/hair-candidate-0-alpha1024.png'))
 def test_native_rest_identical(self):
  src=sha(P/'p15-92-angle-keyart/yaw060-registered.png')
  for tag in ('feather-2','feather-5','feather-10'):
   self.assertEqual(src,sha(P/f'p15-95-elastic-review/{tag}-00.png'))
 def test_alpha_holes(self):
  for info in self.elastic['modes'].values():
   for frame in info['frames'].values():self.assertEqual(frame['holes'],0)
 def test_model_motion_sha(self):
  for tag,info in self.dynamic['variants'].items():
   for dx,frame in info['frames'].items():
    self.assertEqual(frame['sha256'],sha(P/f'p15-95-yaw060-motion/{tag}-frame-{int(dx):02}.png'))
 def test_elastic_motion_sha(self):
  for tag,info in self.elastic['modes'].items():
   self.assertEqual(len(info['frames']),13)
   for dx,frame in info['frames'].items():
    self.assertEqual(frame['sha256'],sha(P/f'p15-95-elastic-review/{tag}-{int(dx):02}.png'))
 def test_elastic_stability(self):
  self.assertLess(self.elastic['modes']['feather-2']['firstStepRatio'],1.4)
 def test_motion_spatial_bounds(self):
  src=np.asarray(Image.open(P/'p15-92-angle-keyart/yaw060-registered.png').convert('RGBA'))
  for dx in (4,8,12):
   v=np.asarray(Image.open(P/f'p15-95-elastic-review/feather-2-{dx:02}.png').convert('RGBA'))
   vis=np.any(src!=v,axis=2)&((src[:,:,3]>128)|(v[:,:,3]>128))
   yy,xx=np.where(vis)
   self.assertGreater(len(xx),0)
   self.assertTrue(np.all((xx>=500)&(xx<840)&(yy>=270)&(yy<600)))
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),8)
  self.assertFalse(self.browser['errors'])
 def test_html(self):
  html=(P/'p15-95-elastic-review/index.html').read_text()
  self.assertIn('id="pose"',html)
  self.assertIn('id="elastic"',html)
 def test_visual_signoff(self):
  self.assertFalse(self.elastic['formalArtMeshAccepted'])
  self.assertFalse(self.dynamic['formalArtMeshAccepted'])
  self.assertFalse(self.model['formalArtMeshAccepted'])
if __name__=='__main__':unittest.main()
