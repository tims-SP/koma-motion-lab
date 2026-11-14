#!/usr/bin/env python3
"""P15-194 source semantic landmark correspondence regression tests."""
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-194-multifeature-correspondence-qa.json'
OUT=ROOT/'private-assets/exports/p15-194-multifeature-correspondence'
class MultiFeatureCorrespondenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_five_native_features_are_ordered_and_shared(self):
  self.assertEqual(self.q['featureNames'],['root','entry_shoulder','outer_arc_apex','exit_shoulder','free_tip'])
  self.assertEqual(self.q['sharedFeatureCoordinates'],[0,.25,.5,.75,1])
  for key,v in self.q['sourceFeatureLandmarks'].items():
   ids=v['indices']
   self.assertEqual(ids[0],0);self.assertEqual(ids[-1],159)
   self.assertTrue(all(a<b for a,b in zip(ids,ids[1:])))
   self.assertEqual(len(v['coordinates']),5)
 def test_all_thirteen_yaw_renders_exist(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  for method in ('arc_linear','multi_feature_linear'):
   files=list((OUT/method).glob('yaw*.png'))
   self.assertEqual(len(files),13)
   for f in files:
    with Image.open(f) as im:self.assertEqual(im.size,(443,443))
 def test_native_keys_connectivity_and_body_are_preserved(self):
  self.assertTrue(self.q['gate']['allNativeKeysExact'])
  self.assertTrue(self.q['gate']['allMidframesSingleComponent'])
  self.assertTrue(self.q['gate']['allMidframesHaveActualCrownCrossing'])
  self.assertTrue(self.q['gate']['allDeepBodyExact'])
  for method in self.q['methods'].values():
   self.assertTrue(method['allNativeKeysExact'])
   self.assertTrue(method['allMidframesSingleComponent'])
   self.assertTrue(method['allMidframesHaveActualCrownCrossing'])
   self.assertTrue(method['allDeepBodyExact'])
 def test_multifeature_candidate_improves_geometry_and_local_temporal(self):
  m=self.q['methods'];a=m['arc_linear'];b=m['multi_feature_linear']
  self.assertEqual(self.q['selectedDiagnosticMethod'],'multi_feature_linear')
  self.assertLess(b['maxAdjacentRootCrossingStepPixels'],a['maxAdjacentRootCrossingStepPixels'])
  self.assertLess(b['maxAdjacentLocalRGBMAE'],a['maxAdjacentLocalRGBMAE'])
  self.assertLess(b['maxAdjacentFeatureStepByName']['entry_shoulder'],a['maxAdjacentFeatureStepByName']['entry_shoulder'])
  self.assertLess(b['maxAdjacentFeatureStepByName']['exit_shoulder'],a['maxAdjacentFeatureStepByName']['exit_shoulder'])
 def test_global_and_visual_acceptance_remain_open(self):
  self.assertFalse(self.q['gate']['globalTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['visualAccepted'])
  self.assertFalse(self.q['gate']['semanticFeatureCorrespondenceApproved'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
