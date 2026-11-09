#!/usr/bin/env python3
"""Independent P0 painted semantic ArtMesh ingestion invariants."""
import sys
import unittest
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import p15_holdout_import as ingest


class IndependentSemanticArtworkTests(unittest.TestCase):
    def test_part_contract_is_stable(self):
        contract=json.loads((ROOT/"metadata/p15-holdout-generation-contract.json").read_text())
        self.assertEqual(ingest.ROLES,tuple(contract["assetsPerView"]))
        self.assertEqual(len(ingest.ROLES),13)
        self.assertEqual(ingest.HOLDOUTS,(65.0,77.5))

    def test_recomposition_and_depth_are_exact(self):
        source=json.loads((ROOT/"private-assets/p5-see-through/mv-candidate/parts.json").read_text())
        values=ingest.canonical_depth(source)
        self.assertEqual(len(values),13)
        self.assertEqual(len(set(values.values())),13)
        alpha=Image.new("RGBA",ingest.CANVAS,(0,0,0,0))
        back=alpha.copy();front=alpha.copy()
        back.putpixel((30,40),(255,0,0,255))
        front.putpixel((30,40),(0,255,0,240))
        recomposed=ingest.composite([back,front])
        self.assertEqual(ingest.diff(recomposed,Image.alpha_composite(back,front)),
                         {"maximumAlphaDifference":0,"maximumVisibleRGBDifference":0,
                          "meanVisibleRGBDifference":0.0})
        self.assertNotEqual(recomposed.getpixel((30,40)),back.getpixel((30,40)))

    def test_rejects_non_rgba_source(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as path:
            p=Path(path)/"bad.png"
            Image.new("RGB",ingest.CANVAS,(0,0,0)).save(p)
            with self.assertRaisesRegex(ValueError,"native RGBA"):
                ingest.open_layer(p)

    def test_rejects_source_outside_workspace(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as path:
            folder=Path(path);(folder/"a").mkdir()
            (folder/"b.png").write_bytes(b"outside")
            with self.assertRaisesRegex(ValueError,"outside permitted"):
                ingest.contained(folder/"b.png",folder/"a")

    def test_real_p14_source_fixtures_validate_pixel_exact(self):
        for stem in ("67p5","72p5"):
            qa=json.loads((ROOT/("evidence/p15-06-importer-fixture-"+stem+".json")).read_text())
            self.assertEqual(qa["status"],"PASS_SOURCE_ARTMESH_INGEST_FIXTURE")
            self.assertEqual(qa["sourceKind"],"registered-p14-fixture")
            self.assertEqual(qa["partCount"],13)
            self.assertEqual(qa["recomposition"]["maximumAlphaDifference"],0)
            self.assertEqual(qa["recomposition"]["maximumVisibleRGBDifference"],0)
            self.assertEqual(len({r["semanticId"] for r in qa["semanticLayers"]}),13)
            self.assertEqual(len({r["path"] for r in qa["semanticLayers"]}),13)
            self.assertTrue(all(len(r["sourceSHA256"]) == 64 for r in qa["semanticLayers"]))


if __name__=="__main__":
    unittest.main()
