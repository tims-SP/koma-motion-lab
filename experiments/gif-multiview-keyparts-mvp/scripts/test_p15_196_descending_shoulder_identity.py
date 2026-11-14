#!/usr/bin/env python3
"""P15-196 descending-branch semantic landmark audit regression."""
import json,sys,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-196-descending-shoulder-identity-qa.json'
OUT=ROOT/'private-assets/exports/p15-196-descending-shoulder-identity'
class DescendingShoulderIdentityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_exit_shoulders_are_after_apex_and_in_descending_window(self):
  for a,v in self.q['sourceLandmarks'].items():
   ids=v['indices'];window=v['windows']['exitWindow']
   self.assertGreater(ids[3],ids[2])
   self.assertGreater(window[0],ids[2])
   self.assertGreaterEqual(ids[3],window[0])
   self.assertLess(ids[3],window[1])
   self.assertEqual(v['exitShoulderBranch'],'descending-after-apex')
 def test_native_features_are_ordered_and_hashed(self):
  for v in self.q['sourceLandmarks'].values():
   self.assertEqual(len(v['indices']),5)
   self.assertTrue(all(x<y for x,y in zip(v['indices'],v['indices'][1:])))
   self.assertEqual(len(v['sourceRGBAHash']),64)
   self.assertEqual(len(v['coordinates']),5)
 def test_all_thirteen_angle_renders_and_review_assets_exist(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  self.assertTrue((OUT/'index.html').exists())
  self.assertTrue((OUT/'corrected-native-feature-points.jpg').exists())
  self.assertTrue((OUT/'corrected-shoulder-13-yaw.jpg').exists())
  for name in self.q['methods']:
   paths=list((OUT/name).glob('yaw*.png'))
   self.assertEqual(len(paths),13)
   for p in paths:
    with Image.open(p) as im:self.assertEqual(im.size,(443,443))
 def test_source_and_structural_invariants_hold(self):
  for v in self.q['methods'].values():
   self.assertTrue(v['allNativeKeysExact'])
   self.assertTrue(v['allMidframesHaveCrownCrossing'])
   self.assertTrue(v['allMidframesSingleComponent'])
   self.assertTrue(v['allDeepBodyExact'])
 def test_corrected_feature_correspondence_is_not_promoted(self):
  old=self.q['methods']['P15_194_old_feature_linear']
  new=self.q['methods']['P15_196_corrected_light_smooth']
  self.assertGreater(new['maxAdjacentLocalRGBMAE'],old['maxAdjacentLocalRGBMAE'])
  self.assertGreater(new['maxAdjacentGlobalRGBMAE'],old['maxAdjacentGlobalRGBMAE'])
  self.assertGreater(new['maxAdjacentRootCrossingStepPixels'],old['maxAdjacentRootCrossingStepPixels'])
  self.assertGreater(new['maxAdjacentSeamChange'],old['maxAdjacentSeamChange'])
  self.assertFalse(self.q['gate']['semanticFeatureCorrespondenceApproved'])
  self.assertFalse(self.q['gate']['visualAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
