#!/usr/bin/env python3
"""P15-110 actual model-vision path provenance, raster support and 3-key preview."""
from pathlib import Path
from hashlib import sha256
from PIL import Image
import unittest,json,numpy as np,math
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
class NativeVisionPaths(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=json.loads((R/'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json').read_text())
  cls.vision=json.loads((R/'evidence/p15-110-vision-qa.json').read_text())
  cls.render=json.loads((R/'evidence/p15-110-render-qa.json').read_text())
  cls.review=json.loads((R/'evidence/p15-110-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-110-browser-qa.json').read_text())
  cls.p107=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
 def test_character_provenance(self):
  self.assertEqual(self.vision['characterId'],'p0_character_001')
  self.assertEqual(self.vision['sourceAngles'],[60,67.5,75])
  self.assertEqual(self.vision['annotationSHA256'],sha(R/'private-assets/p15-110-vision-strokes/vision-stroke-annotations.json'))
 def test_original_source_files(self):
  for view,item in self.vision['sourceImages'].items():self.assertEqual(item['sha256'],sha(R/item['path']))
 def test_eight_semantic_roles(self):
  self.assertEqual(len(self.raw['roles']),8)
  self.assertEqual(set(self.raw['roles']),set(self.vision['roles']))
 def test_actual_model_vision_coordinates(self):
  self.assertEqual(self.raw['angles'],['60','67.5','75'])
  self.assertEqual(self.raw['coordinate_system'],'original 1024x1024 source canvas')
  for role,obj in self.raw['roles'].items():
   self.assertEqual(set(obj['views']),{'60','67.5','75'})
   for view,x in obj['views'].items():
    for p in x['points']:
     self.assertEqual(len(p),2)
     self.assertTrue(all(math.isfinite(n) and 0<=n<1024 for n in p))
 def test_source_path_four_qualified(self):
  self.assertEqual(self.vision['experimentAcceptedRoles'],[
   'bow.left_outer_outline','bow.right_outer_outline',
   'bow.left_inner_fold','bow.left_tail_fold'])
 def test_accepted_source_edge_support(self):
  for role in self.vision['experimentAcceptedRoles']:
   rec=self.vision['roles'][role]
   self.assertTrue(rec['crossViewAcceptedForExperiment'])
   for e in rec['sourceView'].values():
    self.assertTrue(e['passesViewGate'])
    self.assertGreaterEqual(e['edgeWithin9pxFraction'],.6)
 def test_nonqualified_paths_do_not_render(self):
  used=self.render['acceptedSourceStrokeRoles']
  self.assertEqual(used,self.vision['experimentAcceptedRoles'])
  for r in used:self.assertTrue(self.vision['roles'][r]['crossViewAcceptedForExperiment'])
 def test_render_source_qa_sha(self):
  self.assertEqual(self.render['visionEvidenceSHA256'],sha(R/'evidence/p15-110-vision-qa.json'))
 def test_18_generated_frames(self):
  self.assertEqual(len(self.render['methods']),2)
  for m,frames in self.render['methods'].items():
   self.assertEqual(len(frames),9)
   for rec in frames.values():
    p=R/rec['path']
    self.assertEqual(rec['sha256'],sha(p))
    with Image.open(p) as im:
     self.assertEqual(im.mode,'RGBA')
     self.assertEqual(im.size,(1024,1024))
 def test_keyframe_identity(self):
  for frames in self.render['methods'].values():
   for angle in ('60','67.5','75'):
    self.assertEqual(frames[angle]['sha256'],
     self.p107['methods']['companion_direct_native_keys'][angle]['sha256'])
 def test_animated_regional_metrics(self):
  self.assertEqual(len(self.render['metrics']),4)
  for zones in self.render['metrics'].values():
   for area,metric in zones.items():
    self.assertEqual(len(metric['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) and x>=0 for x in metric['adjacentRGBMAE']))
 def test_view_dependent_occlusion_is_explicit(self):
  self.assertTrue(self.render['occlusion']['actualHiddenUnderBroochPixelsNotObserved'])
  self.assertFalse(self.render['occlusion']['syntheticHiddenArtworkApproved'])
 def test_preview_has_four_methods(self):
  self.assertEqual(len(self.review['methodFrames']),4)
  for m,z in self.review['methodFrames'].items():self.assertEqual(len(z),9)
 def test_gif_provenance(self):
  self.assertEqual(len(self.review['animations']),4)
  for rec in self.review['animations'].values():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html_controls(self):
  html=(P/'p15-110-path-vdd/index.html').read_text()
  for name in ('id="method"','id="yaw"','id="frame"','id="motion"'):
   self.assertIn(name,html)
 def test_chromium_checks(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),72)
  self.assertEqual(self.browser['errors'],[])
 def test_independent_visual_approval(self):
  self.assertFalse(self.vision['artistStrokeIDsApproved'])
  self.assertFalse(self.render['naturalYawAccepted'])
  self.assertFalse(self.review['fullYawVisualAccepted'])
if __name__=='__main__':unittest.main()
