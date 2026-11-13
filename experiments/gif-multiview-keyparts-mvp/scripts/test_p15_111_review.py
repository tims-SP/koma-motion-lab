#!/usr/bin/env python3
"""P0 six native imagegen hidden artworks, alpha masks, layer provenance and browser."""
from pathlib import Path
from hashlib import sha256
from PIL import Image
import unittest,json,math,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
class HiddenGarment(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.art=json.loads((R/'private-assets/p15-111-hidden-art/generation-summary.json').read_text())
  cls.src=json.loads((R/'evidence/p15-111-source-qa.json').read_text())
  cls.r=json.loads((R/'evidence/p15-111-render-qa.json').read_text())
  cls.rev=json.loads((R/'evidence/p15-111-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-111-browser-qa.json').read_text())
  cls.old=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
  cls.owner=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
 def test_codex_builtin_image_generation(self):
  self.assertEqual(self.art['successfulImagegenCalls'],6)
  self.assertIn('image_gen.imagegen',self.art['toolsActuallyUsed'])
  self.assertEqual(len(self.art['outputs']),6)
 def test_six_native_rgba_and_sha(self):
  for item in self.art['outputs']:
   f=R/item['path']
   self.assertEqual(item['sha256'],sha(f))
   self.assertTrue(item['byteIdenticalToNative'])
   with Image.open(f) as im:
    self.assertEqual(im.mode,'RGBA')
    self.assertEqual(im.size,(1254,1254))
 def test_art_reproducible_sources(self):
  self.assertEqual(self.src['sourceAngles'],[60,67.5,75])
  self.assertFalse(self.src['hiddenMaterialIsObservedGroundTruth'])
 def test_exact_registered_sources(self):
  for view,parts in self.src['layers'].items():
   for role,item in parts.items():
    self.assertEqual(sha(R/item['nativePath']),item['nativeSHA256'])
    self.assertEqual(sha(R/item['registeredPath']),item['registeredSHA256'])
    self.assertEqual(sha(R/item['hiddenOnlyPath']),item['hiddenOnlySHA256'])
 def test_registered_dimensions_and_alpha(self):
  for view,parts in self.src['layers'].items():
   for role,item in parts.items():
    with Image.open(R/item['registeredPath']) as im:
     self.assertEqual(im.size,(1024,1024))
     self.assertEqual(im.mode,'RGBA')
     a=np.asarray(im)[:,:,3]
     self.assertEqual(int((a[:590,:]>0).sum()),0)
 def test_registration_offsets(self):
  for parts in self.src['layers'].values():
   for item in parts.values():
    self.assertLess(max(abs(x) for x in item['registrationShift1024']),95)
 def test_hidden_only_matches_occlusion_target(self):
  for view,parts in self.src['layers'].items():
   qa=self.src['sourceMasks'][view]
   for role,item in parts.items():
    opaque=np.asarray(Image.open(R/item['hiddenOnlyPath']).convert('RGBA'))[:,:,3]>0
    ownerName='jewel' if role=='bow' else 'bowFabric'
    sourceMask=np.asarray(Image.open(R/self.owner['views'][view]['layers'][ownerName]['maskPath']).convert('L'))>128
    self.assertFalse(np.any(opaque&~sourceMask))
 def test_hidden_region_coverage(self):
  for view,parts in self.src['layers'].items():
   for role,item in parts.items():
    self.assertGreater(item['hiddenTargetPixels'],50)
    self.assertGreater(item['hiddenCoveragePixels'],50)
    threshold=.5 if role=='collar' else .8
    self.assertGreaterEqual(item['hiddenCoverageFraction'],threshold)
 def test_separate_layer_files(self):
  self.assertEqual(sum(len(x) for x in self.src['layers'].values()),6)
  self.assertEqual(len(self.r['drawingOrder']),8)
 def test_three_rendered_strategies(self):
  self.assertEqual(len(self.r['methods']),3)
  self.assertEqual(len(self.r['renderAngles']),9)
 def test_original_keyframes_remain_exact(self):
  for rows in self.r['methods'].values():
   for angle in ('60','67.5','75'):
    self.assertEqual(rows[angle]['sha256'],
     self.old['methods']['companion_direct_native_keys'][angle]['sha256'])
 def test_actual_27_frames(self):
  for rows in self.r['methods'].values():
   self.assertEqual(len(rows),9)
   for rec in rows.values():
    file=R/rec['path']
    self.assertEqual(sha(file),rec['sha256'])
    with Image.open(file) as im:
     self.assertEqual(im.mode,'RGBA')
     self.assertEqual(im.size,(1024,1024))
 def test_measured_roi(self):
  self.assertEqual(len(self.r['metrics']),5)
  for method,parts in self.r['metrics'].items():
   for roi,metric in parts.items():
    self.assertEqual(len(metric['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) and x>=0 for x in metric['adjacentRGBMAE']))
 def test_browser_method_frames(self):
  self.assertEqual(len(self.rev['methodFrames']),5)
  for method,frames in self.rev['methodFrames'].items():
   self.assertEqual(len(frames),9)
   for f in frames.values():
    self.assertTrue((P/'p15-111-layered-render'/f).resolve().is_file())
 def test_gifs(self):
  self.assertEqual(len(self.rev['animations']),5)
  for rec in self.rev['animations'].values():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html(self):
  html=(P/'p15-111-layered-render/index.html').read_text()
  for key in ('id="method"','id="yaw"','id="frame"','id="motion"'):
   self.assertIn(key,html)
 def test_chromium(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),90)
  self.assertEqual(self.browser['errors'],[])
 def test_visual_acceptance_is_separate(self):
  self.assertFalse(self.r['visualApproved'])
  self.assertFalse(self.rev['fullYawVisualAccepted'])
  self.assertFalse(self.src['hiddenMaterialIsObservedGroundTruth'])
if __name__=='__main__':unittest.main()
