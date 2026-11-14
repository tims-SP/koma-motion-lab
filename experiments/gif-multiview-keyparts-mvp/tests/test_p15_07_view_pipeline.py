"""P15-07 ArtMesh, painted keyview, comparison-source and HTML regression."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"scripts"))
import p15_07_geometry_bridge as geometry
import p15_07_semantic_keyframes as semantic
import p15_07_review_qa as review

class P15ViewPipelineTests(unittest.TestCase):
    def test_painted_keyviews_registered_by_sha(self):
        sources,layers,roles,registry=semantic.source_registry()
        self.assertEqual(set(sources),{45.,65.,77.5,90.})
        self.assertEqual(len(roles),13)
        self.assertEqual(len(layers),52)
        self.assertEqual(len(set(roles)),13)
        self.assertEqual(set(registry),{"45.0","65.0","77.5","90.0"})

    def test_independent_geometry_reference_roles(self):
        # P15 independent views are the comparison targets for the P14
        # geometric benchmark, never the benchmark's renderer inputs.
        self.assertTrue(set(geometry.ART.values()).isdisjoint(geometry.HOLDOUT.values()))
        self.assertEqual(set(geometry.HOLDOUT),{65.,77.5})

    def test_semantic_flow_and_sdf_are_mask_bounded(self):
        aa=np.zeros((16,16,4),dtype=np.float32)
        bb=np.zeros_like(aa)
        aa[4:12,3:11,:3]=.4;aa[4:12,3:11,3]=1
        bb[4:12,5:13,:3]=.5;bb[4:12,5:13,3]=1
        for mode in ("ink-owner","ink-transition"):
            result=semantic.blend_painted_part(aa,bb,.5,mode)
            self.assertEqual(result.shape,aa.shape)
            self.assertGreater(float(result[8,8,3]),.8)
            self.assertEqual(float(result[0,0,3]),0.)
            self.assertTrue(np.isfinite(result).all())

    def test_full_37_frame_source_integrity(self):
        sources,_,_,_=semantic.source_registry()
        for name in ("p15-07-semantic-preview","p15-07-wholekey-preview"):
            root=semantic.PRIVATE/name
            obj=json.loads((root/"qa.json").read_text())
            frames=obj.get("renderedFrames",obj.get("frames"))
            self.assertEqual(len(frames),37)
            for yaw,source in sources.items():
                with Image.open(root/semantic.output_frame_id(yaw)) as output,Image.open(source) as origin:
                    self.assertTrue(np.array_equal(np.asarray(output),np.asarray(origin)))

    def test_browser_live_capture_and_registered_sources(self):
        f=semantic.PRIVATE/"p15-07-browser/qa.json"
        qa=json.loads(f.read_text())
        self.assertEqual(qa["status"],"HTML_INTERACTIVE_SOURCE_LOAD_PASS")
        self.assertEqual(qa["screenshotCount"],8)
        self.assertEqual(qa["verifiedSourceImageLoads"],28)
        self.assertFalse(qa["javascriptErrors"])
        self.assertFalse(qa["failedRequests"])
        for rec in qa["screenshots"]:
            sample=semantic.ROOT/rec["screenPath"]
            self.assertEqual(semantic.sha(sample),rec["sha256"])

    def test_visual_acceptance_remains_independent(self):
        audit=json.loads((ROOT/"evidence/p15-07-renderer-qa.json").read_text())
        self.assertEqual(audit["technicalGate"],"SOURCE_INTEGRITY_AND_BROWSER_PASS")
        self.assertEqual(audit["visualReview"]["artisticStatus"],"REWORK_REQUIRED")
        self.assertFalse(audit["identityHeroApprovedSha256Verified"])
        for val in audit["renderers"].values():
            self.assertEqual(val["frameCount"],37)
            self.assertEqual(val["sourceKeyviewsPixelExact"],[45.,65.,77.5,90.])
            self.assertEqual({s["yaw"] for s in val["paintedReferenceComparisons"]},{67.5,72.5})

if __name__=="__main__":
    unittest.main()
