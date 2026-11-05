#!/usr/bin/env python3
"""Regression verification for real P0 45/90° ArtMesh candidate registrations."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/"private-assets"
P2=PRIVATE/"p2-views"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

@unittest.skipUnless((P2/"parts.json").is_file() and
                     (P2/"vdd-canvases/holdout-qa.json").is_file(),
                     "P0 real source P2 artworks only")
class P2ViewAssets(unittest.TestCase):
    def test_two_views_26_parts_and_original_sha(self):
        data=json.loads((P2/"parts.json").read_text())
        self.assertEqual(data["characterId"],"p0_character_001")
        self.assertEqual(data["canvas"],[1024,1024])
        self.assertEqual(len(data["parts"]),26)
        for item in data["parts"]:
            file=PRIVATE/item["path"]
            self.assertEqual(sha(file),item["frameSha256"])
            with Image.open(file) as img:
                self.assertEqual(img.size,(1024,1024))
                self.assertEqual(img.mode,"RGBA")
            self.assertEqual(len(item["mesh"]["vertexIds"]),49)
            self.assertEqual(len(item["mesh"]["triangles"]),72)

    def test_real_yaw45_90_reference_pixel_composition(self):
        data=json.loads((P2/"reconstruction-qa.json").read_text())
        self.assertEqual(data["registeredSlots"],26)
        for angle in ("45","90"):
            info=data["sourceViews"][angle]
            self.assertEqual(info["registeredParts"],13)
            self.assertGreater(info["silhouetteIoU"],0.9999)
            self.assertLessEqual(info["compositePixelDiff"],100)
            self.assertEqual(info["transparentHoles"],0)
        self.assertEqual(data["visibility90Clip"],"hidden")
        self.assertEqual(data["sourceViews"]["45"]["physicalHidden"]["ear.far"],"hidden")
        self.assertEqual(data["sourceViews"]["90"]["physicalHidden"]["eye.far"],"hidden")

    def test_combined_registry_anatomical_topology(self):
        data=json.loads((PRIVATE/"parts.json").read_text())
        self.assertEqual(len(data["parts"]),39)
        self.assertEqual(len(data["wholeViews"]),3)
        parts={(p["yawDeg"],p["semanticId"]):p for p in data["parts"]}
        self.assertEqual(len(parts),39)
        for sid in [p["semanticId"] for p in data["parts"] if p["yawDeg"]==0]:
            for a,b in ((0,45),(45,90)):
                mesh_a=parts[a,sid]["mesh"]
                mesh_b=parts[b,sid]["mesh"]
                self.assertEqual(mesh_a["vertexIds"],mesh_b["vertexIds"])
                self.assertEqual(mesh_a["triangles"],mesh_b["triangles"])

    def test_real_browser_canvas_5_frames_and_art_gate(self):
        report=json.loads((P2/"vdd-canvases/holdout-qa.json").read_text())
        self.assertEqual(report["status"],"PASS_HOLDOUT_COVERAGE")
        self.assertEqual(report["holdoutsFailed"],[])
        keys={x["angle"]:x for x in report["checks"]}
        for yaw in (0,45,90):
            self.assertEqual(keys[yaw]["missingCoveragePixels"],0)
        for yaw in (22.5,67.5):
            self.assertLessEqual(keys[yaw]["missingCoverageRatio"],0.005)
        captures=json.loads((P2/"vdd-canvases/canvas-qa.json").read_text())
        self.assertEqual(captures["status"],"CAPTURED_FOR_ANATOMICAL_INSPECTION")
        self.assertEqual(len(captures["outputs"]),5)
        for item in captures["outputs"]:
            self.assertEqual(sha(item["path"]),item["sha256"])

    def test_holdout_texture_art_acceptance(self):
        texture=json.loads((P2/"vdd-canvases/texture-qa.json").read_text())
        self.assertEqual(texture["status"],"REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE")
        self.assertEqual(texture["failed"],2)
        byangle={x["angle"]:x for x in texture["holdouts"]}
        self.assertGreater(byangle[22.5]["edgeDensityRelativeToAdjacentMax"],5.0)
        self.assertGreater(byangle[67.5]["edgeDensityRelativeToAdjacentMax"],2.0)

    def test_37_frame_visual_motion_preview(self):
        folder=P2/"turn-sequence"
        manifest=json.loads((folder/"turn-gif-qa.json").read_text())
        self.assertEqual(manifest["status"],"REAL_BROWSER_FRAMES_PACKAGED")
        self.assertEqual(manifest["sourceFrameCount"],37)
        self.assertEqual(manifest["GIFFrames"],72)
        self.assertEqual(sha(manifest["GIFFile"]),manifest["GIFSHA256"])
        self.assertEqual(len(list(folder.glob("yaw*.png"))),37)

    def test_private_bundle_integrity(self):
        package=P2/"review-package-qa.json"
        self.assertTrue(package.exists())
        info=json.loads(package.read_text())
        archive=Path(info["path"])
        self.assertEqual(sha(archive),info["sha256"])
        self.assertTrue(info["internalHashesVerified"])
        with zipfile.ZipFile(archive) as z:
            self.assertIsNone(z.testzip())
            manifest=json.loads(z.read("package-manifest.json"))
            self.assertEqual(manifest["registeredSemanticParts"],39)
            self.assertEqual(manifest["holdoutVisualStatus"],
                             "PASS_HOLDOUT_COVERAGE")
            self.assertFalse(manifest["approvedHeroOriginalSHAverified"])

if __name__=="__main__":
    unittest.main(verbosity=2)
