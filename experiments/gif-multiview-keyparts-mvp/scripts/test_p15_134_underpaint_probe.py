import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_134_underpaint_probe.py')
s=importlib.util.spec_from_file_location('p15_134_underpaint_probe',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class UnderpaintTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.report=m.assess(save=False)
 def test_native_art_provenance(self):
  q=self.report
  self.assertEqual(q['tool'],'image_gen.imagegen')
  self.assertTrue(q['nativeRGBAProven'])
  self.assertEqual(q['nativeDimensions'],[1254,1254])
  self.assertEqual(q['nativeUnderpaintSHA256'],m.sha(m.GEN/'underpaint-native.png'))
 def test_source_layer_recomposition(self):
  self.assertTrue(self.report['sourceAndHairPixelReconstructionExact'])
  self.assertTrue(self.report['sourceAndHairPixelReconstructionExact'])
 def test_jacket_registration(self):
  r=self.report['underpaintRegistration']
  self.assertGreater(r['jacketAlphaIoU'],0.95)
  self.assertLess(r['jacketCompositeRGBMAE'],10)
 def test_hair_reveal_stress(self):
  vals=self.report['displacementStress']
  self.assertLess(vals['0']['compositeDifferenceAgainstOriginalRGBMAE'],vals['12']['compositeDifferenceAgainstOriginalRGBMAE'])
  self.assertLess(vals['12']['newVisibleAlphaPixelsOutsideOriginal'],vals['24']['newVisibleAlphaPixelsOutsideOriginal'])
 def test_art_acceptance_independent(self):
  self.assertTrue(self.report['paintedHiddenScalpPresent'])
  self.assertFalse(self.report['occlusionEdgeRegistrationAccepted'])
  self.assertFalse(self.report['fullRotationVisualAccepted'])
if __name__=='__main__': unittest.main()
