import importlib.util
import unittest
from pathlib import Path
p=Path(__file__).with_name('p15_126_midview_correspondence.py')
s=importlib.util.spec_from_file_location('p15_126_midview_correspondence',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class MidviewCorrespondenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=m.audit(save=False)

    def test_independent_midview_is_needed(self):
        self.assertEqual(self.result['targetYaw'],112.5)
        self.assertFalse(self.result['actualIndependent112p5SourceAvailable'])
        self.assertFalse(self.result['physicalHiddenSurfacesVerified'])

    def test_region_disagreement(self):
        regions=self.result['directionalRegionDisagreement']
        self.assertEqual(set(regions),{'hair','face','neck_collar','jacket'})
        for region in regions.values():
            self.assertGreater(region['regionPixels'],0)
            self.assertGreater(region['meanBackgroundCompositeRGBDisagreement'],0)

    def test_mask_scores(self):
        parts=self.result['semanticBoundaryAgreement']
        self.assertEqual(set(parts),{'hair.visible','skin.visible','garment.visible'})
        self.assertTrue(all(0<=v['midpointWarpMaskIoU']<=1 for v in parts.values()))
        self.assertLess(parts['skin.visible']['midpointWarpMaskIoU'],parts['hair.visible']['midpointWarpMaskIoU'])

if __name__=='__main__':unittest.main()
