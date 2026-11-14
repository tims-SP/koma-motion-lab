#!/usr/bin/env python3
"""P15-108 native source layer partition, role ink, viewport, frame provenance."""
import unittest,json,hashlib,math
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P15108(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.a=json.loads((R/'evidence/p15-108-source-qa.json').read_text())
  cls.b=json.loads((R/'evidence/p15-108-stroke-qa.json').read_text())
  cls.c=json.loads((R/'evidence/p15-108-render-qa.json').read_text())
  cls.v=json.loads((R/'evidence/p15-108-review-qa.json').read_text())
  cls.browser=json.loads((R/'evidence/p15-108-browser-qa.json').read_text())
  cls.old=json.loads((R/'evidence/p15-107-companion-qa.json').read_text())
  cls.top=json.loads((R/'evidence/p15-99-topology-qa.json').read_text())
 def test_three_real_sources(self):
  self.assertEqual(set(self.a['views']),{'60','67.5','75'})
  for v,e in self.a['views'].items():self.assertEqual(e['sourceSHA256'],sha(R/e['source']))
 def test_stroke_qa_source(self):
  for v,rec in self.b['views'].items():
   self.assertEqual(rec['sourceSHA256'],self.a['views'][v]['sourceSHA256'])
   self.assertTrue(rec['reassembledPixelExact'])
 def test_five_depth_layers(self):
  self.assertEqual(self.b['depthOrder'],['background','goldTrim','collarWhite','bowFabric','jewel'])
  for v,rec in self.b['views'].items():self.assertEqual(len(rec['layers']),5)
 def test_source_rgba_exact_reassembly(self):
  for v,rec in self.b['views'].items():
   src=np.asarray(Image.open(R/rec['source']).convert('RGBA'))
   rebuilt=np.zeros_like(src)
   assigned=np.zeros(src.shape[:2],np.uint8)
   for role,item in rec['layers'].items():
    layer=np.asarray(Image.open(R/item['texturePath']).convert('RGBA'))
    mask=np.asarray(Image.open(R/item['maskPath']).convert('L'))>128
    self.assertEqual(item['textureSHA256'],sha(R/item['texturePath']))
    self.assertEqual(item['maskSHA256'],sha(R/item['maskPath']))
    self.assertFalse(np.any(assigned[mask]>0))
    rebuilt[mask]=layer[mask]
    assigned[mask]=1
   self.assertTrue(np.array_equal(rebuilt,src))
   self.assertTrue(np.all(assigned==1))
 def test_six_semantic_regions(self):
  self.assertEqual(len(self.b['roleIDs']),6)
  for v,rec in self.b['views'].items():
   self.assertEqual(set(rec['strokeRegions']),set(self.b['roleIDs']))
   for role,item in rec['strokeRegions'].items():
    self.assertEqual(item['maskSHA256'],sha(R/item['maskPath']))
    self.assertGreaterEqual(item['pixelCount'],0)
 def test_candidates_do_not_claim_stroke_certification(self):
  self.assertFalse(self.b['sameStrokeAcrossViewsArtistVerified'])
 def test_region_ink_evidence(self):
  for v,rec in self.b['views'].items():
   self.assertEqual(sum(x['pixelCount'] for role,x in rec['strokeRegions'].items() if role.startswith('bow')),
                    rec['bowInkPixelsOwned'])
   self.assertEqual(sum(x['pixelCount'] for role,x in rec['strokeRegions'].items() if role.startswith('collar')),
                    rec['collarInkPixelsOwned'])
 def test_source_hash_binding(self):
  self.assertEqual(self.c['sourceStrokeQASHA256'],sha(R/'evidence/p15-108-stroke-qa.json'))
 def test_render_three_strategies(self):
  self.assertEqual(len(self.c['methods']),3)
  self.assertEqual(len(self.c['renderedAngles']),9)
 def test_native_full_character_source_keys(self):
  for method,frames in self.c['methods'].items():
   for view in ('60','67.5','75'):
    if method=='sdf_role_ink_original_keys' and view in ('60','75'):
     self.assertEqual(frames[view]['sha256'],self.top['views'][view]['sourceSHA256'])
    else:
     ref=self.old['methods']['companion_direct_native_keys'][view]['relativePath']
     a=np.asarray(Image.open(R/frames[view]['path']).convert('RGBA'))
     b=np.asarray(Image.open(R/ref).convert('RGBA'))
     self.assertTrue(np.array_equal(a,b))
 def test_actual_rendered_frames(self):
  for method,frames in self.c['methods'].items():
   for item in frames.values():
    p=R/item['path']
    self.assertEqual(item['sha256'],sha(p))
    with Image.open(p) as art:
     self.assertEqual(art.mode,'RGBA')
     self.assertEqual(art.size,(1024,1024))
 def test_measured_regional_differences(self):
  for method,regions in self.c['metrics'].items():
   for region,e in regions.items():
    self.assertEqual(len(e['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(a) and a>=0 for a in e['adjacentRGBMAE']))
 def test_review_frames(self):
  self.assertEqual(len(self.v['methodFrames']),5)
  for m,frames in self.v['methodFrames'].items():
   self.assertEqual(len(frames),9)
   for file in frames.values():
    self.assertTrue((P/'p15-108-stroke-render'/file).resolve().is_file())
 def test_gifs(self):
  self.assertEqual(len(self.v['gifs']),5)
  for rec in self.v['gifs'].values():self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html(self):
  html=(P/'p15-108-stroke-render/index.html').read_text()
  for x in ('id="method"','id="yaw"','id="frame"','id="loop"'):self.assertIn(x,html)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),90)
  self.assertEqual(self.browser['errors'],[])
 def test_visual_gate(self):
  self.assertFalse(self.c['continuousYawVisualAccepted'])
  self.assertFalse(self.v['fullVisualContinuityAccepted'])
if __name__=='__main__':unittest.main()
