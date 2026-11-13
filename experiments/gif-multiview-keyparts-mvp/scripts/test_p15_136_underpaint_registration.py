import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_136_underpaint_registration.py')
s=importlib.util.spec_from_file_location('p15_136_underpaint_registration',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class UnderpaintRegistrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.evaluate(save=False)
 def test_local_expansion(self):
  self.assertEqual(self.q['selectedDiagnostic'],'extended_16')
  self.assertLess(self.q['comparison']['extended_16']['inferredPixels'],600)
  self.assertGreater(self.q['comparison']['extended_16']['inferredPixels'],0)
 def test_ear_and_neck_hole_reduction(self):
  a=self.q['comparison']['native_aligned']['shifts']
  b=self.q['comparison']['extended_16']['shifts']
  for shift in ('12','24'):
   self.assertEqual(b[shift]['alphaHoles']['ear'],0)
   self.assertLess(b[shift]['alphaHoles']['neck'],a[shift]['alphaHoles']['neck'])
   self.assertLess(b[shift]['alphaHoles']['all'],a[shift]['alphaHoles']['all'])
 def test_unchanged_art_and_unresolved_eye(self):
  self.assertTrue(self.q['sourceKeyPixelPreservation'])
  self.assertTrue(self.q['sourceUnderpaintPreservation'])
  self.assertGreater(self.q['comparison']['extended_16']['shifts']['24']['alphaHoles']['eye'],0)
  self.assertFalse(self.q['artQualityAccepted'])
  self.assertFalse(self.q['fullVisualAcceptance'])
 def test_extension_only_inside_original_hair(self):
  from p15_135_closed_hair_mask import closed_mask
  source=m.rgba(m.SOURCE)
  under=m.transform(np.asarray(m.Image.open(m.P/'p15-134-occlusion-underpaint/underpaint-native.png').convert('RGBA').resize((443,443),m.Image.Resampling.LANCZOS)))
  _,filled,_=m.extend(under,16)
  hair=closed_mask(source)[0]
  self.assertTrue(np.all(~filled|hair))
if __name__=='__main__':unittest.main()
