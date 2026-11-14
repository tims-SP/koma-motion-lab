#!/usr/bin/env python3
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-188-root-occlusion-sweep-qa.json'
OUT=ROOT/'private-assets/exports/p15-188-root-occlusion-sweep'
class RootOcclusionSweepTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_thirteen_yaw_outputs_and_preview(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  self.assertTrue((OUT/'index.html').is_file())
  for mode in ('hair_front','crown_front','crown_front_root_slot'):
   files=list((OUT/mode).glob('yaw*.png'));self.assertEqual(len(files),13)
   for path in files:
    with Image.open(path) as im:self.assertEqual(im.size,(443,443))
 def test_source_keys_and_deep_body_are_exact(self):
  for mode in self.q['methods'].values():
   self.assertTrue(mode['allNativeKeysExact'])
   self.assertTrue(mode['allDeepBodyExact'])
   self.assertTrue(mode['allMidframesConnected'])
 def test_crown_front_hides_root_under_source_owned_scalp(self):
  mode=self.q['methods']['crown_front']
  self.assertTrue(mode['allRootsHiddenBehindCrown'])
  for report in self.q['details']['crown_front'].values():
   self.assertGreaterEqual(report['rootUnderpaintCoverageRatio'],.90)
   self.assertGreater(report['rootUnderpaintSampleCount'],0)
 def test_crown_front_reduces_local_temporal_error(self):
  mode=self.q['methods']['crown_front']
  self.assertLess(mode['maxAdjacentLocalRGBMAE'],mode['maxAdjacentDISLocalRGBMAE'])
  self.assertLess(mode['maxAdjacentLocalRGBMAE'],self.q['methods']['hair_front']['maxAdjacentLocalRGBMAE'])
  self.assertLess(mode['maxAdjacentLocalRGBMAE'],self.q['methods']['crown_front_root_slot']['maxAdjacentLocalRGBMAE'])
 def test_global_and_visual_gates_remain_explicit(self):
  self.assertFalse(self.q['gate']['globalTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['rootEmergenceVisuallyAccepted'])
  self.assertFalse(self.q['gate']['semanticRootCorrespondenceVerified'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
