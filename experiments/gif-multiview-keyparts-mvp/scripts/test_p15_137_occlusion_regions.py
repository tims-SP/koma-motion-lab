import importlib.util
import unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_137_occlusion_regions.py')
spec=importlib.util.spec_from_file_location('p15_137_occlusion_regions',p)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class OcclusionRegionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=module.run(save=False)
 def test_eye_candidate_reduces_holes(self):
  base=self.qa['variants']['p15_136']['shiftTests']
  eye=self.qa['variants']['eye_08']['shiftTests']
  for d in ('12','24'):
   self.assertLess(eye[d]['holes']['eye'],base[d]['holes']['eye'])
   self.assertLess(eye[d]['holes']['all'],base[d]['holes']['all'])
 def test_selected_local_candidate(self):
  self.assertEqual(self.qa['selectedDiagnostic'],'eye_08')
  self.assertLess(self.qa['variants']['eye_08']['addedInferredPixels'],100)
 def test_extrapolation_not_artwork(self):
  self.assertFalse(self.qa['rearScalpSourcePaintApproved'])
  self.assertFalse(self.qa['artistApprovedEyeArt'])
  self.assertFalse(self.qa['visualAccepted'])
  self.assertFalse(self.qa['continuousYawRendered'])
 def test_source_pixels_unchanged(self):
  self.assertTrue(self.qa['sourcePixelsUnchanged'])
  self.assertTrue(self.qa['nativeGeneratedUnderpaintUnchanged'])
  self.assertEqual(self.qa['variants']['eye_08']['shiftTests']['0']['holes']['all'],0)
if __name__=='__main__':unittest.main()
