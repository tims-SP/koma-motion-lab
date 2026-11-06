#!/usr/bin/env python3
"""Regression checks for genuine See-through P0 front PSD and VDD candidate."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile
from PIL import Image
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"private-assets"
P4=BASE/"p4-see-through"
FRONT=P4/"front"
INTEGRATED=FRONT/"integrated"
PSD=FRONT/"p0-character-001-see-through.psd"
MV=P4/"mv-candidate"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fp:
        for chunk in iter(lambda:fp.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

@unittest.skipUnless(PSD.is_file(), "P0 source PSD stored in private assets")
class P0SeeThroughAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads((FRONT/"inference-qa.json").read_text())
        cls.psd=json.loads((FRONT/"exported/layer-qa.json").read_text())
        cls.qa=json.loads((INTEGRATED/"integration-qa.json").read_text())
        cls.manifest=json.loads((INTEGRATED/"integrated-parts.json").read_text())

    def test_source_psd_checksum_and_native_resolution(self):
        with PSD.open("rb") as fp:
            self.assertEqual(fp.read(4),b"8BPS")
        self.assertEqual(self.source["characterId"],"p0_character_001")
        self.assertEqual(self.source["status"],"PSD_RECEIVED_AWAITING_LAYER_INSPECTION")
        self.assertEqual(sha(PSD),self.source["outputFiles"][0]["sha256"])
        self.assertEqual(self.psd["psdSHA256"],sha(PSD))
        self.assertEqual(self.psd["modelCanvas"],[768,768])
        self.assertEqual(self.psd["exportCanvas"],[1024,1024])

    def test_13_semantic_rgba_layers(self):
        self.assertEqual(self.psd["totalLayers"],13)
        self.assertEqual(len(self.psd["layers"]),13)
        names={x["semanticCandidateId"] for x in self.psd["layers"]}
        for name in ("face.skin","hair.back","hair.front","eye.iris.pair",
                     "eye.lash.pair","eye.sclera.pair","ear.pair","hair.clip.cross_gold"):
            self.assertIn(name,names)
        for rec in self.psd["layers"]:
            filename=FRONT/"exported"/rec["outputPath"]
            self.assertEqual(sha(filename),rec["outputSha256"])
            with Image.open(filename) as image:
                self.assertEqual(image.mode,"RGBA")
                self.assertEqual(image.size,(1024,1024))

    def test_original_visible_pixels_and_inferred_underpaint(self):
        self.assertEqual(self.qa["status"],"PASS_SEMANTIC_LAYER_REGISTRATION")
        self.assertEqual(self.qa["layerCount"],13)
        self.assertEqual(self.qa["inferredUnderpaintPixels"],376671)
        self.assertEqual(self.qa["metrics"]["originalStaticSilhouetteIoU"],1)
        self.assertEqual(self.qa["metrics"]["staticOpaqueHoles"],0)
        self.assertLess(self.qa["metrics"]["staticPixelsDifferentMoreThanOne"],1000)
        self.assertLess(self.qa["metrics"]["sourceCompositeColorMAE"],0.01)

    def test_13_physically_named_layers_checksum(self):
        self.assertEqual(len(self.manifest["parts"]),13)
        self.assertEqual(self.manifest["characterId"],"p0_character_001")
        physical={p["semanticId"]:p for p in self.manifest["parts"]}
        self.assertEqual(len(physical),13)
        for sid,rec in physical.items():
            file=INTEGRATED/rec["path"]
            self.assertEqual(sha(file),rec["frameSha256"],sid)
            self.assertEqual(len(rec["mesh"]["vertexIds"]),49)
            self.assertEqual(len(rec["mesh"]["triangles"]),72)
            with Image.open(file) as image:
                self.assertEqual(image.mode,"RGBA")
                self.assertEqual(image.size,(1024,1024))

    def test_fringe_motion_occlusion_improvement(self):
        metrics=self.qa["metrics"]
        before=metrics["sourceFringeMotionOpaqueHoles"]
        after=metrics["inferredFringeMotionOpaqueHoles"]
        self.assertEqual(metrics["fringeMoveDxPx"],16)
        self.assertGreater(before,2500)
        self.assertLess(after,before*0.20)
        self.assertEqual(metrics["inferredFringePreviouslyTransparentRestoredPixels"],before-after)
        self.assertEqual(metrics["nearEyeMotionOpaqueHoles"],0)
        self.assertTrue((INTEGRATED/"p0-fringe-motion-review.jpg").is_file())

    def test_actual_browser_review_captures(self):
        qa=json.loads((FRONT/"browser/browser-qa.json").read_text())
        self.assertEqual(qa["status"],"PASS_P4_PSD_BROWSER_ENGINEERING")
        self.assertTrue(qa["sourceReady"])
        self.assertEqual(qa["sourceSelection"],"seethrough")
        self.assertEqual(qa["initial"]["partCount"],13)
        self.assertFalse(qa["errors"])
        self.assertFalse(qa["failedRequests"])
        self.assertEqual(len(qa["shots"]),3)
        for shot in qa["shots"]:
            self.assertEqual(sha(shot["file"]),shot["sha256"])

    def test_multiview_registry_stable_source_and_holdout_gate(self):
        alt=json.loads((MV/"parts.json").read_text())
        canonical=json.loads((BASE/"parts.json").read_text())
        self.assertEqual(len(alt["parts"]),39)
        self.assertEqual(len(canonical["parts"]),39)
        a={(x["yawDeg"],x["semanticId"]):x for x in alt["parts"]}
        b={(x["yawDeg"],x["semanticId"]):x for x in canonical["parts"]}
        for yaw in (45,90):
            for sid in {x[1] for x in b if x[0]==yaw}:
                self.assertEqual(a[yaw,sid]["frameSha256"],b[yaw,sid]["frameSha256"])
        self.assertEqual(alt["frontAddedUnderpaintPixels"],376671)
        self.assertEqual(json.loads((MV/"holdout-qa.json").read_text())["status"],
                         "PASS_HOLDOUT_COVERAGE")
        texture=json.loads((MV/"texture-qa.json").read_text())
        self.assertEqual(texture["status"],"REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE")
        self.assertEqual(texture["failed"],2)
        capture=json.loads((MV/"vdd-canvas/canvas-qa.json").read_text())
        self.assertEqual(capture["source"],"seethrough-front")
        self.assertEqual(len(capture["outputs"]),5)
        animation=json.loads((MV/"turn-gif-qa.json").read_text())
        self.assertEqual(animation["sourceFrameCount"],37)
        self.assertEqual(animation["GIFFrames"],72)
        self.assertEqual(sha(MV/"p0-psd-front-vdd-turn.gif"),animation["GIFSHA256"])

    @unittest.skipUnless((P4/"p4-package-qa.json").is_file(),"Review package generated after source QA")
    def test_p4_review_archive(self):
        report=json.loads((P4/"p4-package-qa.json").read_text())
        archive=Path(report["archivePath"])
        self.assertEqual(sha(archive),report["sha256"])
        self.assertTrue(report["internalHashesVerified"])
        with zipfile.ZipFile(archive) as z:
            self.assertIsNone(z.testzip())
            meta=json.loads(z.read("package-manifest.json"))
            self.assertEqual(meta["characterId"],"p0_character_001")
            self.assertEqual(meta["registeredSemanticSlots"],39)
            self.assertEqual(meta["psdModelNativeSize"],[768,768])
            self.assertEqual(meta["PSDEnhancedBrowserFrames"],37)
            self.assertEqual(meta["PSDEnhancedMotionGIFFrames"],72)
            self.assertEqual(meta["vddHoldoutTextureStatus"],
                             "REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE")

if __name__=="__main__":
    unittest.main(verbosity=2)
