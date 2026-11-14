#!/usr/bin/env python3
"""Native Codex garment keyart and three-view animation consistency checks."""
import unittest,json,hashlib,math
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Companions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=json.loads((R/'private-assets/p15-107-codex-patches/generation-summary.json').read_text())
  cls.a=json.loads((R/'evidence/p15-107-patch-qa.json').read_text())
  cls.r=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
  cls.v=json.loads((R/'evidence/p15-107-companion-review-qa.json').read_text())
  cls.b=json.loads((R/'evidence/p15-107-companion-browser-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
 def test_true_model_generation(self):
  self.assertEqual(len(self.raw['assets']),2)
  for asset in self.raw['assets']:
   self.assertTrue(asset['tool_image_gen_imagegen_actually_invoked'])
 def test_original_native_images_preserved(self):
  self.assertTrue(self.a['allDimensionsAndColorsValidated'])
  for view,rec in self.a['generatedCompanions'].items():
   self.assertEqual(rec['nativeSHA256'],sha(R/rec['nativePath']))
   self.assertEqual(rec['registeredSHA256'],sha(R/rec['registeredPath']))
 def test_rgba_and_native_dimensions(self):
  for view,rec in self.a['generatedCompanions'].items():
   with Image.open(R/rec['nativePath']) as im:
    self.assertEqual(im.mode,'RGBA')
    self.assertEqual(im.size,tuple(rec['nativeDimensions']))
    self.assertGreaterEqual(min(im.size),1000)
 def test_brooch_registration(self):
  for view,rec in self.a['generatedCompanions'].items():
   self.assertLess(max(abs(v) for v in rec['registrationOffset']),40)
   self.assertEqual(rec['opaqueAbove590'],0)
 def test_bow_garment_structural_pixels(self):
  for record in self.a['generatedCompanions'].values():
   self.assertGreater(record['bowHuePixels'],7000)
   self.assertGreater(record['goldHuePixels'],1000)
 def test_rendered_modes(self):
  self.assertEqual(len(self.r['methods']),5)
  self.assertEqual(len(self.r['angles']),9)
 def test_original_endpoint_integrity(self):
  for mode,frames in self.r['methods'].items():
   if not mode.endswith('orig_keys'):continue
   for angle,view in [('60','60'),('75','75')]:
    self.assertEqual(frames[angle]['sha256'],self.top['views'][view]['sourceSHA256'])
 def test_rendered_frames(self):
  for mode,frames in self.r['methods'].items():
   self.assertEqual(len(frames),9)
   for rec in frames.values():
    p=R/rec['relativePath'];self.assertEqual(rec['sha256'],sha(p))
    with Image.open(p) as im:
     self.assertEqual(im.mode,'RGBA')
     self.assertEqual(im.size,(1024,1024))
 def test_temporal_metrics(self):
  for mode,regions in self.r['metrics'].items():
   for name,metric in regions.items():
    self.assertEqual(len(metric['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) for x in metric['adjacentRGBMAE']))
 def test_native_collared_source_numeric_improvement(self):
  base=self.r['metrics']['P15-101-head_alpha_blend']['collar']['maxAdjacentRGBMAE']
  candidate=self.r['metrics']['companion_direct_native_keys']['collar']['maxAdjacentRGBMAE']
  self.assertLess(candidate,base)
 def test_gif_integrity(self):
  self.assertEqual(len(self.v['animations']),7)
  for item in self.v['animations'].values():
   self.assertEqual(item['sha256'],sha(R/item['path']))
 def test_review_html(self):
  self.assertEqual(len(self.v['methods']),7)
  txt=(P/'p15-107-companion-render/index.html').read_text()
  for key in ('id="method"','id="yaw"','id="frame"','id="loop"'):
   self.assertIn(key,txt)
 def test_browser(self):
  self.assertEqual(self.b['status'],'PASS')
  self.assertEqual(len(self.b['checks']),126)
  self.assertFalse(self.b['errors'])
 def test_artistic_gate(self):
  self.assertFalse(self.a['artisticApproved'])
  self.assertFalse(self.r['artisticAcceptance'])
  self.assertFalse(self.v['visualAccepted'])
if __name__=='__main__':unittest.main()
