import importlib.util
import unittest
from pathlib import Path
import numpy as np

path=Path(__file__).with_name('p15_125_hair_flow_regularization.py')
spec=importlib.util.spec_from_file_location('p15_125_hair_flow_regularization',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestRearArcRegularization(unittest.TestCase):
    def test_keyframes_are_source_exact(self):
        sources=module.load()
        for sigma in (0,4,10):
            frames=module.produce(sigma)
            self.assertEqual(len(frames),5)
            self.assertTrue(np.array_equal(frames[0],sources[90]))
            self.assertTrue(np.array_equal(frames[-1],sources[135]))

    def test_rendered_alpha_bounds(self):
        for frame in module.produce(4):
            self.assertEqual(frame.shape,(443,443,4))
            self.assertEqual(frame.dtype,np.uint8)

if __name__=='__main__': unittest.main()
