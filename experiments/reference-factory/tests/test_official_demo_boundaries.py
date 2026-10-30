"""Offline boundary tests for the CORE-023 Task C official-demo runner.

No network calls, no gradio_client import, no inference. These tests only
exercise the pure parser/guard helpers of try_official_decomposition.
"""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import try_official_decomposition as tod  # noqa: E402


class BoundaryTests(unittest.TestCase):
    def test_only_official_space_allowed(self):
        self.assertEqual(tod.validate_space_url(tod.DEFAULT_SPACE_URL),
                         tod.DEFAULT_SPACE_URL)
        for bad in ("https://evil.example.com",
                    "http://24yearsold-see-through-demo.hf.space",
                    tod.DEFAULT_SPACE_URL + "/extra",
                    ""):
            with self.assertRaises(tod.BoundaryError):
                tod.validate_space_url(bad)

    def test_source_hash_must_match_pinned_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "img.png"
            p.write_bytes(b"not the pinned image")
            with self.assertRaises(tod.BoundaryError):
                tod.check_source_hash(p)
            digest = hashlib.sha256(b"x").hexdigest()
            p.write_bytes(b"x")
            self.assertEqual(tod.check_source_hash(p, digest), digest)

    def test_no_hash_mismatch_override_option(self):
        source = Path(tod.__file__).read_text()
        self.assertNotIn("allow-source-hash-mismatch", source)
        self.assertNotIn("allow_source_hash_mismatch", source)

    def test_client_kwargs_are_explicitly_anonymous(self):
        kwargs = tod.client_kwargs(tod.DEFAULT_SPACE_URL, Path("/tmp/out"))
        self.assertIs(kwargs["token"], False)
        self.assertFalse(kwargs["verbose"])
        with self.assertRaises(tod.BoundaryError):
            tod.client_kwargs("https://elsewhere.example", Path("/tmp/out"))

    def test_runner_never_resolves_tokens_implicitly(self):
        source = Path(tod.__file__).read_text()
        self.assertIn('os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"', source)
        self.assertIn("token=kwargs[\"token\"]", source)


if __name__ == "__main__":
    unittest.main()
