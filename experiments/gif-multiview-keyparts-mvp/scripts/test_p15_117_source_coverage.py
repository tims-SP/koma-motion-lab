import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('p15_117_source_coverage.py')
spec = importlib.util.spec_from_file_location('p15_117_source_coverage', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SourceCoverageTests(unittest.TestCase):
    def test_verified_native_parts(self):
        result = module.audit()
        self.assertEqual(result['verifiedCompleteManifestAngles'], [0, 45, 90])
        self.assertEqual(result['invalidSourceParts'], [])
        self.assertEqual(len(result['semanticRoles']), 13)

    def test_back_source_gap_is_explicit(self):
        result = module.audit()
        self.assertEqual(result['missingCanonicalManifestAngles'], [135, 180])
        self.assertFalse(result['acceptance']['fullYawVisualAccepted'])

if __name__ == '__main__':
    unittest.main()
