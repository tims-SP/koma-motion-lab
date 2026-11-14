import importlib.util
import unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_123_part_vdd.py')
s=importlib.util.spec_from_file_location('p15_123_part_vdd',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class TestPartVDD(unittest.TestCase):
    def test_native_visible_partition(self):
        for angle in (90,135,180):
            original=m.load()[angle]
            layers=m.layers(angle)
            self.assertEqual(set(layers),set(m.PARTS))
            visible=original[...,3]>0
            self.assertTrue(np.array_equal(sum((x[...,3]>0).astype(np.uint8) for x in layers.values()),visible.astype(np.uint8)))
            rebuilt=original.copy();rebuilt[visible]=0
            for part in layers.values():rebuilt+=part
            self.assertTrue(np.array_equal(rebuilt,original))

    def test_anchor_coordinates(self):
        for angle in (90,135,180):
            for layer in m.layers(angle).values():
                x,y=m.centroid(layer)
                if layer[...,3].any():
                    self.assertTrue(0<=x<443 and 0<=y<443)

if __name__=='__main__':unittest.main()
