import hashlib
import json
import unittest
from pathlib import Path
from PIL import Image

R = Path(__file__).resolve().parents[1]
P = R / "private-assets"
D = P / "exports/p15-47-face-local-review"
Q = R / "evidence/p15-47-face-local-qa.json"
I = R / "evidence/p15-47-inference-qa.json"

class FaceLocalQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q = json.loads(Q.read_text())
        cls.inference = json.loads(I.read_text())

    def test_inference_records_quota_rejection(self):
        self.assertEqual(self.inference["status"], "INFERENCE_REJECTED_OR_FAILED")
        self.assertIn("ZeroGPU quota exceeded", self.inference["error"])

    def test_no_false_generation_success(self):
        self.assertNotIn("outputSHA256", self.inference)
        self.assertEqual(self.q["modelOutput"], "P15-45 seed 65445; not a new inference")

    def test_source_byte_hash(self):
        p = P / "p15-38-p0-registered-arc/yaw65/composite.png"
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), self.q["sourceSHA256"])

    def test_original_model_image_hash(self):
        p = P / "exports/p15-45-qwen21-controlnet-candidate.png"
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), self.q["modelOutputSHA256"])

    def test_composite_file_hash(self):
        p = D / "face-local-engineering-composite.png"
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), self.q["compositeSHA256"])

    def test_mask_zero_keeps_exact_rgba(self):
        src = Image.open(P / "p15-38-p0-registered-arc/yaw65/composite.png").convert("RGBA")
        comp = Image.open(D / "face-local-engineering-composite.png").convert("RGBA")
        mask = Image.open(P / "exports/p15-46-anchor-guides/face-mask-narrow-65.png").convert("L")
        for sv, cv, mv in zip(src.getdata(), comp.getdata(), mask.getdata()):
            if mv == 0:
                self.assertEqual(sv, cv)

    def test_alpha_is_unmodified_exactly(self):
        src = Image.open(P / "p15-38-p0-registered-arc/yaw65/composite.png").getchannel("A")
        comp = Image.open(D / "face-local-engineering-composite.png").getchannel("A")
        self.assertEqual(src.tobytes(), comp.tobytes())

    def test_rejected_art(self):
        self.assertFalse(self.q["pose65Accepted"])
        self.assertFalse(self.q["identityAccepted"])
        self.assertFalse(self.q["formalArtMeshModified"])

    def test_review_html_assets(self):
        html = (D / "index.html").read_text()
        for name in ["registered-65.png", "original-model-output.png", "face-local-engineering-composite.png",
                     "narrow-mask-65.png", "geometry-guide-65.png", "face-local-difference.png"]:
            self.assertIn('src="' + name + '"', html)
            self.assertTrue((D / name).is_file())

if __name__ == "__main__":
    unittest.main()
