import importlib.util
import unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_127_keyview_transition.py')
spec=importlib.util.spec_from_file_location('p15_127_keyview_transition',p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestIndependentMidview(unittest.TestCase):
    def test_tool_provenance(self):
        for path,metadata in ((m.A,m.A.with_name('generation-result.json')),
                              (m.B,m.B.with_name('generation-result.json'))):
            self.assertTrue(m.validate_native(path,metadata)['actualImageGeneration'])
    def test_bracketed_visible_face(self):
        native=m.load()
        a=m.face_skin_count(native[90]); b=m.face_skin_count(m.key(m.B)); c=m.face_skin_count(native[135])
        self.assertGreater(a,b)
        self.assertGreater(b,c)
    def test_registered_preview(self):
        self.assertEqual(m.key(m.B).shape,(443,443,4))
        self.assertEqual(m.SAMPLES[2],112.5)
if __name__=='__main__':unittest.main()
