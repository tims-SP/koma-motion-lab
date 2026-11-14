#!/usr/bin/env python3
"""Source geometry and stroke matching invariants for P15-04."""
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import p15_anatomical_strokes as part


class P15AnatomicalStrokesTests(unittest.TestCase):
    def test_alpha_centroid_is_measured_with_transparency(self):
        image = np.zeros((12, 12, 4), dtype=np.uint8)
        image[4, 5, 3] = 255
        image[4, 7, 3] = 255
        center = part.alpha_centroid(image)
        self.assertTrue(np.allclose(center, [6, 4]))
        self.assertIsNone(part.alpha_centroid(np.zeros_like(image)))

    def test_project_original_P5_points_only(self):
        db = {"landmarks": {"nose": [
            {"yaw": 45, "visible": True, "xy": [660, 530]},
            {"yaw": 90, "visible": True, "xy": [760, 540]}
        ]}}
        self.assertTrue(np.allclose(part.source_anchor(db, "nose", 67.5), [710, 535]))
        self.assertIsNone(part.source_anchor(db, "ear", 67.5))

    def test_source_alpha_support_true_false(self):
        native = np.zeros((128, 128, 4), dtype=np.uint8)
        native[49:57, 69:77, 3] = 255
        inside = part.predicted_anchor_support(native, (584, 420))
        outside = part.predicted_anchor_support(native, (140, 140))
        self.assertTrue(inside["candidateMaskContainsPrediction"])
        self.assertEqual(inside["distanceToCandidateAlphaPx1024"], 0)
        self.assertFalse(outside["candidateMaskContainsPrediction"])
        self.assertGreater(outside["distanceToCandidateAlphaPx1024"], 100)

    def test_matching_rejects_missing_ink(self):
        self.assertEqual(part.match_pair([], [], [0, 0]), [])
        self.assertEqual(part.match_pair([], [{"id": "b"}], [1, 0]), [])

    def test_registered_roles_and_angles(self):
        self.assertEqual(len(part.ROLES), 4)
        self.assertEqual(len(part.VIEW_PAIRS) * len(part.ROLES), 12)
        self.assertEqual(part.VIEW_ANGLES, (45, 67.5, 72.5, 90))


if __name__ == "__main__":
    unittest.main()
