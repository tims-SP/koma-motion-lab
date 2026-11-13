#!/usr/bin/env python3
"""Source-owned P0 collar, 3-view seam registration, nine-frame preview QA."""
from pathlib import Path
from hashlib import sha256
from PIL import Image
import unittest,json,math
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
class CollarRegistration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=json.loads((R/'evidence/p15-114-source-qa.json').read_text())
  cls.render=json.loads((R/'evidence/p15-114-render-qa.json').read_text())
  cls.review=json.loads((R/'evidence/p15-114-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-114-browser-qa.json').read_text())
  cls.native=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
  cls.previous=json.loads((R/'evidence/p15-113-topology-qa.json').read_text())
 def test_p0_registered_views(self):
  self.assertEqual(self.source['characterId'],'p0_character_001')
  self.assertEqual(self.source['sourceAngles'],[60,67.5,75])
 def test_one_source_color_and_ink(self):
  self.assertEqual(self.source['canonicalAngle'],67.5)
  self.assertEqual(self.source['canonicalSourceSHA256'],sha(R/self.source['canonicalRGBA']))
  self.assertEqual(self.render['singleSourceCollarAngle'],67.5)
 def test_art_is_original_preserved(self):
  self.assertTrue(self.source['originalSourcePreserved'])
  self.assertTrue(self.render['nativeOriginalSourceRGBAUnchanged'])
  for v,rec in self.source['views'].items():
   self.assertEqual(rec['sourceTargetSHA256'],sha(R/rec['sourceTarget']))
 def test_three_view_affine_determinant(self):
  for view,rec in self.source['views'].items():
   self.assertGreater(rec['determinant'],.75)
   self.assertLess(rec['determinant'],1.3)
 def test_60_shape_fidelity(self):
  self.assertGreater(self.source['views']['60']['mappedNativeTargetIoU'],.85)
 def test_75_shape_fidelity(self):
  self.assertGreater(self.source['views']['75']['mappedNativeTargetIoU'],.82)
 def test_better_than_mesh_collar(self):
  for v in ('60','75'):
   iou=self.source['views'][v]['mappedNativeTargetIoU']
   baseline=self.previous['actualTargetMaskIoU']['collar'][v]['IoU']
   self.assertGreater(iou,baseline+.35)
 def test_source_mid_100_percent_mask(self):
  self.assertAlmostEqual(self.source['views']['67.5']['mappedNativeTargetIoU'],1)
 def test_actual_fold_correspondence(self):
  for v in ('60','75'):
   for role,rec in self.source['views'][v]['nativeObservedSeamDrift'].items():
    self.assertLess(rec['meanSourceLineDriftPx'],5)
    self.assertLess(rec['maxSourceLineDriftPx'],9)
 def test_transparent_png_identity(self):
  for v,rec in self.source['views'].items():
   for fileKey,shaKey in (('canonicalCollarPath','canonicalCollarSHA256'),
                            ('nativeSilhouetteCollarPath','nativeSilhouetteSHA256')):
    p=R/rec[fileKey]
    self.assertEqual(sha(p),rec[shaKey])
    with Image.open(p) as img:
     self.assertEqual(img.size,(1024,1024))
     self.assertEqual(img.mode,'RGBA')
 def test_native_silhouette_is_clipped(self):
  for view,rec in self.source['views'].items():
   with Image.open(R/rec['canonicalCollarPath']) as art, Image.open(R/rec['nativeSilhouetteCollarPath']) as strict:
    import numpy as np
    a=np.asarray(art)[:,:,3];b=np.asarray(strict)[:,:,3]
    self.assertTrue((b<=a).all())
 def test_two_rendering_strategies(self):
  self.assertEqual(len(self.render['methods']),2)
  self.assertEqual(len(self.render['renderedAngles']),9)
 def test_actual_full_frame_rendering(self):
  for frames in self.render['methods'].values():
   self.assertEqual(len(frames),9)
   for rec in frames.values():
    self.assertEqual(rec['sha256'],sha(R/rec['path']))
    with Image.open(R/rec['path']) as im:
     self.assertEqual(im.size,(1024,1024))
     self.assertEqual(im.mode,'RGBA')
 def test_source_provenance_in_each_frame(self):
  self.assertEqual(self.render['sourceRegistrationSHA256'],sha(R/'evidence/p15-114-source-qa.json'))
  for rows in self.render['methods'].values():
   for rec in rows.values():
    self.assertEqual(rec['diagnostics']['canonicalTextureSHA256'],self.source['canonicalSourceSHA256'])
 def test_real_timing_metrics(self):
  self.assertEqual(len(self.render['metrics']),5)
  for m,parts in self.render['metrics'].items():
   for p,metric in parts.items():
    self.assertEqual(len(metric['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) and x>=0 for x in metric['adjacentRGBMAE']))
 def test_review_models_and_gifs(self):
  self.assertEqual(len(self.review['methodFrames']),5)
  self.assertEqual(len(self.review['animations']),5)
  for rec in self.review['animations'].values():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html_controls(self):
  html=(P/'p15-114-collar-render/index.html').read_text()
  for x in ('id="method"','id="yaw"','id="frame"','id="loop"'):
   self.assertIn(x,html)
 def test_chromium_viewports(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),90)
  self.assertEqual(self.browser['errors'],[])
 def test_artistic_gate_is_independent(self):
  self.assertFalse(self.render['fullVisualApproved'])
  self.assertFalse(self.review['artistVisualApproved'])
if __name__=='__main__':unittest.main()
