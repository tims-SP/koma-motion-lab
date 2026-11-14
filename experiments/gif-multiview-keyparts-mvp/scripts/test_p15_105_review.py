#!/usr/bin/env python3
"""P0 original native 67.5 keyart source integrity, registration, VDD frames, browser."""
import unittest,hashlib,json,math
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class P15105(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.native=json.loads((R/'evidence/p15-105-native-art-qa.json').read_text())
  cls.model=json.loads((R/'private-assets/p15-105-yaw0675/generation-result.json').read_text())
  cls.render=json.loads((R/'evidence/p15-105-render-qa.json').read_text())
  cls.review=json.loads((R/'evidence/p15-105-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-105-browser-qa.json').read_text())
  cls.head=json.loads((R/'evidence/p15-101-render-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
 def test_actual_codex_imagegen_used(self):
  self.assertEqual(self.model['actual_image_tool_used'],'image_gen.imagegen')
  self.assertEqual(self.native['model'],'Codex built-in image_gen.imagegen')
 def test_native_sha_unmodified(self):
  p=R/self.native['nativePath']
  self.assertEqual(self.native['nativeSHA256'],sha(p))
  self.assertEqual(self.model['sha256'],sha(p))
 def test_native_rgba_dimensions(self):
  with Image.open(R/self.native['nativePath']) as im:
   self.assertEqual(im.mode,'RGBA')
   self.assertEqual(im.size,(1254,1254))
  self.assertEqual(self.native['nativeDimensions'],[1254,1254])
 def test_model_has_single_bow_brooch(self):
  self.assertTrue(self.model['visual_review']['single_bow_and_brooch'])
  self.assertTrue(self.model['visual_review']['head_hair_absent'])
  self.assertGreater(self.native['bowHuePixels'],20000)
 def test_registered_source(self):
  with Image.open(R/self.native['registeredPath']) as im:
   self.assertEqual(im.size,(1024,1024))
  self.assertEqual(self.native['registeredSHA256'],sha(R/self.native['registeredPath']))
  self.assertEqual(self.native['opaqueAboveFaceROI'],0)
  self.assertGreater(self.native['registeredOpaquePixels'],160000)
 def test_brooch_registration(self):
  source=self.native['nativeGoldMeasuredCanvas1024']
  shift=self.native['translation1024']
  target=self.native['sourceTargetGoldCenter']
  self.assertAlmostEqual(source[0]+shift[0],target[0],delta=.03)
  self.assertAlmostEqual(source[1]+shift[1],target[1],delta=.03)
  self.assertLess(max(map(abs,shift)),40)
 def test_new_keyframe_is_actual_middle_source(self):
  q=self.render['nativeMidKeyframe']
  self.assertGreater(q['clothingOpaquePixelsBelow770'],130000)
  self.assertEqual(q['clothingSourceMAE'],0.0)
  self.assertEqual(q['clothingSourceExactFraction'],1.0)
 def test_registered_art_endpoints(self):
  for method,frames in self.render['methods'].items():
   for a,v in [('60','60'),('75','75')]:
    self.assertEqual(frames[a]['sha256'],self.top['views'][v]['sourceSHA256'])
 def test_three_keyframes_declared(self):
  self.assertEqual(self.render['sourceAngles'],[60,67.5,75])
  self.assertTrue(self.render['sourceGenuineMidpoint'])
  self.assertEqual(self.render['registeredKeyartSha256'],self.native['registeredSHA256'])
 def test_27_generated_rgba(self):
  self.assertEqual(len(self.render['methods']),3)
  for mode,frames in self.render['methods'].items():
   self.assertEqual(len(frames),9)
   for key,rec in frames.items():
    f=R/rec['relativePath']
    self.assertEqual(sha(f),rec['sha256'])
    with Image.open(f) as im:
     self.assertEqual(im.mode,'RGBA')
     self.assertEqual(im.size,(1024,1024))
 def test_regional_motion_metrics(self):
  self.assertEqual(len(self.render['metrics']),4)
  for method,regions in self.render['metrics'].items():
   for area,rec in regions.items():
    self.assertEqual(len(rec['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) and x>=0 for x in rec['adjacentRGBMAE']))
 def test_flow_provenance(self):
  for k,rec in self.render['flowMagnitude'].items():
   self.assertGreater(rec['meanPx'],0)
   self.assertGreaterEqual(rec['maxPx'],rec['meanPx'])
 def test_review_has_all_frames(self):
  self.assertEqual(len(self.review['frameFiles']),4)
  for method,record in self.review['frameFiles'].items():
   self.assertEqual(len(record),9)
   for p in record.values():
    self.assertTrue((P/'p15-105-three-key-vdd'/p).resolve().is_file())
 def test_gif_provenance(self):
  self.assertEqual(len(self.review['animations']),4)
  for record in self.review['animations'].values():
   self.assertEqual(record['sha256'],sha(R/record['path']))
 def test_html(self):
  txt=(P/'p15-105-three-key-vdd/index.html').read_text()
  for marker in ('id="method"','id="yaw"','id="current"','id="motion"'):
   self.assertIn(marker,txt)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),72)
  self.assertEqual(self.browser['errors'],[])
 def test_visual_signoff(self):
  self.assertFalse(self.native['angleGeometricallyVerified'])
  self.assertFalse(self.render['nativeMidpointGeometryAccepted'])
  self.assertFalse(self.render['continuousVisualAccepted'])
  self.assertFalse(self.review['modelMiddleArtAccepted'])
if __name__=='__main__':unittest.main()
