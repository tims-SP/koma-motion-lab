#!/usr/bin/env python3
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-184-alpha-aware-temporal-sweep-qa.json'
OUT=ROOT/'private-assets/exports/p15-184-alpha-aware-temporal-sweep'
class AlphaAwareSweepTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_thirteen_yaw_outputs_exist(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  for variant in self.q['textureMixVariants']:
   files=list((OUT/variant).glob('yaw*.png'))
   self.assertEqual(len(files),13)
   for f in files:
    with Image.open(f) as im:self.assertEqual(im.size,(443,443))
 def test_native_keys_and_structure_are_preserved(self):
  m=self.q['metrics'][self.q['selectedDiagnosticMethod']]
  self.assertTrue(m['allNativeKeysExact'])
  self.assertTrue(m['allDeepBodyExact'])
  self.assertTrue(m['singleConnectedStrand'])
  self.assertTrue(m['freeTipPreserved'])
  self.assertTrue(self.q['gate']['allNativeKeysExact'])
 def test_texture_and_temporal_tradeoff_is_reported(self):
  metrics=self.q['metrics']
  self.assertEqual(self.q['selectedDiagnosticMethod'],'valid_mix_80')
  self.assertLess(metrics['valid_mix_80']['totalDarkEdgePixels'],metrics['valid_mix_65']['totalDarkEdgePixels'])
  self.assertGreater(metrics['valid_mix_80']['maxAdjacentLocalRGBMAE'],metrics['valid_mix_65']['maxAdjacentLocalRGBMAE'])
  self.assertFalse(self.q['gate']['darkEdgePixelsAtMost25'])
  self.assertFalse(self.q['gate']['localTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['globalTemporalBeatsDIS'])
 def test_production_and_visual_gates_remain_closed(self):
  self.assertFalse(self.q['visualAccepted'])
  self.assertFalse(self.q['productionRendererUpdated'])
  self.assertFalse(self.q['gate']['passes'])
if __name__=='__main__':unittest.main()
