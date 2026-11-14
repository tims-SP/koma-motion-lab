import importlib.util
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

p=Path(__file__).with_name('p15_175_layered_crown_assets.py')
spec=importlib.util.spec_from_file_location('p15_175_layered_crown_assets',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CrownAndAhogePairTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.run(save=False)
 def test_all_three_keyview_rgba_pairs(self):
  self.assertTrue(self.qa['gate']['allThreePairsPresent'])
  self.assertTrue(self.qa['gate']['allPairsTransparent'])
  for a in m.KEYS:
   folder=m.OUT/'root_contact'/m.TAGS[a]
   with Image.open(folder/'ahoge.png') as strand, Image.open(folder/'crown.png') as crown:
    self.assertEqual(strand.mode,'RGBA')
    self.assertEqual(crown.mode,'RGBA')
    self.assertEqual(strand.size,(443,443))
    self.assertEqual(crown.size,(443,443))
 def test_owner_reassembly_restores_original_for_source_owned_region(self):
  for a in m.KEYS:
   original,strand,crown,owner,reassembled,_,metrics=m.build(a,'root_contact')
   self.assertTrue(np.array_equal(reassembled,original))
   self.assertEqual(metrics['nativeReassemblyDiffPixels'],0)
   self.assertTrue(metrics['sourceBelowY125Exact'])
 def test_other_patch_modes_report_true_mismatch(self):
  for mode in ('root_band','source_ai'):
   for angle in m.KEYS:
    result=m.build(angle,mode)[-1]
    self.assertGreater(result['nativeReassemblyDiffPixels'],0)
    self.assertGreater(result['alphaOverDiffVisiblePixels'],0)
 def test_alpha_over_is_not_confused_with_owner_overwrite(self):
  self.assertGreater(self.qa['perView']['root_contact']['112.5']['alphaOverDiffVisiblePixels'],0)
  self.assertFalse(self.qa['gate']['normalAlphaOverSourceExact'])
  self.assertFalse(self.qa['gate']['losslessOwnerReassembly'])
 def test_visual_acceptance(self):
  self.assertFalse(self.qa['rootlessCrownArtworkArtistApproved'])
  self.assertFalse(self.qa['independentHairArtArtistApproved'])
  self.assertFalse(self.qa['keyviewVisualAccepted'])
  self.assertFalse(self.qa['midYawRendered'])
  self.assertFalse(self.qa['productionRendererUpdated'])
  self.assertFalse(self.qa['gate']['passes'])

if __name__=='__main__':unittest.main()
