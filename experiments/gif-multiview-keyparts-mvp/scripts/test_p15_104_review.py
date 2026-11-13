#!/usr/bin/env python3
"""Actual garment ink tie-point proof, shared mesh topology, rendering and browser QA."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import unittest,numpy as np,json,math
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
class P15104(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.features=json.loads((R/'evidence/p15-104-feature-qa.json').read_text())
  cls.m=json.loads((P/'p15-104-detail-mesh/garment-ink-correspondence.json').read_text())
  cls.mqa=json.loads((R/'evidence/p15-104-mesh-qa.json').read_text())
  cls.render=json.loads((R/'evidence/p15-104-render-qa.json').read_text())
  cls.review=json.loads((R/'evidence/p15-104-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-104-browser-qa.json').read_text())
  cls.parts=json.loads((R/'evidence/p15-103-parts-qa.json').read_text())
 def test_source_part_identity(self):
  self.assertEqual(self.m['characterId'],'p0_character_001')
  self.assertEqual(self.m['sourceAngles'],[60,75])
  self.assertTrue(self.parts['sourceReassemblyExact'])
 def test_feature_origin(self):
  self.assertEqual(self.features['schema'],'KOMA_P15_104_FEATURE_DISCOVERY_V1')
  self.assertEqual(self.features['method'],'independent source texture SIFT, mutual ratio test and RANSAC')
  self.assertEqual(self.mqa['sourceSIFTSHA256'],sha(R/'evidence/p15-104-feature-qa.json'))
 def test_filtered_crossview_correspondences(self):
  expected={'bow':6,'collar':3,'jewel':2,'shoulder.left':2}
  self.assertEqual(set(self.m['parts']),set(expected))
  for role,n in expected.items():
   self.assertEqual(self.mqa['roles'][role]['acceptedInteriorCorrespondences'],n)
   self.assertEqual(len(self.m['parts'][role]['matchedFeatures']),n)
 def test_triangle_count(self):
  self.assertEqual(sum(len(p['vertices']) for p in self.m['parts'].values()),49)
  self.assertEqual(sum(len(p['triangles']) for p in self.m['parts'].values()),58)
  self.assertEqual(self.mqa['meshSHA256'],sha(P/'p15-104-detail-mesh/garment-ink-correspondence.json'))
 def test_uv_range(self):
  for role,p in self.m['parts'].items():
   for v in p['vertices']:
    self.assertEqual(set(v['viewUV']),{'60','75'})
    for coords in v['viewUV'].values():
     self.assertTrue(all(0<=x<=1 for x in coords))
 def test_no_triangle_folds(self):
  self.assertFalse(self.mqa['sourceGeometryFolded'])
  for role,x in self.mqa['roles'].items():
   self.assertEqual(len(x['sampledGeometry']),9)
   for s in x['sampledGeometry']:
    self.assertGreater(s['minSignedArea'],0)
    self.assertEqual(s['folds'],0)
 def test_frame_integrity(self):
  self.assertEqual(len(self.render['methods']),3)
  for method,frames in self.render['methods'].items():
   self.assertEqual(len(frames),9)
   for a,r in frames.items():
    f=R/r['relativePath']
    self.assertEqual(r['sha256'],sha(f))
    with Image.open(f) as im:
     self.assertEqual(im.size,(1024,1024))
     self.assertEqual(im.mode,'RGBA')
 def test_keyframes_native(self):
  for method,frames in self.render['methods'].items():
   for a,v in [('60','60'),('75','75')]:
    self.assertEqual(frames[a]['sha256'],self.parts['views'][v]['sourceSHA256'])
 def test_edge_agreement(self):
  for role,d in self.render['inkAlignmentAt67p5'].items():
   a=d['grid']['edgeAgreementWithin2Px']
   b=d['detailed']['edgeAgreementWithin2Px']
   self.assertGreaterEqual(b,a)
   self.assertTrue(0<=a<=1 and 0<=b<=1)
  self.assertGreater(self.render['inkAlignmentAt67p5']['bow']['detailed']['edgeAgreementWithin2Px'],.69)
 def test_frame_differences(self):
  for m,regions in self.render['metrics'].items():
   for key,metric in regions.items():
    self.assertEqual(len(metric['adjacentMAE']),8)
    self.assertTrue(all(math.isfinite(n) and n>=0 for n in metric['adjacentMAE']))
 def test_review_gifs(self):
  self.assertEqual(len(self.review['animations']),5)
  for m,rec in self.review['animations'].items():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html(self):
  s=(P/'p15-104-detail-render/index.html').read_text()
  for key in ('id="method"','id="yaw"','id="current"','id="motion"'):
   self.assertIn(key,s)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),90)
  self.assertEqual(self.browser['errors'],[])
 def test_visual_gate(self):
  self.assertFalse(self.m['sourceVerifiedByArtist'])
  self.assertFalse(self.mqa['formalTopologyApproved'])
  self.assertFalse(self.render['continuousYawAccepted'])
  self.assertFalse(self.review['visualAccepted'])
if __name__=='__main__':unittest.main()
