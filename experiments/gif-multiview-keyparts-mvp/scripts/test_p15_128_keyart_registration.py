import importlib.util
import unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_128_keyart_registration.py')
s=importlib.util.spec_from_file_location('p15_128_keyart_registration',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class RegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=m.measure(save=False)
    def test_bounded_improvement(self):
        self.assertGreaterEqual(self.r['maskIoUAfter'],self.r['maskIoUBefore'])
        self.assertTrue(.94<=self.r['candidateScale']<=1.06)
        self.assertTrue(all(abs(v)<=12 for v in self.r['candidateShiftXY']))
    def test_native_paint_remains_source(self):
        self.assertTrue(self.r['nativeImageUnmodified'])
        self.assertTrue(self.r['sourceKeyframesPixelExact'])
        self.assertEqual(self.r['nativeCandidateSHA256'],m.hashlib.sha256(m.B.read_bytes()).hexdigest())
    def test_geometry_and_art_acceptance_separate(self):
        self.assertFalse(self.r['visualAccepted'])
        self.assertFalse(self.r['hairStrokeCorrespondenceVerified'])
        self.assertFalse(self.r['hiddenSurfaceVerified'])
    def test_input_translation_identity(self):
        key=m.key(m.B)
        self.assertTrue(np.array_equal(m.transform(key,1,0,0),key))
if __name__=='__main__': unittest.main()
