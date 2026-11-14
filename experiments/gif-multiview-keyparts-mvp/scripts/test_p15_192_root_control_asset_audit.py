#!/usr/bin/env python3
"""P15-192 native root-control package and held-out key validation."""
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-192-root-control-asset-qa.json'
OUT=ROOT/'private-assets/exports/p15-192-root-control-asset'
class RootControlAssetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_three_source_pairs_reassemble_exact(self):
  self.assertTrue(self.q['gate']['allThreeSourcePairsReassembleExact'])
  for v in self.q['nativeViews'].values():
   self.assertTrue(v['sourcePairReassemblyExact'])
   for key in ('sourceSHA256','strandSHA256','crownPairSHA256','aiRootlessFullSHA256','motionUnderpaintSHA256'):
    self.assertEqual(len(v[key]),64)
 def test_native_112p5_local_asset_exists(self):
  folder=OUT/'yaw112p5'
  for name in ('source.png','source-owned-strand.png','rootless-crown-donor.png','owner-matte.png'):
   self.assertTrue((folder/name).is_file())
  self.assertTrue((OUT/'root-landmarks.json').is_file())
  self.assertTrue((OUT/'112p5-heldout-root-control-candidate.png').is_file())
 def test_heldout_prediction_is_not_native_replacement(self):
  p=self.q['heldOut112p5Prediction']
  self.assertEqual(p['sourceKeysUsed'],[90.0,135.0])
  self.assertEqual(p['heldOutNativeKey'],112.5)
  self.assertLess(p['maskIoU'],.1)
  self.assertGreater(p['crossingDisplacementPixels'],50)
  self.assertFalse(p['nativeKeyframeModified'])
  self.assertFalse(self.q['gate']['heldOutPredictionMatchesNativeKey'])
 def test_p15_189_measurement_reproduces_with_pinned_inputs(self):
  self.assertTrue(self.q['gate']['evidenceReproducible'])
  self.assertFalse(self.q['staleEvidenceDetected'])
  for a,v in self.q['nativeViews'].items():
   self.assertLess(v['staleP15_189CrossingDeltaPixels'],.001)
 def test_production_gate_remains_closed(self):
  self.assertFalse(self.q['sourceAssetsModified'])
  self.assertFalse(self.q['productionRendererUpdated'])
  self.assertFalse(self.q['visualAccepted'])
  self.assertFalse(self.q['gate']['sourceRootSemanticsApproved'])
  self.assertFalse(self.q['gate']['productionApproved'])
  self.assertFalse(self.q['gate']['passes'])
if __name__=='__main__':unittest.main()
