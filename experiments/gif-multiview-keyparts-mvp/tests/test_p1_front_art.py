#!/usr/bin/env python3
"""Regression tests on real recovered P0 artwork; no fixture is treated as art approval."""
import json
import pathlib
import sys
import unittest

import cv2
import numpy as np
from PIL import Image

BASE=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/"scripts"))
from p1_front_semantic import DEPTH, SEMANTIC, load, ownership, make_ellipse
from qa_p1_front import run as qa_run

PRIVATE=BASE/"private-assets"
P1=PRIVATE/"p1-front"


@unittest.skipUnless((P1/"parts.json").is_file() and
                     (PRIVATE/"recovered-review/frames/head_8/yaw000_whole.png").is_file(),
                     "P0 raw artwork is stored in the private asset folder")
class P1ArtworkIntegration(unittest.TestCase):
    def test_real_source_provenance(self):
        from p1_front_semantic import sha
        manifest=json.loads((P1/"parts.json").read_text())
        self.assertEqual(manifest["characterId"],"p0_character_001")
        self.assertEqual(len(manifest["parts"]),13)
        self.assertEqual(manifest["canvas"],[1024,1024])
        for p in manifest["parts"]:
            self.assertEqual(p["sourceGifSha256"],
                             sha(PRIVATE/"whole/head-turn-8view.gif"))
            self.assertEqual(p["frameSha256"],sha(PRIVATE/p["path"]))

    def test_eye_identity_and_fringe_exclusivity(self):
        original=load(PRIVATE/"recovered-review/frames/head_8/yaw000_whole.png")
        owner,_=ownership(PRIVATE,original)
        for center in ((190,196),(271,196)):
            core=make_ellipse(center,(19,16))
            self.assertEqual(int((core&(owner==DEPTH["hair.front"])).sum()),0)
        self.assertGreater(int((owner==DEPTH["eye.near"]).sum()),1000)
        self.assertGreater(int((owner==DEPTH["eye.far"]).sum()),1000)

    def test_soft_alpha_and_mesh_anchors(self):
        manifest=json.loads((P1/"parts.json").read_text())
        for p in manifest["parts"]:
            img=np.array(Image.open(PRIVATE/p["path"]).convert("RGBA"))
            self.assertEqual(img.shape,(1024,1024,4))
            self.assertGreater(np.count_nonzero((img[:,:,3]>0)&(img[:,:,3]<255)),0)
            self.assertEqual(len(p["mesh"]["vertexIds"]),49)
            self.assertEqual(len(p["mesh"]["triangles"]),72)
            self.assertGreaterEqual(len(p["anchors"]),5)
            self.assertFalse(p["semanticReviewed"])
            self.assertFalse(p["visualReviewed"])

    def test_static_and_eye_motion(self):
        dest=P1/"integration-qa.json"
        result=qa_run(PRIVATE,dest)
        self.assertEqual(result["status"],"PASS_STRUCTURAL_ENGINEERING")
        self.assertEqual(result["failed"],0)
        self.assertGreaterEqual(result["measures"]["staticSilhouetteIoU"],0.9999)
        self.assertEqual(result["measures"]["eyeMoveNewTransparentHoles"],0)
        self.assertEqual(result["measures"]["farEyeMaxChannelDifference"],0)


if __name__=="__main__":
    unittest.main(verbosity=2)
