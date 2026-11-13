import importlib.util
import unittest
from pathlib import Path
p=Path(__file__).with_name('p15_160_root_underpaint.py')
spec=importlib.util.spec_from_file_location('p15_160_root_underpaint',p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RootUnderpaintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.q=m.evaluate(save=False)
    def test_actual_source_roots_cross_extraction_cut(self):
        self.assertEqual(set(self.q['rootInspection']),{'90','112.5','135'})
        for angle,detail in self.q['rootInspection'].items():
            self.assertTrue(detail['sourceRootBelowCut'])
            self.assertGreater(detail['landmarkRoot'][1],54)
            self.assertEqual(detail['loopExtractedPixelsBelowCut'],0)
            self.assertGreater(detail['rootZoneSourcePixels'],100)
    def test_synthetic_inpaint_is_bounded(self):
        for detail in self.q['underpaintProbes'].values():
            self.assertGreater(detail['syntheticInpaintMaskPixels'],100)
            self.assertLess(detail['syntheticInpaintMaskPixels'],200)
            self.assertTrue(detail['nativeSourceUnchanged'])
            self.assertEqual(detail['extendedSourceLoopPixels'],0)
    def test_original_keys_preserved(self):
        for result in self.q['methods'].values():
            self.assertTrue(result['nativeKeysPixelExact'])
        self.assertTrue(self.q['originalSourcesUnchanged'])
    def test_midframe_topology_remains_blocked(self):
        reference=self.q['methods']['reference']
        repair=self.q['methods']['bounded_underpaint']
        self.assertEqual(reference['topConnectedComponents'],[1,1,1,1,1])
        self.assertEqual(repair['topConnectedComponents'],[1,2,1,3,1])
        self.assertLess(repair['maxAdjacentRGBMAE'],self.q['methods']['source_ownership']['maxAdjacentRGBMAE'])
        self.assertGreater(repair['maxAdjacentRGBMAE'],reference['maxAdjacentRGBMAE'])
        self.assertFalse(self.q['acceptanceGate']['passes'])
    def test_unverified_material_is_not_accepted(self):
        self.assertFalse(self.q['independentPaintedRootAvailable'])
        self.assertFalse(self.q['sourceMatchedHiddenScalpApproved'])
        self.assertFalse(self.q['fullYawVisualAccepted'])
        self.assertFalse(self.q['selectedForProduction'])
if __name__=='__main__':unittest.main()
