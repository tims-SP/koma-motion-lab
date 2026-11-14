#!/usr/bin/env python3
"""P15-190 root registration comparison and acceptance gates."""
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-190-root-registration-qa.json'
OUT=ROOT/'private-assets/exports/p15-190-root-registration'
class RootRegistrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_all_methods_have_thirteen_frames(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  for mode in ('baseline','anchor_24','anchor_40','anchor_64'):
   files=list((OUT/mode).glob('yaw*.png'))
   self.assertEqual(len(files),13)
   for path in files:
    with Image.open(path) as im:self.assertEqual(im.size,(443,443))
 def test_source_keys_body_and_free_tip_exact(self):
  self.assertTrue(self.q['gate']['allSourceKeysExact'])
  self.assertTrue(self.q['gate']['allBodyBelow125Exact'])
  self.assertTrue(self.q['gate']['allFreeTipsExact'])
  self.assertTrue(self.q['gate']['allMidframesConnected'])
  for method in self.q['methods'].values():
   self.assertTrue(method['allNativeKeysExact'])
   self.assertTrue(method['allBodyBelow125Exact'])
   self.assertTrue(method['allConnected'])
   self.assertTrue(method['allFreeTipsExact'])
 def test_selected_candidate_matches_actual_crossing_metric(self):
  chosen=min(self.q['methods'],key=lambda m:(
   self.q['methods'][m]['maxAdjacentCrossingDisplacementPixels'],
   self.q['methods'][m]['maxAdjacentLocalRGBMAE']))
  self.assertEqual(self.q['selectedByCrossingContinuity'],chosen)
  self.assertEqual(chosen,'anchor_40')
  self.assertLess(self.q['methods'][chosen]['maxAdjacentCrossingDisplacementPixels'],
                  self.q['methods']['baseline']['maxAdjacentCrossingDisplacementPixels'])
 def test_temporal_and_color_tradeoffs_recorded(self):
  m=self.q['methods']['anchor_40'];b=self.q['methods']['baseline']
  self.assertLess(m['maxAdjacentLocalRGBMAE'],b['maxAdjacentLocalRGBMAE'])
  self.assertLess(m['maxAdjacentGlobalRGBMAE'],b['maxAdjacentGlobalRGBMAE'])
  self.assertGreater(m['maxAdjacentColorSeamChange'],b['maxAdjacentColorSeamChange'])
  self.assertGreater(m['middleColorSeamChanges'][0],b['middleColorSeamChanges'][0])
  self.assertFalse(self.q['gate']['globalTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['colorSeamContinuityAccepted'])
 def test_production_gate_remains_closed(self):
  self.assertFalse(self.q['sourceKeysModified'])
  self.assertFalse(self.q['productionRendererUpdated'])
  self.assertFalse(self.q['visualAccepted'])
  self.assertFalse(self.q['gate']['passes'])
if __name__=='__main__':unittest.main()
