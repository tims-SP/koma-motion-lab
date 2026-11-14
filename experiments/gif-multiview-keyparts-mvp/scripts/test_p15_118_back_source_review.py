import importlib.util
import unittest
from pathlib import Path
p=Path(__file__).with_name('p15_118_back_source_review.py')
s=importlib.util.spec_from_file_location('p15_118_back_source_review',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class BackSourceTests(unittest.TestCase):
    def test_provenance_and_alpha(self):
        report=m.audit()
        self.assertEqual([x['angle'] for x in report['candidates']],[90,135,180])
        self.assertTrue(all(x['alphaPixelsGt16']>50000 for x in report['candidates']))
    def test_unverified_layers_explicit(self):
        report=m.audit()
        self.assertEqual(report['semanticLayerCoverage135180'],0)
        self.assertFalse(report['registrationVerified'])
        self.assertFalse(report['visualAcceptance'])
if __name__=='__main__': unittest.main()
