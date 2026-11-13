import importlib.util
import unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_150_three_view_ahoge.py')
spec=importlib.util.spec_from_file_location('p15_150_three_view_ahoge',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ThreeViewAhogeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qa=m.run(save=False)

    def test_all_native_rgba_assets_verified(self):
        self.assertEqual(self.qa['sourceAngles'],[90.,112.5,135.])
        self.assertEqual(len(self.qa['views']),3)
        for angle in self.qa['sourceAngles']:
            raw,meta=m.load_native(angle)
            self.assertEqual(raw.shape,(443,443,4))
            self.assertEqual(meta['nativeDimensions'],[1254,1254])
            self.assertEqual(meta['nativeFormat'],'RGBA')
            self.assertEqual(meta['nativeSHA256'],m.sha(m.image_for(angle)))

    def test_alpha_isolated_from_lower_body(self):
        for result in self.qa['views'].values():
            self.assertEqual(result['raw']['opaqueBelowY120'],0)
            self.assertGreater(result['raw']['opaquePixels'],1000)
            self.assertTrue(result['sourceBelowY130Exact'])

    def test_source_registration_is_recorded(self):
        for result in self.qa['views'].values():
            fit=result['registration']
            self.assertGreater(fit['freeLoopAlphaIoU'],0.5)
            self.assertLess(fit['freeLoopAlphaIoU'],1.)
            self.assertGreater(result['freeLoopPixelsSource'],500)

    def test_complete_yaw_review_and_no_false_acceptance(self):
        self.assertEqual(len(self.qa['samples']),5)
        self.assertEqual(len(self.qa['render']['candidateAdjacentRGBMAE']),4)
        self.assertFalse(self.qa['assetAdmissionGate']['passes'])
        self.assertFalse(self.qa['assetAdmissionGate']['candidateSelectedForProduction'])
        self.assertFalse(self.qa['physicalDoubleRootIdentityVerified'])
        self.assertFalse(self.qa['hiddenCrownUnderpaintApproved'])
        self.assertFalse(self.qa['continuousVisualAccepted'])

    def test_reference_painting_remains_unchanged(self):
        self.assertTrue(self.qa['sourceArtUnmodified'])
        self.assertTrue(self.qa['nativeGeneratedFilesPreserved'])
        source=m.keyframes()
        for angle in self.qa['sourceAngles']:
            part,_=m.load_native(angle)
            aligned,_=m.fit(part,source[angle])
            candidate=m.replace_upper(source[angle],aligned)
            self.assertTrue(np.array_equal(candidate[130:],source[angle][130:]))

if __name__=='__main__':
    unittest.main()
