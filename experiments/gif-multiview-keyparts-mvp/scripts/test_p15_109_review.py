#!/usr/bin/env python3
"""Measured ink-path support, provenance, local render and browser QA."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import unittest,numpy as np,json,math
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
class NativeStroke(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.path=json.loads((R/'evidence/p15-109-path-qa.json').read_text())
  cls.render=json.loads((R/'evidence/p15-109-render-qa.json').read_text())
  cls.review=json.loads((R/'evidence/p15-109-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-109-browser-qa.json').read_text())
  cls.base=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
  cls.stroke=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
 def test_character(self):
  self.assertEqual(self.path['characterId'],'p0_character_001')
 def test_genuine_three_view_sources(self):
  self.assertEqual(self.path['sourceAngles'],[60,67.5,75])
  for view,source in self.path['views'].items():
   self.assertEqual(source['sourceSHA256'],sha(R/source['source']))
   self.assertEqual(source['sourceSHA256'],self.stroke['views'][view]['sourceSHA256'])
 def test_six_candidates(self):
  self.assertEqual(len(self.path['candidateStrokeRoles']),6)
  self.assertEqual(len(self.path['crossViewRoles']),6)
 def test_strict_qualification(self):
  approved=[k for k,v in self.path['crossViewRoles'].items() if v['usableForMorph']]
  self.assertEqual(approved,['collar.left_crease'])
  self.assertFalse(self.path['artistVerified'])
 def test_measured_points(self):
  for v in ('60','67.5','75'):
   r=self.path['views'][v]['roles']['collar.left_crease']
   self.assertEqual(len(r['sourceXY']),24)
   self.assertGreater(r['polylineArcLength'],12)
 def test_path_source_bounds(self):
  for view,info in self.path['views'].items():
   for role,e in info['roles'].items():
    if e['supported']:
     self.assertTrue(all(0<=p[0]<1024 and 0<=p[1]<1024 for p in e['sourceXY']))
 def test_identity_length_and_drift(self):
  e=self.path['crossViewRoles']['collar.left_crease']
  self.assertLessEqual(e['lengthRatio'],2.5)
  self.assertLessEqual(max(e['meanPathDisplacementPx']),38)
 def test_render_source_binding(self):
  self.assertEqual(self.render['sourcePathsSHA256'],sha(R/'evidence/p15-109-path-qa.json'))
  self.assertEqual(self.render['matchedStrokeID'],'collar.left_crease')
 def test_rendered_frames(self):
  self.assertEqual(len(self.render['methods']),2)
  for method,frames in self.render['methods'].items():
   self.assertEqual(len(frames),9)
   for rec in frames.values():
    file=R/rec['path']
    self.assertEqual(rec['sha256'],sha(file))
    with Image.open(file) as im:
     self.assertEqual(im.mode,'RGBA')
     self.assertEqual(im.size,(1024,1024))
 def test_keyviews_exact(self):
  for method,frames in self.render['methods'].items():
   for v in ('60','67.5','75'):
    self.assertEqual(frames[v]['sha256'],self.base['methods']['companion_direct_native_keys'][v]['sha256'])
 def test_local_paint_bounds(self):
  for method,frames in self.render['methods'].items():
   for view,rec in frames.items():
    if view not in ('60','67.5','75'):
     self.assertLess(rec['diagnostics']['changedMaskPixels'],28000)
     self.assertGreater(rec['diagnostics']['changedMaskPixels'],20)
 def test_metrics_complete(self):
  self.assertEqual(len(self.render['metrics']),4)
  for m,regions in self.render['metrics'].items():
   for name,rec in regions.items():
    self.assertEqual(len(rec['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(v) and v>=0 for v in rec['adjacentRGBMAE']))
 def test_artistic_gate(self):
  self.assertFalse(self.render['formalArtistApproved'])
  self.assertFalse(self.review['continuousVisualAccepted'])
 def test_review(self):
  self.assertEqual(len(self.review['methods']),4)
  for m,frames in self.review['methods'].items():
   self.assertEqual(len(frames),9)
 def test_gifs(self):
  self.assertEqual(len(self.review['animations']),4)
  for rec in self.review['animations'].values():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html(self):
  content=(P/'p15-109-collar-render/index.html').read_text()
  for mark in ('id="method"','id="yaw"','id="frame"','id="loop"'):
   self.assertIn(mark,content)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),72)
  self.assertEqual(self.browser['errors'],[])
if __name__=='__main__':unittest.main()
