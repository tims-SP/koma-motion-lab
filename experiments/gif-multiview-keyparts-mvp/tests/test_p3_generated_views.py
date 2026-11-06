#!/usr/bin/env python3
"""Tests on actual P0 reference-guided RGBA generation and camera-angle QA."""
import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"private-assets"
GENERATED=ASSETS/"p3-native-source-trial"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

@unittest.skipUnless((GENERATED/"qa.json").is_file(), "Generated P0 assets are private")
class P0ReferenceGuidedViews(unittest.TestCase):
    def test_genuine_original_reference_source_hashes(self):
        record=json.loads((GENERATED/"qa.json").read_text())
        self.assertEqual(record["characterId"],"p0_character_001")
        self.assertEqual(record["sourceGenerationStatus"],"PASS")
        originals=[("yaw000",0),("yaw045",45),("yaw090",90)]
        for rec,(label,yaw) in zip(record["sourceGeneration"]["referenceInputs"],originals):
            path=ASSETS/"recovered-review/frames/head_8"/f"yaw{yaw:03d}_whole.png"
            self.assertEqual(rec["sha256"],sha(path))

    def test_generated_rgba_canvas_alpha_and_provenance(self):
        record=json.loads((GENERATED/"qa.json").read_text())
        self.assertIn("remove_image_background", " ".join(record["sourceGeneration"]["transparentBackgroundPipeline"]))
        for result in record["sourceGeneration"]["generatedOutputs"]:
            p=GENERATED/Path(result["path"]).name
            self.assertEqual(sha(p),result["sha256"])
            with Image.open(p) as image:
                self.assertEqual(image.mode,"RGBA")
                self.assertEqual(image.size,(1024,1024))
                alpha=np.asarray(image.getchannel("A"))
                self.assertEqual(int(alpha[0,0]),0)
                self.assertEqual(int(alpha[-1,-1]),0)
                self.assertGreater(int(np.count_nonzero((alpha>0)&(alpha<255))),100)

    def test_angle_progress_geometry_uses_original_anchor_keys(self):
        report=json.loads((GENERATED/"preview/yaw-progress-qa.json").read_text())
        self.assertEqual(report["status"],"GENERATED_VIEW_ANGLES_REQUIRE_POSE_CONSTRAINTS")
        self.assertEqual(report["failed"],4)
        progress={(c["candidateYaw"],c["region"]):c for c in report["checks"]}
        self.assertLess(progress[(22.5,"head")]["estimatedSilhouetteProgress"],0.20)
        self.assertLess(progress[(67.5,"head")]["estimatedSilhouetteProgress"],0.30)
        for rec in report["sources"].values():
            self.assertEqual(sha(ASSETS/rec["path"]),rec["sha256"])

    def test_five_view_storyboard_is_actual_source_art(self):
        report=json.loads((GENERATED/"preview/qa.json").read_text())
        self.assertEqual(report["characterId"],"p0_character_001")
        self.assertEqual(report["generatedViewCount"],2)
        self.assertEqual(report["originalKeyframeCount"],3)
        self.assertEqual(report["GIFFrames"],8)
        self.assertEqual(sha(report["outputGIF"]),report["GIFSHA256"])
        self.assertEqual(sha(report["outputContact"]),report["contactSHA256"])
        with Image.open(report["outputGIF"]) as image:
            self.assertEqual(image.n_frames,8)

    def test_pose_guided_camera_fidelity_review(self):
        data=json.loads((GENERATED/"iteration2/qa.json").read_text())
        self.assertEqual(data["characterId"],"p0_character_001")
        self.assertEqual(data["sourceGenerationStatus"],"PASS")
        result=data["sourceGeneration"]["generatedOutputs"][0]
        self.assertEqual(sha(GENERATED/"iteration2/yaw0675_pose_guided.png"),
                         result["sha256"])
        self.assertEqual(data["subjectiveYawFidelity"]["farEyeSliver"],"NOT_MET")
        self.assertEqual(data["result"],
                         "PASS_FORMAT_ALPHA_IDENTITY__FAIL_EXACT_YAW_GEOMETRY")

if __name__=="__main__":
    unittest.main(verbosity=2)
