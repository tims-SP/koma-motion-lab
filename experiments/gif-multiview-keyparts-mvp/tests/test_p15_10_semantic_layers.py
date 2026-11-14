"""P15-10 source-registered semantic-layer geometry and browser regression."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
from p15_09_anchor_pose import ASSETS, DEST, sha
from p15_10_semantic_key55 import CHECK, OUTPUT, image_rgba
from p15_10_semantic_arc import OUT, STEPS, SOURCE65, QA65
from p8_semantic_occlusion import output_frame_id


class P15TenQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=json.loads(CHECK.read_text())
        cls.arc=json.loads((ROOT/"evidence/p15-10-semantic-arc-qa.json").read_text())
        cls.browser=json.loads((ASSETS/"p15-10-semantic-pose/browser/qa.json").read_text())

    def test_character_and_view_source_hashes(self):
        self.assertEqual(self.key["characterId"],"p0_character_001")
        self.assertEqual(self.key["P5Pose55SHA256"],
                         sha(DEST/"yaw055-p5-anchor-reference.png"))
        self.assertEqual(self.arc["source65SHA256"],sha(SOURCE65))
        self.assertEqual(self.arc["roleCount"],13)
        roles=[x["semanticId"] for x in self.key["semanticLayers"]]
        self.assertEqual(roles,self.arc["roles"])
        self.assertEqual(len(set(roles)),13)

    def test_key55_rgba_canvas_and_lossless_semantic_partition(self):
        frame=image_rgba(DEST/"yaw055-p5-anchor-reference.png")
        total=np.zeros_like(frame,dtype=np.uint16)
        for role in self.key["semanticLayers"]:
            f=ASSETS/role["outputPath"]
            self.assertEqual(sha(f),role["sha256"])
            total+=image_rgba(f).astype(np.uint16)
        self.assertTrue(np.array_equal(total.astype(np.uint8),frame))
        self.assertTrue(self.key["pixelExactComposite"])
        self.assertGreater(self.key["farEyePixels"],1000)
        self.assertGreater(self.key["hairclipPixels"],1000)

    def test_input_keyframes_retained(self):
        self.assertTrue(np.array_equal(
            image_rgba(OUT/output_frame_id(55)),
            image_rgba(DEST/"yaw055-p5-anchor-reference.png")))
        self.assertTrue(np.array_equal(
            image_rgba(OUT/output_frame_id(65)),
            image_rgba(SOURCE65)))
        for row in self.arc["frames"]:
            self.assertEqual(sha(ASSETS/row["path"]),row["sha256"])

    def test_role_identity_depth_and_65_source_lineage(self):
        meta=json.loads(QA65.read_text())
        self.assertEqual(meta["characterId"],"p0_character_001")
        self.assertEqual([r["semanticId"] for r in meta["semanticLayers"]],
                         self.arc["roles"])
        for r in meta["semanticLayers"]:
            self.assertEqual(sha(ASSETS/r["path"]),r["sourceSHA256"])
            self.assertEqual(r["registeredCanvas"],[1024,1024])
        for row in self.arc["frames"]:
            d=ASSETS/row["partDirectory"]
            self.assertEqual(len(list(d.glob("*.png"))),13)
            for role in self.arc["roles"]:
                self.assertEqual(image_rgba(d/(role+".png")).shape,(1024,1024,4))

    def test_physical_eye_and_hairclip_visibility(self):
        eyes=[x["parts"]["eye.far"] for x in self.arc["frames"]]
        clips=[x["parts"]["hair.clip.cross_gold"] for x in self.arc["frames"]]
        near=[x["parts"]["eye.near"] for x in self.arc["frames"]]
        self.assertGreater(eyes[0],1000)
        self.assertEqual(eyes[-1],0)
        self.assertEqual(clips[-1],0)
        self.assertTrue(all(x>0 for x in near))
        self.assertTrue(self.arc["source55FarEyeVisible"])
        self.assertTrue(self.arc["source65FarEyeHidden"])
        self.assertTrue(self.arc["source65HairclipHidden"])

    def test_image_continuity_report_and_art_source_scope(self):
        self.assertEqual(len(self.arc["frames"]),len(STEPS))
        self.assertEqual(len(self.arc["transition"]),len(STEPS)-1)
        for item in self.arc["transition"]:
            self.assertGreater(item["semanticAlphaIoU"],0.60)
            self.assertLessEqual(item["semanticAlphaIoU"],1.0)
        self.assertEqual(self.arc["renderStatus"],"ROLE_LOCAL_ARTMESH_FRAMES_REGISTERED")
        self.assertIn("PENDING",self.arc["artisticStatus"])

    def test_chromium_sources_and_capture_hashes(self):
        data=self.browser
        self.assertEqual(data["status"],"INTERACTIVE_ARTMESH_HTML_VERIFIED")
        self.assertEqual(data["screenshotCount"],8)
        self.assertEqual(data["imageLoads"],32)
        self.assertEqual(data["javascriptErrors"],[])
        self.assertEqual(data["failedRequests"],[])
        for item in data["screenshots"]:
            self.assertEqual(item["sourceCount"],4)
            self.assertEqual(sha(ROOT/item["path"]),item["sha256"])

if __name__=="__main__":
    unittest.main()
