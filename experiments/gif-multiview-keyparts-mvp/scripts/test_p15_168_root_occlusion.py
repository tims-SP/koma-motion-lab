import importlib.util
import unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_168_root_occlusion.py')
s=importlib.util.spec_from_file_location('p15_168_root_occlusion',p)
m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)

class RootOcclusionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.evaluate(save=False)
 def test_reference_source_and_keyview_immutability(self):
  self.assertEqual(self.qa['renderAngles'],[90,101.25,112.5,123.75,135])
  self.assertTrue(self.qa['gate']['originalKeyviewsPixelExact'])
  self.assertTrue(all(x['originalKeyviewsPixelExact'] for x in self.qa['variants'].values()))
 def test_root_and_crown_ownership_continuity(self):
  self.assertEqual(self.qa['variants']['reference']['topConnectedComponents'],[1,1,1,1,1])
  self.assertEqual(self.qa['variants']['upper_only']['topConnectedComponents'],[1,2,1,2,1])
  for name in ('root_front','crown_front'):
   self.assertEqual(self.qa['variants'][name]['topConnectedComponents'],[1,1,1,1,1])
  self.assertTrue(self.qa['gate']['bothMidframesConnected'])
 def test_deep_crown_and_body_pixel_exact(self):
  self.assertTrue(self.qa['gate']['zeroChangedPixelsBelowY125'])
  for candidate in self.qa['midframeDiagnostics'].values():
   for sample in candidate.values():
    self.assertTrue(sample['nativeBelowY125Exact'])
    self.assertEqual(sample['headFarBelowCrownChangedChannels'],0)
 def test_root_connection_material_is_present(self):
  for name in ('root_front','crown_front'):
   for meta in self.qa['midframeDiagnostics'][name].values():
    self.assertGreater(meta['visibleHairPixels'],700)
    self.assertGreater(meta['foregroundAlphaPixelsInCrownBand'],0)
 def test_render_is_not_claimed_as_visual_acceptance(self):
  self.assertFalse(self.qa['gate']['beatsCurrentBaseline'])
  self.assertFalse(self.qa['gate']['visualApproval'])
  self.assertFalse(self.qa['gate']['passes'])
  self.assertFalse(self.qa['painterApprovedUnderpaint'])
  self.assertFalse(self.qa['physicalRootConnected'])
  self.assertFalse(self.qa['fullYawVisualAccepted'])
  self.assertFalse(self.qa['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
