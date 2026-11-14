import importlib.util
import unittest
from pathlib import Path
import numpy as np

ROOT=Path(__file__).parent
def load(name):
    path=ROOT/(name+'.py')
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

gate=load('p15_151_double_root_gate')
study=load('p15_151_root_extension')

class RootGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=gate.analyze(save=False)
        cls.trial=study.evaluate(save=False)

    def test_three_keyviews_coverage(self):
        self.assertEqual(set(self.q['views']),{'90','112.5','135'})
        for view in self.q['views'].values():
            self.assertEqual(len(view['rows']),8)
            self.assertTrue(view['sourceBelowY130PixelExact'])

    def test_missing_root_is_identified(self):
        self.assertEqual(self.q['views']['90']['lastPairedRowY'],55)
        self.assertFalse(self.q['views']['90']['twoRootsReachAttachmentY75'])
        self.assertTrue(self.q['views']['112.5']['twoRootsReachAttachmentY75'])
        self.assertTrue(self.q['views']['135']['twoRootsReachAttachmentY75'])
        self.assertFalse(self.q['geometryGate']['allViewsTwoRootsReachAttachment'])

    def test_geometric_extension_of_double_root(self):
        self.assertFalse(self.trial['variants']['source_fit']['rootAtY75'])
        self.assertTrue(self.trial['variants']['root_075']['rootAtY75'])
        self.assertTrue(self.trial['variants']['root_081']['rootAtY75'])
        self.assertTrue(self.trial['variants']['root_087']['rootAtY75'])
        for result in self.trial['variants'].values():
            self.assertTrue(result['sourceBelowY130Exact'])

    def test_continuity_is_observed_but_not_artistic_acceptance(self):
        self.assertLess(self.trial['variants']['root_081']['maxAdjacentRGBMAE'],
                        self.trial['sourceMaximumAdjacentRGBMAE'])
        self.assertFalse(self.q['geometryGate']['physicalCorrespondenceApproved'])
        self.assertFalse(self.q['geometryGate']['sourcePaintedHiddenScalpAvailable'])
        self.assertFalse(self.trial['rootTopologyArtistApproved'])
        self.assertFalse(self.trial['fullYawVisualAccepted'])

    def test_original_material_preserved(self):
        self.assertTrue(self.q['sourceArtworkUnmodified'])
        self.assertTrue(self.trial['nativeSourcePreserved'])
        raw,_=gate.load_native(90.)
        fitted,_=gate.fit(raw,gate.keyframes()[90.])
        elongated=study.extend_lower_roots(fitted,new_end=81)
        self.assertTrue(np.array_equal(elongated[:28],fitted[:28]))
        self.assertFalse(np.array_equal(elongated[40:75],fitted[40:75]))

if __name__=='__main__':
    unittest.main()
