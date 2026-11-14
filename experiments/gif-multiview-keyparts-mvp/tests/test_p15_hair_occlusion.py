#!/usr/bin/env python3
"""P15-05 semantic hair depth, alpha-overlap and source contract tests."""
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import p15_hair_occlusion as hair


class HairOcclusionTests(unittest.TestCase):
    def test_semantic_roles_and_depth_are_unique(self):
        self.assertEqual(len(hair.ROLE_SET),4)
        self.assertEqual(len(set(hair.ROLE_SET)),4)
        self.assertEqual(len(hair.PAIRS)*len(hair.ROLE_SET),12)
        for top,lower in hair.OCCLUSION:
            self.assertGreater(hair.EXPECTED_DEPTH[top],hair.EXPECTED_DEPTH[lower])

    def test_source_occlusion_has_deterministic_overlap(self):
        a=np.zeros((8,8),dtype=np.uint8)
        b=np.zeros((8,8),dtype=np.uint8)
        a[2:6,2:6]=255
        b[4:7,4:7]=255
        result=hair.occlusion_measure(a,b)
        self.assertEqual(result["frontVisiblePixels"],16)
        self.assertEqual(result["backVisiblePixels"],9)
        self.assertEqual(result["overlapPixels"],4)
        self.assertEqual(result["singleVisibleBoundaryPixels"],17)
        self.assertAlmostEqual(result["backAlphaCoveredFraction"],4/9,places=5)

    def test_alpha_threshold_changes_occlusion(self):
        top=np.zeros((5,5),dtype=np.uint8)
        low=np.zeros((5,5),dtype=np.uint8)
        top[2,2]=63;low[2,2]=255
        self.assertEqual(hair.occlusion_measure(top,low)["overlapPixels"],0)
        top[2,2]=64
        self.assertEqual(hair.occlusion_measure(top,low)["overlapPixels"],1)

    def test_canvas_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,"Same global"):
            hair.occlusion_measure(np.zeros((4,4),dtype=np.uint8),np.zeros((5,5),dtype=np.uint8))

    def test_ahoge_uses_p5_root_anchor(self):
        self.assertEqual(hair.ANCHORS["hair.ahoge"],("hair.ahoge.root",))
        self.assertEqual(hair.KEYS,(45,67.5,72.5,90))
        self.assertEqual(len(hair.OCCLUSION),4)


if __name__=="__main__":
    unittest.main()
