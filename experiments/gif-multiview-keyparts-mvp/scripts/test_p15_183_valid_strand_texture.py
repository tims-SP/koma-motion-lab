#!/usr/bin/env python3
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-183-valid-strand-texture-qa.json'
OUT=ROOT/'private-assets/exports/p15-183-valid-strand-texture'
class StrandTextureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_all_five_texture_variants(self):
  self.assertEqual(set(self.q['modes']),{'native','nearest_valid','alpha_normalized','valid_mix_50','valid_mix_75'})
  for mode in self.q['modes']:
   imgs=list((OUT/mode).glob('yaw*.png'))
   self.assertEqual(len(imgs),5)
   for path in imgs:
    with Image.open(path) as im:self.assertEqual(im.size,(443,443))
 def test_source_and_geometry_preserved(self):
  for v in self.q['modes'].values():
   self.assertTrue(v['allSourceKeysExact'])
   self.assertTrue(v['allDeepBodyExact'])
   self.assertTrue(v['singleConnectedStrand'])
   self.assertTrue(v['freeTipPreserved'])
 def test_source_valid_color_reduces_dark_fringe(self):
  metrics=self.q['modes']
  self.assertGreater(metrics['native']['totalDarkEdgePixels'],metrics['valid_mix_75']['totalDarkEdgePixels'])
  self.assertGreater(metrics['valid_mix_75']['totalDarkEdgePixels'],metrics['nearest_valid']['totalDarkEdgePixels'])
  self.assertTrue(self.q['gate']['textureDarkEdgeReduced'])
  self.assertEqual(self.q['selectedDiagnosticMethod'],'valid_mix_75')
 def test_temporal_and_visual_acceptance_are_evidence_based(self):
  self.assertFalse(self.q['gate']['temporalBetterThanP15182'])
  self.assertFalse(self.q['gate']['temporalBeatsWholeFrameBaseline'])
  self.assertFalse(self.q['gate']['visualAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
