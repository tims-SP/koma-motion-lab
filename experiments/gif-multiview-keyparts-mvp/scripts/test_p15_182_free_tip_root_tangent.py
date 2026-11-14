#!/usr/bin/env python3
"""P15-182 geometry and temporal gates for one-root/free-tip ahoge motion."""
import importlib.util,json,unittest
from pathlib import Path
import numpy as np
from PIL import Image
SCRIPT=Path(__file__).with_name('p15_182_free_tip_root_tangent.py')
spec=importlib.util.spec_from_file_location('p15_182_free_tip_root_tangent',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FreeTipRootTangentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(m.E.read_text())
 def test_source_tip_is_kept_free(self):
  self.assertTrue(self.q['gate']['freeTipIdentityPreserved'])
  for detail in self.q['details'].values():
   for item in detail.values():
    self.assertTrue(item['freeTipPreserved'])
    self.assertGreaterEqual(item['rootExtensionDistance'],0)
 def test_all_native_keys_and_deep_body_unchanged(self):
  self.assertTrue(self.q['gate']['allNativeKeysExact'])
  self.assertTrue(self.q['gate']['allDeepBodyExact'])
  for v in self.q['methods'].values():
   self.assertTrue(v['allKeyframesExact'])
   self.assertTrue(v['allDeepBodyExact'])
 def test_single_loop_and_bounded_core_area(self):
  self.assertTrue(self.q['gate']['singleLoop'])
  self.assertTrue(self.q['gate']['areaWithin25Percent'])
  for v in self.q['methods'].values():
   self.assertTrue(v['midframesSingleComponent'])
   self.assertTrue(v['areaWithin25Percent'])
 def test_candidate_images_present(self):
  for variant in self.q['methods']:
   files=list((m.OUT/variant).glob('yaw*.png'))
   self.assertEqual(len(files),len(m.ANGLES))
   for f in files:
    with Image.open(f) as im:
     self.assertEqual(im.size,(443,443))
 def test_temporal_and_visual_gates_use_real_data(self):
  best=self.q['bestTemporalCandidate']
  self.assertEqual(best,min(self.q['methods'],key=lambda k:self.q['methods'][k]['maxAdjacentRGBMAE']))
  self.assertTrue(self.q['gate']['betterThanP15181'])
  self.assertFalse(self.q['gate']['beatsWholeFrameReference'])
  self.assertFalse(self.q['gate']['rootContactVisuallyAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
