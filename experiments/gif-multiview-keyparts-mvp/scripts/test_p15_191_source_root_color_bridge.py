#!/usr/bin/env python3
"""P15-191 source-root color validation and accepted baseline contract."""
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-191-source-root-color-qa.json'
OUT=ROOT/'private-assets/exports/p15-191-source-root-color'
class RootColorBridgeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_source_key_crossings_and_anchor_identity(self):
  p=self.q['rootAnchorVsCrossing']
  self.assertEqual(set(p),{'90','112.5','135'})
  self.assertGreater(p['112.5']['distance'],17)
  self.assertLess(p['112.5']['distance'],19)
  self.assertTrue(self.q['nativeVisibleColorPalette'])
 def test_all_candidate_images(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  for mode in self.q['methods']:
   files=list((OUT/mode).glob('yaw*.png'))
   self.assertEqual(len(files),13)
   for f in files:
    with Image.open(f) as img:self.assertEqual(img.size,(443,443))
 def test_alpha_keyframes_and_lower_head_are_exact(self):
  self.assertTrue(self.q['gate']['nativeKeysExact'])
  self.assertTrue(self.q['gate']['allAlphaExact'])
  self.assertTrue(self.q['gate']['deepBodyExact'])
  for item in self.q['methods'].values():
   self.assertTrue(item['nativeKeysExact'])
   self.assertTrue(item['alphaExact'])
   self.assertTrue(item['below125Exact'])
 def test_original_has_best_seam_score(self):
  metrics=self.q['methods']
  self.assertEqual(self.q['selectedDiagnosticMethod'],'original')
  for name in metrics:
   if name!='original':
    self.assertGreater(metrics[name]['maxAdjacentRootColorSeamChange'],
                       metrics['original']['maxAdjacentRootColorSeamChange'])
    self.assertGreater(metrics[name]['maxAdjacentLocalRGBMAE'],
                       metrics['original']['maxAdjacentLocalRGBMAE'])
  self.assertFalse(self.q['gate']['rootSeamImproved'])
 def test_final_gate_remains_closed(self):
  self.assertTrue(self.q['gate']['localTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['globalTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['sourceRootIdentityApproved'])
  self.assertFalse(self.q['gate']['visualAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
