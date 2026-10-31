#!/usr/bin/env python3
"""CORE-025 M1 regression tests for the source-over / multiply compositing core.

The expected values are hand-derived constants (they are NOT generated with the
same formula that the implementation uses), so a broken formula cannot make
the tests pass.

Derivation of the constants (all values 0..1, straight RGB + alpha):

  normal:   dst = blue (0,0,1) a=0.5, src = red (1,0,0) a=0.5
            Ao  = 0.5 + 0.5*0.5                       = 0.75
            premult = 0.5*(1,0,0) + 0.5*0.5*(0,0,1)    = (0.5, 0, 0.25)
            Co  = premult / 0.75 = (2/3, 0, 1/3)

  multiply: dst = blue (0,0,1) a=0.5, src = red (1,0,0) a=0.5
            effective = (1,0,0) * (1-0.5 + 0.5*(0,0,1)) = (0.5, 0, 0)
            premult = 0.5*(0.5,0,0) + 0.5*0.5*(0,0,1)    = (0.25, 0, 0.25)
            Co  = (0.25, 0, 0.25) / 0.75 = (1/3, 0, 1/3)

  transparent backdrop: dst = (0,0,0) a=0, src = red (1,0,0) a=1
            effective = (1,0,0) * (1 - 0 + 0*0) = (1,0,0)   -> still red
            premult = 1*(1,0,0) + 0 = (1,0,0); Ao = 1
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prepare_core025 import composite_over  # noqa: E402


def arr(values):
    return np.asarray(values, np.float32)


class Core025BlendTest(unittest.TestCase):
    def test_normal_over_half_transparent_blue(self):
        dst_rgb = arr([[[0.0, 0.0, 1.0]]])
        dst_a = arr([[0.5]])
        src_rgb = arr([[[1.0, 0.0, 0.0]]])
        src_a = arr([[0.5]])
        out_rgb, out_a = composite_over(dst_rgb, dst_a, src_rgb, src_a, "NORMAL")
        self.assertAlmostEqual(float(out_rgb[0, 0, 0]), 2.0 / 3.0, places=6)
        self.assertAlmostEqual(float(out_rgb[0, 0, 1]), 0.0, places=6)
        self.assertAlmostEqual(float(out_rgb[0, 0, 2]), 1.0 / 3.0, places=6)
        self.assertAlmostEqual(float(out_a[0, 0]), 0.75, places=6)

    def test_multiply_over_half_transparent_blue(self):
        dst_rgb = arr([[[0.0, 0.0, 1.0]]])
        dst_a = arr([[0.5]])
        src_rgb = arr([[[1.0, 0.0, 0.0]]])
        src_a = arr([[0.5]])
        out_rgb, out_a = composite_over(dst_rgb, dst_a, src_rgb, src_a, "MULTIPLY")
        self.assertAlmostEqual(float(out_rgb[0, 0, 0]), 1.0 / 3.0, places=6)
        self.assertAlmostEqual(float(out_rgb[0, 0, 1]), 0.0, places=6)
        self.assertAlmostEqual(float(out_rgb[0, 0, 2]), 1.0 / 3.0, places=6)
        self.assertAlmostEqual(float(out_a[0, 0]), 0.75, places=6)

    def test_multiply_over_transparent_backdrop_stays_red(self):
        dst_rgb = arr([[[0.0, 0.0, 0.0]]])
        dst_a = arr([[0.0]])
        src_rgb = arr([[[1.0, 0.0, 0.0]]])
        src_a = arr([[1.0]])
        out_rgb, out_a = composite_over(dst_rgb, dst_a, src_rgb, src_a, "MULTIPLY")
        self.assertAlmostEqual(float(out_rgb[0, 0, 0]), 1.0, places=6)
        self.assertAlmostEqual(float(out_rgb[0, 0, 1]), 0.0, places=6)
        self.assertAlmostEqual(float(out_rgb[0, 0, 2]), 0.0, places=6)
        self.assertAlmostEqual(float(out_a[0, 0]), 1.0, places=6)
        # explicit guard against the classic "multiply against black" bug
        self.assertGreater(float(out_rgb[0, 0, 0]), 0.9)


if __name__ == "__main__":
    unittest.main()
