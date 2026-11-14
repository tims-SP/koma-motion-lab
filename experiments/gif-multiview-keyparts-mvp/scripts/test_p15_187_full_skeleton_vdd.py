#!/usr/bin/env python3
"""P15-187 structural and measured temporal regression tests."""
import json,unittest,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-187-full-skeleton-vdd-qa.json'
OUT=ROOT/'private-assets/exports/p15-187-full-skeleton-vdd'
class FullSkeletonVDDTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_thirteen_angle_output_for_both_modes(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  for mode in ('linear_centerline','pchip_centerline'):
   imgs=list((OUT/mode).glob('yaw*.png'))
   self.assertEqual(len(imgs),13)
   for f in imgs:
    with Image.open(f) as im:self.assertEqual(im.size,(443,443))
 def test_full_source_skeleton_geometry(self):
  for key,geo in self.q['sourceGeometry'].items():
   self.assertGreater(geo['skeletonLength'],60)
   self.assertGreater(geo['sourceMaskArea'],100)
   self.assertEqual(len(geo['widthPercentiles']),3)
   self.assertLess(geo['widthPercentiles'][0],geo['widthPercentiles'][2])
   self.assertEqual(len(geo['sourcePixelSHA256']),64)
 def test_keyframes_and_deep_head_are_preserved(self):
  for entry in self.q['methods'].values():
   self.assertTrue(entry['allNativeKeyframesExact'])
   self.assertTrue(entry['allDeepBodyExact'])
   self.assertTrue(entry['allMidframesConnected'])
   self.assertTrue(entry['variableWidthConfirmed'])
 def test_local_temporal_improves_over_reference(self):
  linear=self.q['methods']['linear_centerline']
  self.assertEqual(self.q['selectedDiagnosticMethod'],'linear_centerline')
  self.assertTrue(self.q['gate']['localTemporalBeatsDIS'])
  self.assertLess(linear['maxAdjacentLocalRGBMAE'],linear['maxAdjacentLocalDIS'])
  self.assertLess(linear['maxAdjacentLocalRGBMAE'],self.q['methods']['pchip_centerline']['maxAdjacentLocalRGBMAE'])
 def test_global_and_visual_gates_are_openly_recorded(self):
  self.assertFalse(self.q['gate']['globalTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['crossViewSemanticCorrespondenceVerified'])
  self.assertFalse(self.q['gate']['visualAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
