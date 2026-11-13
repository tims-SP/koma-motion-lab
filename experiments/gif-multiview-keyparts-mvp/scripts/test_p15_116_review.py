#!/usr/bin/env python3
"""P0 native-view keyframe, explicit source-owner masks and real browser QA."""
from pathlib import Path
from hashlib import sha256
from PIL import Image
import json,math,unittest,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda p:sha256(Path(p).read_bytes()).hexdigest()
class SourceVisibility(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  def read(s):return json.loads((R/'evidence'/s).read_text())
  cls.q=read('p15-116-render-qa.json')
  cls.review=read('p15-116-review-qa.json')
  cls.browser=read('p15-116-browser-qa.json')
  cls.base=read('p15-107-companion-qa.json')
  cls.source=read('p15-115-source-qa.json')
 def test_character_and_angle_range(self):
  self.assertEqual(self.q['characterId'],'p0_character_001')
  self.assertEqual(self.q['sourceViews'],[60,67.5,75])
  self.assertEqual(len(self.q['renderAngles']),9)
 def test_verified_source_registration(self):
  self.assertEqual(self.q['sourceQASHA256'],sha(R/'evidence/p15-115-source-qa.json'))
  self.assertEqual(self.q['physicalSourceOwnership']['bowFabric'],'67.5')
 def test_native_right_lapel_handoff(self):
  self.assertEqual(self.q['physicalSourceOwnership']['goldTrimRight75'],'75')
  self.assertEqual(self.source['registered']['goldTrimRight']['75']['sourceOwner'],'nativeTarget')
 def test_four_candidate_strategies(self):
  self.assertEqual(len(self.q['models']),4)
  for rows in self.q['models'].values():self.assertEqual(len(rows),9)
 def test_native_keyframes_bit_identical(self):
  for key in ('60','67.5','75'):
   reference=self.base['methods']['companion_direct_native_keys'][key]['sha256']
   for method,frames in self.q['models'].items():
    self.assertEqual(frames[key]['sha256'],reference)
    self.assertEqual(frames[key]['changed512Pixels'],0)
 def test_all_candidate_pngs(self):
  for frames in self.q['models'].values():
   for rec in frames.values():
    f=R/rec['path']
    self.assertEqual(rec['sha256'],sha(f))
    with Image.open(f) as art:
     self.assertEqual(art.size,(1024,1024))
     self.assertEqual(art.mode,'RGBA')
 def test_preserved_source_frame_content(self):
  self.assertTrue(self.q['outsideMaterialRegionPixelExact'])
  self.assertTrue(self.q['nativeKeyframeByteExact'])
 def test_per_frame_local_pixel_changes(self):
  for method,frames in self.q['models'].items():
   for angle,rec in frames.items():
    if angle in ('60','67.5','75'):continue
    with Image.open(R/rec['path']) as art:
     current=np.asarray(art.convert('RGBA'),dtype=np.int16)
    with Image.open(R/self.base['methods']['companion_direct_native_keys'][angle]['relativePath']) as original:
     base=np.asarray(original.convert('RGBA'),dtype=np.int16)
    changed=np.any(current!=base,axis=2)
    y,x=np.where(changed)
    self.assertGreater(len(x),0,(method,angle))
    self.assertGreater(int(x.min()),360)
    self.assertGreater(int(y.min()),650)
    self.assertLess(int(x.max()),1024)
    self.assertLess(int(y.max()),1024)
 def test_bounded_alpha_footprint(self):
  for method,frames in self.q['models'].items():
   for angle,rec in frames.items():
    if angle in ('60','67.5','75'):continue
    area=rec['changedBoundingBox512']
    self.assertIsNotNone(area)
    self.assertGreater(area[0],180)
    self.assertGreater(area[1],325)
 def test_source_matte_owner_metrics(self):
  for method,frames in self.q['models'].items():
   for angle,rec in frames.items():
    if angle in ('60','67.5','75'):continue
    for name,val in rec['ownerDebug'].items():
     self.assertGreaterEqual(val['nativeMaterialMaskPixels'],0)
     self.assertGreaterEqual(val['newOneSourcePixels'],0)
     self.assertGreaterEqual(val['oldRimRemovedPixels'],0)
 def test_vision_result_not_automatically_approved(self):
  self.assertFalse(self.q['full360ArtistApproved'])
  self.assertFalse(self.review['artistFullYawAccepted'])
 def test_rgb_temporal_metrics(self):
  self.assertEqual(len(self.q['metrics']),7)
  for method,regions in self.q['metrics'].items():
   for k,metric in regions.items():
    self.assertEqual(len(metric['adjacentRGBMAE']),8)
    self.assertTrue(all(math.isfinite(x) and x>=0 for x in metric['adjacentRGBMAE']))
 def test_review_methods_and_frames(self):
  self.assertEqual(len(self.review['methodFrames']),7)
  for m,fs in self.review['methodFrames'].items():
   self.assertEqual(len(fs),9)
   for f in fs.values():self.assertTrue((P/'p15-116-visibility-repair'/f).resolve().is_file())
 def test_review_gif_integrity(self):
  self.assertEqual(len(self.review['animations']),7)
  for item in self.review['animations'].values():
   self.assertEqual(item['sha256'],sha(R/item['path']))
 def test_html_controls(self):
  page=(P/'p15-116-visibility-repair/index.html').read_text()
  for text in ('id="method"','id="yaw"','id="frame"','id="loop"'):
   self.assertIn(text,page)
 def test_source_matte_visual(self):
  self.assertTrue((P/'p15-116-visibility-repair/source-matte-occlusion-contact.jpg').is_file())
  self.assertTrue((P/'p15-116-visibility-repair/trim-reference-difference.jpg').is_file())
 def test_chromium(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),126)
  self.assertFalse(self.browser['errors'])
if __name__=='__main__':unittest.main()
