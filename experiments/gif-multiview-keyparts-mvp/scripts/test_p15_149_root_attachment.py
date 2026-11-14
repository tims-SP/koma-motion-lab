import importlib.util
import unittest
from pathlib import Path
import numpy as np

p=Path(__file__).with_name('p15_149_root_attachment.py')
spec=importlib.util.spec_from_file_location('p15_149_root_attachment',p)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RootAttachmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=module.assess(save=False)

    def test_native_source_and_endpoints_preserved(self):
        self.assertTrue(self.q['sourcePreserved'])
        self.assertTrue(all(x['native90And135Exact'] for x in self.q['methods'].values()))
        self.assertTrue(all(v['sourcePixelsBelowFadeExact'] for v in self.q['candidateDetails'].values()))

    def test_smooth_alpha_ownership_boundaries(self):
        original=module.rgba(module.SOURCE)
        native,_=module.actual_source()
        registered=module.shift(native,.9,24,-14)
        for name,(start,end) in module.PARAMS.items():
            candidate,old,fg=module.compose_crown(original,registered,start,end)
            self.assertEqual(int(old.sum()),956)
            self.assertTrue(np.array_equal(original[end+1:],candidate[end+1:]))
            self.assertTrue(np.all(fg[end+1:,:,3]==0))
            self.assertGreater(int((fg[...,3]>16).sum()),1000)

    def test_best_candidate_diagnostic(self):
        scores=self.q['methods']
        self.assertLess(scores['crown_fade_65']['maxAdjacentRGBMAE'],
                        scores['p15_148_loop_replacement']['maxAdjacentRGBMAE'])
        self.assertGreater(scores['crown_fade_65']['maxAdjacentRGBMAE'],
                           scores['canonical']['maxAdjacentRGBMAE'])

    def test_alpha_holes_remain(self):
        self.assertEqual(self.q['methods']['canonical']['rootCoverageAlphaHoles'],0)
        self.assertTrue(all(self.q['methods'][name]['rootCoverageAlphaHoles']>0 for name in module.PARAMS))

    def test_visual_gate(self):
        self.assertFalse(self.q['rootAnatomyArtistApproved'])
        self.assertFalse(self.q['fullLoopHiddenPaintVerified'])
        self.assertFalse(self.q['fullYawVisualAccepted'])

if __name__=='__main__':
    unittest.main()
