#!/usr/bin/env python3
import hashlib
import json
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"evidence/p15-14-existing-psd-mapping-qa.json"
PRIVATE=ROOT/"private-assets"

class P15PSDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(DATA.read_text())
    def test_sources_and_roles(self):
        self.assertEqual(len(self.report["roles"]),13)
        self.assertEqual(len(self.report["sources"]),3)
        self.assertEqual(sum(s["nativeLayerCount"] for s in self.report["sources"]),39)
    def test_native_layer_hashes(self):
        for source in self.report["sources"]:
            self.assertEqual(len(source["nativeLayerEntries"]),13)
            for layer in source["nativeLayerEntries"]:
                if "path" not in layer:continue
                path=PRIVATE/layer["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),layer["sha256"])
    def test_psd_signatures_and_composites(self):
        for source in self.report["sources"]:
            self.assertEqual((PRIVATE/source["source"]).read_bytes()[:4],b"8BPS")
            with Image.open(PRIVATE/source["compositePath"]) as img:
                self.assertEqual(img.size,(768,768))
            self.assertGreater(source["underpaintCandidateCoveredPixelInstances"],0)
    def test_do_not_auto_accept_underpaint(self):
        self.assertFalse(self.report["directRoleAcceptance"])
        self.assertFalse(self.report["layerSplitAccepted"])
        self.assertFalse(self.report["hiddenRegionArtAcceptance"])
        self.assertEqual(self.report["artmeshIndependentLayersAccepted"],0)
        self.assertTrue(any(x["status"]=="SPLIT_OR_IDENTITY_REVIEW_REQUIRED"
                            for s in self.report["sources"] for x in s["nativeLayerEntries"]))

if __name__=="__main__":unittest.main()
