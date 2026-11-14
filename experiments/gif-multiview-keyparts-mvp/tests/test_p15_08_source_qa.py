"""P15-08 independently generated pose source and alpha lineage regression."""
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
import p15_08_pose_qa as qa


class P15EightSourceQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=json.loads((ROOT/"evidence/p15-08-source-candidate-qa.json").read_text())

    def test_unique_p0_source_identity_and_canvas(self):
        self.assertEqual(self.record["characterId"],"p0_character_001")
        self.assertEqual(self.record["targetAngle"],55.)
        for item in self.record["registeredSourceViews"].values():
            f=qa.PRIVATE/item["path"]
            self.assertEqual(qa.sha(f),item["sha256"])
            self.assertEqual(item["canvas"],[1024,1024])

    def test_two_candidates_source_and_rgba_sha(self):
        self.assertEqual(len(self.record["candidateRecords"]),2)
        for name,item in self.record["candidateRecords"].items():
            self.assertEqual(qa.sha(qa.PRIVATE/item["painting"]["path"]),item["painting"]["sha256"])
            self.assertEqual(qa.sha(qa.PRIVATE/item["mattePath"]),item["matteSHA256"])
            self.assertGreater(item["matteForegroundPixels"],200000)
            self.assertGreater(item["mattePartialAlphaPixels"],3000)

    def test_hairclip_physical_side_calibration(self):
        reference_x=self.record["hairclipValidation"]["original45ClipCenter"][0]
        self.assertGreater(reference_x,600.)
        self.assertFalse(self.record["hairclipValidation"]["sideProfile65ClipVisible"])
        for item in self.record["candidateRecords"].values():
            self.assertTrue(item["painting"]["goldClip"]["present"])
            self.assertLess(item["painting"]["goldClip"]["center"][0],512.)
            self.assertEqual(item["physicalHairclipCheck"],"REWORK_REQUIRED")

    def test_source_candidate_admission_gate(self):
        self.assertEqual(self.record["status"],"P15_08_CANDIDATE_SOURCE_REGISTERED_POSE_REWORK")
        self.assertFalse(self.record["originalHeroSourceVerified"])
        self.assertEqual(self.record["semanticIndependent55LayersAccepted"],0)
        self.assertEqual(self.record["formalArtAcceptance"],"PENDING_ANATOMICAL_VIEW_CORRESPONDENCE")

    def test_browser_real_image_capture(self):
        browser=qa.PRIVATE/"p15-08-yaw055/browser/qa.json"
        self.assertTrue(browser.is_file())
        data=json.loads(browser.read_text())
        self.assertEqual(data["status"],"SOURCE_IMAGES_AND_ALPHA_GALLERY_PASS")
        self.assertEqual(data["imageLoads"],10)
        self.assertEqual(data["screenshotCount"],2)
        self.assertEqual(data["pageErrors"],[])
        self.assertEqual(data["failedRequests"],[])
        for frame in data["captures"]:
            image=ROOT/frame["capturedPath"]
            self.assertEqual(qa.sha(image),frame["sha256"])


if __name__=="__main__":
    unittest.main()
