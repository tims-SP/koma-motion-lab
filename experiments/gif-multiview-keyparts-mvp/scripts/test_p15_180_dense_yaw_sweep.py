#!/usr/bin/env python3
"""Structural and diagnostic regression gates for P15-180 dense yaw sweep."""
import json
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-180-dense-yaw-sweep-qa.json'
ASSETS=ROOT/'private-assets/exports/p15-180-dense-yaw-sweep'
YAWS=(90.,95.,100.,101.25,105.,110.,112.5,115.,120.,123.75,125.,130.,135.)
KEYS=(90.,112.5,135.)

class DenseYawSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=json.loads(E.read_text())
    def test_angles_and_artifact_count(self):
        self.assertEqual(tuple(self.q['renderAngles']),YAWS)
        self.assertEqual(tuple(self.q['sourceAngles']),KEYS)
        for method in ('anchor_owner','anchor_blend','anchor_sdf'):
            images=list((ASSETS/method).glob('yaw*.png'))
            self.assertEqual(len(images),len(YAWS))
            for p in images:
                with Image.open(p) as im:
                    self.assertEqual(im.size,(443,443))
    def test_unmodified_keyviews_across_candidates(self):
        self.assertTrue(self.q['gate']['allSourceKeysExact'])
        self.assertTrue(self.q['gate']['allDeepBodyExact'])
        for m in self.q['methods'].values():
            self.assertTrue(m['temporal']['allNativeKeysPixelExact'])
            self.assertTrue(m['temporal']['allBodyBelowY125Exact'])
    def test_dense_motion_produces_contiguous_frames(self):
        self.assertTrue(self.q['gate']['allMidframesConnected'])
        for a,d in self.q['methods']['anchor_owner']['perFrame'].items():
            self.assertEqual(d['topConnectedComponents'],1, a)
    def test_visual_and_temporal_thresholds_remain_explicit(self):
        gate=self.q['gate']
        expected_area=max(self.q['methods']['anchor_owner']['temporal']['adjacentRelativeAirLoopAreaJumps'])
        self.assertAlmostEqual(gate['maxAdjacentRelativeAreaJump'],expected_area,places=4)
        self.assertGreater(gate['maxMidframeRootRGBMAE'],5)
        self.assertFalse(gate['temporalBetterThanReference'])
        self.assertFalse(gate['rootTemporalVisualAccepted'])
        self.assertFalse(gate['passes'])
        self.assertFalse(self.q['productionRendererUpdated'])
    def test_methods_have_different_geometry_behavior(self):
        m=self.q['methods']
        self.assertGreater(m['anchor_blend']['perFrame']['101.25']['airLoopAreaRatio'],1.3)
        self.assertLess(m['anchor_sdf']['perFrame']['101.25']['airLoopAreaRatio'],.7)
        self.assertGreater(m['anchor_owner']['perFrame']['105']['airLoopAreaRatio'],1.3)

if __name__=='__main__':
    unittest.main()
