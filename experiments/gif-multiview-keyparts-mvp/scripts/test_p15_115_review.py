#!/usr/bin/env python3
"""P15-115 source-part registration, occlusion ownership, local patch and browser QA."""
from pathlib import Path
from PIL import Image
from hashlib import sha256
import json,unittest,math
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports'
sha=lambda x:sha256(Path(x).read_bytes()).hexdigest()
class CanonicalParts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  def qa(s):return json.loads((R/'evidence'/s).read_text())
  cls.reg=qa('p15-115-source-qa.json')
  cls.render=qa('p15-115-render-qa.json')
  cls.local=qa('p15-115-local-qa.json')
  cls.review=qa('p15-115-review-qa.json')
  cls.browser=qa('p15-115-browser-qa.json')
  cls.native=qa('p15-108-stroke-qa.json')
 def test_p0_and_source(self):
  self.assertEqual(self.reg['characterId'],'p0_character_001')
  self.assertEqual(self.reg['sourceView'],'67.5')
  self.assertEqual(self.reg['targetViews'],['60','67.5','75'])
 def test_four_part_groups(self):
  self.assertEqual(set(self.reg['roles']),{'bowFabric','jewel','goldTrimLeft','goldTrimRight'})
 def test_native_source_immutability(self):
  self.assertTrue(self.reg['sourceArtImmutable'])
  for v in ('60','67.5','75'):
   self.assertEqual(self.native['views'][v]['sourceSHA256'],sha(R/self.native['views'][v]['source']))
 def test_registered_texture_sha(self):
  for role,entries in self.reg['registered'].items():
   self.assertEqual(len(entries),3)
   for view,rec in entries.items():
    self.assertEqual(rec['sourceSHA256'],sha(R/rec['source']))
    self.assertEqual(rec['registeredSHA256'],sha(R/rec['registeredPath']))
 def test_all_rgba_frames(self):
  for role,entries in self.reg['registered'].items():
   for rec in entries.values():
    with Image.open(R/rec['registeredPath']) as art:
     self.assertEqual(art.mode,'RGBA')
     self.assertEqual(art.size,(1024,1024))
 def test_bow_correspondence(self):
  self.assertGreater(self.reg['registered']['bowFabric']['60']['sourceToNativeMaskIoU'],.86)
  self.assertGreater(self.reg['registered']['bowFabric']['75']['sourceToNativeMaskIoU'],.78)
 def test_jewel_correspondence(self):
  for view in ('60','75'):
   self.assertGreater(self.reg['registered']['jewel'][view]['sourceToNativeMaskIoU'],.89)
 def test_left_gold_correspondence(self):
  for view in ('60','75'):
   self.assertGreater(self.reg['registered']['goldTrimLeft'][view]['sourceToNativeMaskIoU'],.62)
 def test_right_gold_visible_source_handoff(self):
  self.assertEqual(self.reg['registered']['goldTrimRight']['75']['sourceOwner'],'nativeTarget')
  self.assertEqual(self.reg['registered']['goldTrimRight']['67.5']['sourceOwner'],'canonical67.5')
  self.assertLess(self.reg['registered']['goldTrimRight']['75']['sourceToNativeMaskIoU'],.36)
 def test_stable_affine_except_owner_transition(self):
  for role,entries in self.reg['registered'].items():
   for view,rec in entries.items():
    if role=='goldTrimRight' and view=='75':continue
    self.assertGreater(rec['jacobianDeterminant'],.72)
    self.assertLess(rec['jacobianDeterminant'],1.60)
 def test_three_complete_layered_strategies(self):
  self.assertEqual(len(self.render['methods']),3)
  for method,frames in self.render['methods'].items():
   self.assertEqual(len(frames),9)
 def test_three_local_source_variants(self):
  self.assertEqual(len(self.local['methods']),3)
  for method,frames in self.local['methods'].items():
   self.assertEqual(len(frames),9)
 def test_render_registry_hash(self):
  self.assertEqual(self.render['sourceRegistrySHA256'],sha(R/'evidence/p15-115-source-qa.json'))
  self.assertEqual(self.local['registrationSHA256'],sha(R/'evidence/p15-115-source-qa.json'))
 def test_render_frame_integrity(self):
  for rows in (self.render['methods'],self.local['methods']):
   for method,frames in rows.items():
    for item in frames.values():
     p=R/item['path']
     self.assertEqual(item['sha256'],sha(p))
     with Image.open(p) as art:
      self.assertEqual(art.size,(1024,1024))
      self.assertEqual(art.mode,'RGBA')
 def test_local_changes_bounded(self):
  for mode,frames in self.local['methods'].items():
   for item in frames.values():
    self.assertGreater(item['actualChanged512Pixels'],10)
    self.assertLess(item['actualChanged512Pixels'],8000)
 def test_declared_source_owner(self):
  for mode,frames in self.render['methods'].items():
   for frame in frames.values():
    a=frame['ownerAudit']
    self.assertIn('67.5',a['bowSource'])
    self.assertIn('67.5',a['jewelSource'])
 def test_historical_metrics(self):
  self.assertEqual(len(self.render['metrics']),6)
  self.assertEqual(len(self.local['metrics']),5)
  for q in (self.render,self.local):
   for mode,regions in q['metrics'].items():
    for region,z in regions.items():
     self.assertEqual(len(z['adjacentRGBMAE']),8)
     self.assertTrue(all(math.isfinite(x) and x>=0 for x in z['adjacentRGBMAE']))
 def test_preview_all_methods(self):
  self.assertEqual(len(self.review['methodFrames']),9)
  for method,frames in self.review['methodFrames'].items():
   self.assertEqual(len(frames),9)
   for relative in frames.values():
    self.assertTrue((P/'p15-115-review'/relative).resolve().is_file())
 def test_gifs(self):
  self.assertEqual(len(self.review['animations']),9)
  for rec in self.review['animations'].values():
   self.assertEqual(rec['sha256'],sha(R/rec['path']))
 def test_html(self):
  html=(P/'p15-115-review/index.html').read_text()
  for x in ('id="method"','id="yaw"','id="frame"','id="loop"'):
   self.assertIn(x,html)
 def test_browser(self):
  self.assertEqual(self.browser['status'],'PASS')
  self.assertEqual(len(self.browser['checks']),162)
  self.assertEqual(self.browser['errors'],[])
 def test_visual_gate(self):
  self.assertFalse(self.render['fullYawVisualApproved'])
  self.assertFalse(self.local['fullVisualAccepted'])
  self.assertFalse(self.review['fullYawVisualApproved'])
if __name__=='__main__':unittest.main()
