"""Offline unit tests for CORE-023 Task B readiness probe (probe_decomposition.py).

No network, no installs, no downloads. Everything here runs on temp dirs only.
Run: python -m unittest discover -s experiments/reference-factory/tests -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import probe_decomposition as pd  # noqa: E402


class TestOutputLocation(unittest.TestCase):
    def test_default_output_dir_is_ordered_location(self):
        """Default output must be experiments/reference-factory/out/core023, not repo-root out/."""
        expected = ROOT / "out" / "core023"
        self.assertEqual(pd.DEFAULT_OUT_DIR, expected)
        self.assertNotEqual(
            pd.DEFAULT_OUT_DIR, pd.REPO_ROOT / "out" / "core023",
            "default output must not fall back to the repository-root out/",
        )

    def test_out_dir_is_injectable(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "custom" / "core023"
            rc = pd.main(["--out-dir", str(target), "--skip-network"])
            self.assertEqual(rc, 0)
            out = target / pd.OUT_JSON_NAME
            self.assertTrue(out.is_file())
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["output_path"], str(out))
            self.assertTrue(data["offline_mode"])


class TestWeightsGate(unittest.TestCase):
    def test_empty_directory_is_not_weights(self):
        with tempfile.TemporaryDirectory() as td:
            empty = Path(td) / "models"
            empty.mkdir()
            res = pd.assess_weights([empty])
            self.assertFalse(res["weights_complete"])
            self.assertNotEqual(res["status"], "PASS")
            self.assertIn("NOT loaded model weights", res["note"])

    def test_cloned_source_repo_is_not_weights(self):
        """A source checkout with .py files is not a checkpoint payload."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "see-through"
            (repo / "utils").mkdir(parents=True)
            (repo / "utils" / "inference_utils.py").write_text("x = 1\n", encoding="utf-8")
            (repo / "requirements.txt").write_text("torch\n", encoding="utf-8")
            res = pd.assess_weights([repo])
            self.assertFalse(res["weights_complete"])
            self.assertNotEqual(res["status"], "PASS")

    def test_actual_weight_file_counts(self):
        """Payload presence is recorded, but never as completeness or PASS."""
        with tempfile.TemporaryDirectory() as td:
            ck = Path(td) / "ck"
            ck.mkdir()
            (ck / "diffusion_pytorch_model.safetensors").write_bytes(b"0" * 64)
            res = pd.assess_weights([ck])
            self.assertTrue(res["checkpoint_payload_found"])
            self.assertFalse(res["weights_complete"])
            self.assertEqual(res["status"], "NOT_TESTED")
            self.assertNotEqual(res["status"], "PASS")

    def test_dummy_safetensors_cannot_enable_local_pass(self):
        """Readiness regression: a dummy .safetensors file must not unblock readiness."""
        with tempfile.TemporaryDirectory() as td:
            ck = Path(td) / "ck"
            ck.mkdir()
            (ck / "diffusion_pytorch_model.safetensors").write_bytes(b"0" * 64)
            weights = pd.assess_weights([ck])
            facts = {
                "torch": {"spec_found": True, "import_ok": True, "status": "PASS"},
                "gpu": {"status": "PASS", "note": "GPU device visible"},
                "weights": weights,
                "aka": {"status": "PASS", "note": "match"},
                "input_hash": {"status": "PASS", "note": "match", "input_hash_matches_manifest": True},
                "upstream": {"all_match": True},
            }
            res = pd.evaluate_local_readiness(facts)
            self.assertEqual(res["status"], "BLOCKED")
            self.assertTrue(any("integrity or load validation" in b or "NOT verified complete" in b
                                for b in res["blockers"]))


class TestReadinessGating(unittest.TestCase):
    """Hash mismatch must block readiness even when hardware probes look available."""

    def _facts(self):
        return {
            "torch": {"spec_found": True, "import_ok": True, "status": "PASS"},
            "gpu": {"status": "PASS", "note": "GPU device visible"},
            "weights": {"weights_complete": True, "note": "ok", "status": "PASS"},
            "aka": {"status": "PASS", "note": "match"},
            "input_hash": {"status": "PASS", "note": "match", "input_hash_matches_manifest": True},
            "upstream": {"all_match": True},
        }

    def test_all_good_is_pass(self):
        res = pd.evaluate_local_readiness(self._facts())
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["blockers"], [])

    def test_hash_mismatch_blocks_even_with_mocked_hardware(self):
        facts = self._facts()
        facts["input_hash"] = {
            "status": "FAIL",
            "note": "flattened input hash DIFFERS from recorded manifest hash",
            "input_hash_matches_manifest": False,
        }
        res = pd.evaluate_local_readiness(facts)
        self.assertEqual(res["status"], "BLOCKED")
        self.assertTrue(any("input hash gate failed" in b for b in res["blockers"]))

    def test_upstream_evidence_mismatch_blocks(self):
        facts = self._facts()
        facts["upstream"] = {"all_match": False}
        res = pd.evaluate_local_readiness(facts)
        self.assertEqual(res["status"], "BLOCKED")

    def test_torch_spec_alone_is_not_compatibility(self):
        facts = self._facts()
        facts["torch"] = {"spec_found": True, "import_ok": False, "status": "NOT_TESTED"}
        res = pd.evaluate_local_readiness(facts)
        self.assertEqual(res["status"], "BLOCKED")
        self.assertTrue(any("spec presence is not compatibility validation" in b for b in res["blockers"]))


class TestMetadataValidation(unittest.TestCase):
    def test_html_body_is_rejected(self):
        res = pd.parse_config_payload(b"<html><body>login</body></html>")
        self.assertFalse(res["ok"])
        self.assertIn("HTML", res["reason"])

    def test_non_json_body_is_rejected(self):
        res = pd.parse_config_payload(b"not json at all")
        self.assertFalse(res["ok"])

    def test_missing_dependency_metadata_is_rejected(self):
        res = pd.parse_config_payload(json.dumps({"api_prefix": "/gradio_api"}).encode())
        self.assertFalse(res["ok"])
        self.assertIn("dependencies", res["reason"])

    def test_dependencies_without_api_name_is_rejected(self):
        body = json.dumps({"dependencies": [{"id": 1}]}).encode()
        res = pd.parse_config_payload(body)
        self.assertFalse(res["ok"])

    def test_valid_config_is_accepted_and_auth_is_unknown(self):
        body = json.dumps({
            "api_prefix": "/gradio_api",
            "version": "6.12.0",
            "dependencies": [{"id": 0, "api_name": "inference"}],
        }).encode()
        res = pd.parse_config_payload(body)
        self.assertTrue(res["ok"])
        self.assertEqual(res["api_names"], ["inference"])
        auth = pd.extract_auth_status(res["config"])
        self.assertEqual(auth["status"], "UNKNOWN")
        self.assertEqual(auth["fields"], {})

    def test_offline_probe_makes_no_request(self):
        res = pd.probe_demo_config(offline=True)
        self.assertEqual(res["status"], "NOT_TESTED")
        self.assertFalse(res["attempted"])
        self.assertIsNone(res["http_status"])


class TestDecompositionStatus(unittest.TestCase):
    def test_actual_decomposition_remains_not_tested(self):
        with tempfile.TemporaryDirectory() as td:
            data = pd.build_report(Path(td), offline=True)
            self.assertEqual(data["M3_actual_decomposition"], "NOT_TESTED")
            self.assertEqual(data["ranking"], "NONE_ACCEPTED")
            self.assertEqual(data["production_approval"], "OPEN")


if __name__ == "__main__":
    unittest.main()
