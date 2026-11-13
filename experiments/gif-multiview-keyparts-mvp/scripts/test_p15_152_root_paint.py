import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_152_root_paint_review.py')
spec=importlib.util.spec_from_file_location('p15_152_root_paint_review',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class NativeCrownPaintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.q=m.evaluate(save=False)
    def test_real_rgba_image_and_provenance(self):
        self.assertEqual(self.q['nativeCanvas'],[1254,1254])
        self.assertTrue(self.q['nativeRGBA'])
        self.assertEqual(self.q['nativeSHA256'],m.sha(m.PNG))
        self.assertTrue(self.q['nativeSourcePreserved'])
    def test_raw_alpha_noise_detected(self):
        self.assertGreater(self.q['rawNonzeroAlphaOutsideExpectedROI'],10000)
        self.assertFalse(self.q['rawTransparentRegionGatePassed'])
        self.assertGreater(self.q['boundedCleanRemovedPixels'],10000)
    def test_alpha_crop_source_integrity(self):
        original=m.rgba(m.P/'exports/p15-151-root-extension/source_fit-composite.png')
        native=m.native()
        clean,mask=m.bounded_clean(native)
        self.assertTrue(np.all(clean[130:]==0))
        self.assertTrue(np.all(clean[~mask]==0))
        self.assertTrue(self.q['boundedCleanBelowY130Exact'])
    def test_real_five_angle_comparison(self):
        values=self.q['variants']
        self.assertEqual(len(values),6)
        self.assertTrue(all(v['native112p5And135Exact'] for v in values.values()))
        self.assertTrue(values['bounded_clean_025']['sourceBelowY130Exact'])
        self.assertLess(values['bounded_clean_025']['maxAdjacentRGBMAE'],values['original']['maxAdjacentRGBMAE'])
        self.assertGreater(values['root_patch_050']['maxAdjacentRGBMAE'],values['original']['maxAdjacentRGBMAE'])
    def test_no_false_art_acceptance(self):
        self.assertFalse(self.q['candidateAdmissionGatePassed'])
        self.assertFalse(self.q['artistVerifiedDoubleRootJunction'])
        self.assertFalse(self.q['hiddenScalpPaintApproved'])
        self.assertFalse(self.q['physicalStrandIdentityVerified'])
        self.assertFalse(self.q['continuousVisualAccepted'])
if __name__=='__main__':unittest.main()
