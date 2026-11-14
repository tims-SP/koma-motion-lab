#!/usr/bin/env python3
"""Independent generated keyview ArtMesh, source raster and underpainting tests."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parents[1]
PRIVATE=HERE/"private-assets"
sys.path.insert(0,str(HERE/"scripts"))
import p15_generated_semantics as parts
import p15_06_generated_acceptance as gate
import p15_inpainted_underpaint as inpaint


class P15GeneratedArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qa=json.loads((HERE/"evidence/p15-06-generated-keyviews-qa.json").read_text())

    def test_independently_painted_source_views_registered(self):
        self.assertEqual(self.qa["candidateViewCount"],2)
        self.assertEqual(self.qa["registeredSemanticRGBA"],26)
        self.assertEqual([x["angle"] for x in self.qa["generatedIndependentCandidateViews"]],[65.0,77.5])
        self.assertEqual([x["sourceView"] for x in self.qa["generatedIndependentCandidateViews"]],[45,90])
        self.assertEqual(self.qa["sourceExactRecompositions"],2)
        self.assertEqual(self.qa["formalArtAcceptance"],0)

    def test_source_png_and_matte_are_native_rgba(self):
        for e in self.qa["generatedIndependentCandidateViews"]:
            art=gate.check_sha(gate.assert_source_path(e["originalPainting"]["path"]),e["originalPainting"]["sha256"])
            matte=gate.check_sha(gate.assert_source_path(e["transparentPainting"]["path"]),e["transparentPainting"]["sha256"])
            with Image.open(art) as im:
                self.assertEqual(im.size,(1024,1024))
                self.assertEqual(im.mode,"RGB")
            with Image.open(matte) as im:
                self.assertEqual(im.size,(1024,1024))
                self.assertEqual(im.mode,"RGBA")
                alpha=np.asarray(im.getchannel("A"))
                self.assertGreater(int(((alpha>0)&(alpha<255)).sum()),3000)

    def test_semantic_ownership_recomposition_matches_painted_source(self):
        for key in ("yaw065","yaw077p5"):
            qa=json.loads((PRIVATE/("p15-independent-candidates/"+key+"-artmesh/qa.json")).read_text())
            self.assertEqual(qa["semanticPartCount"],13)
            self.assertEqual(qa["alphaRecompositionMaxDifference"],0)
            self.assertEqual(qa["rgbRecompositionMaxDifference"],0)
            self.assertGreater(qa["nearEarCandidateSkinPixels"],0)
            self.assertGreater(next(x["visiblePixels"] for x in qa["semanticLayerRecords"]
                if x["semanticId"]=="ear.near"),500)
            self.assertGreater(qa["singleAhogeCandidatePixels"],500)
            self.assertEqual(len({p["path"] for p in qa["semanticLayerRecords"]}),13)
            self.assertEqual(len({p["semanticId"] for p in qa["semanticLayerRecords"]}),13)

    def test_ahoge_and_ear_from_source_image(self):
        for angle,key in ((65.0,"yaw065"),(77.5,"yaw077p5")):
            with Image.open(PRIVATE/("p15-independent-candidates/"+key+"-source-rgba.png")) as im:
                pix=np.asarray(im.convert("RGBA"))
            tip=parts.candidate_ahoge(pix)
            ear=parts.candidate_ear(pix,angle)
            self.assertGreater(int(tip.sum()),1000)
            self.assertGreater(int(ear.sum()),0)
            self.assertEqual(int((ear&tip).sum()),0)

    def test_hidden_inpaint_and_original_visible_raster_identical(self):
        datum=self.qa["seeThroughBackHairAndSkin"]
        self.assertEqual(datum["targetAngle"],77.5)
        self.assertEqual(datum["sourceResolution"],[768,768])
        self.assertGreater(datum["hiddenInpaintedPixels"],50000)
        self.assertEqual(datum["resultRGBAExactRecomposition"],{"maxAlphaDifference":0,"maxRGBDifferenceOnSource":0})
        under=json.loads((PRIVATE/"p15-independent-candidates/yaw077p5-inpainted/qa.json").read_text())
        self.assertEqual(under["visiblePixelExactAlphaMax"],0)
        self.assertEqual(under["visiblePixelExactRGBMax"],0)
        self.assertEqual(under["nativeSemanticLayers"],13)
        self.assertEqual(sum(x["inpaintedHiddenPixels"] for x in under["hiddenSourceRoles"]),under["totalHiddenPaintedPixels"])

    def test_browser_source_sha_and_live_captures(self):
        browser=self.qa["browserReview"]
        self.assertEqual(browser["reviewScreenshots"],8)
        self.assertEqual(browser["sourceImagesHashVerified"],32)
        self.assertEqual(browser["javascriptErrors"],0)
        self.assertEqual(browser["failedRequests"],0)
        data=json.loads((PRIVATE/"p15-independent-candidates/browser/qa.json").read_text())
        self.assertEqual(data["screenshotCount"],8)
        for sample in data["samples"]:
            image=(HERE/sample["path"]).resolve()
            self.assertTrue(image.is_relative_to(PRIVATE.resolve()))
            self.assertEqual(gate.sha(image),sample["sha256"])


if __name__=="__main__":
    unittest.main()
