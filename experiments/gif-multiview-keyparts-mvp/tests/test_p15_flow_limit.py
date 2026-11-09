#!/usr/bin/env python3
"""Deterministic tests for bounded semantic view-dependent deformation."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p14_keyview_vdd as renderer


def fixture():
    arr = np.zeros((128, 128, 4), dtype=np.uint8)
    arr[50:56, 50:56] = (240, 110, 200, 255)
    flow = np.zeros((64, 64, 2), dtype=np.float32)
    flow[:, :, 0] = 20.0
    grid = np.meshgrid(np.arange(128, dtype=np.float32),
                       np.arange(128, dtype=np.float32))
    return arr, flow, grid


def center_x(frame):
    y, x = np.where(frame[:, :, 3] >= .9)
    return float(x.mean())


class P15FlowLimitTests(unittest.TestCase):
    def test_zero_displacement_preserves_source(self):
        source, flow, grid = fixture()
        flow[:] = 0
        with patch.object(renderer, "W", 128), patch.object(renderer, "G", 64):
            out = renderer.interpolate_alpha(source, flow, .5, grid, 3.0)
        self.assertTrue(np.allclose(out[:, :, 3], source[:, :, 3] / 255, atol=1/255))

    def test_view_limit_bounds_displacement(self):
        source, flow, grid = fixture()
        with patch.object(renderer, "W", 128), patch.object(renderer, "G", 64):
            original = renderer.interpolate_alpha(source, flow, .5, grid)
            bounded = renderer.interpolate_alpha(source, flow, .5, grid, 3.0)
        self.assertGreater(center_x(original) - 52.5, 15)
        self.assertLessEqual(center_x(bounded) - 52.5, 3.5)

    def test_default_matches_original_unbounded_remap(self):
        source, flow, grid = fixture()
        with patch.object(renderer, "W", 128), patch.object(renderer, "G", 64):
            result = renderer.interpolate_alpha(source, flow, .5, grid)
            original = source.astype(np.float32) / 255
            original[:, :, :3] *= original[:, :, 3:4]
            dx = cv2.resize(flow[:, :, 0], (128, 128), interpolation=cv2.INTER_LINEAR) * 2
            dy = cv2.resize(flow[:, :, 1], (128, 128), interpolation=cv2.INTER_LINEAR) * 2
            expected = cv2.remap(original,
                                 grid[0] - .5 * dx, grid[1] - .5 * dy,
                                 cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        self.assertTrue(np.array_equal(result, expected))

    def test_negative_limit_rejected(self):
        source, flow, grid = fixture()
        with patch.object(renderer, "W", 128), patch.object(renderer, "G", 64):
            with self.assertRaisesRegex(ValueError, "nonnegative"):
                renderer.interpolate_alpha(source, flow, .5, grid, -1)


if __name__ == "__main__":
    unittest.main()
