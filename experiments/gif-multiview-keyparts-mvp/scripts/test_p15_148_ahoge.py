import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).parent
def load(name):
    p=ROOT/(name+'.py')
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
native=load('p15_148_native_ahoge_review')
reg=load('p15_148_ahoge_registration')

class NativeAhogeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=native.evaluate(save=False)
        cls.registered=reg.evaluate(save=False)
    def test_true_native_source(self):
        q=self.source
        self.assertEqual(q['generator'],'image_gen.imagegen')
        self.assertTrue(q['nativeAssetPreserved'])
        self.assertEqual(q['nativeDimensions'],[1254,1254])
        self.assertEqual(q['nativeAssetSHA256'],native.sha(native.PNG))
        self.assertTrue(q['registrationGatePassed'])
        self.assertEqual(q['alphaStats']['faceRegionPixels'],0)
        self.assertEqual(q['alphaStats']['outsideExpectedTopRegion'],0)
    def test_spatial_alignment(self):
        q=self.registered
        self.assertGreater(q['fit']['iouAboveCrown'],.6)
        self.assertEqual(q['fit']['shiftXY'],[24,-14])
        self.assertTrue(q['sourcePixelsBelowCrownUnmodified'])
    def test_original_endpoints_exact(self):
        for method in self.registered['methods'].values():
            self.assertTrue(method['sourceEndpoint90And135PixelExact'])
    def test_overlay_versus_reference(self):
        results=self.registered['methods']
        self.assertLess(results['loop_replacement']['maxAdjacentRGBMAE'],
                        results['direct_overlay']['maxAdjacentRGBMAE'])
        self.assertGreater(results['loop_replacement']['maxAdjacentRGBMAE'],
                           results['canonical']['maxAdjacentRGBMAE'])
    def test_art_acceptance_separate(self):
        self.assertFalse(self.source['rootTipArtistVerified'])
        self.assertFalse(self.source['continuousVisualAccepted'])
        self.assertFalse(self.registered['hiddenRootPaintVerified'])
        self.assertFalse(self.registered['visualAccepted'])

if __name__=='__main__':unittest.main()
