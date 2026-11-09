#!/usr/bin/env python3
"""Unit regression of P14 file provenance before touching source assets."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "scripts/verify_p14_evidence.py"
spec = importlib.util.spec_from_file_location("p14_evidence", FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class P14EvidenceUnitTests(unittest.TestCase):
    def test_digest_matches_content(self):
        with tempfile.TemporaryDirectory() as td:
            file = Path(td) / "test.png"
            file.write_bytes(b"p0-character")
            import hashlib
            self.assertEqual(module.digest(file), hashlib.sha256(b"p0-character").hexdigest())

    def test_content_hash_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            file = root / "source.png"
            file.write_bytes(b"verified-source")
            entry = {"path": "source.png", "sha256": module.digest(file)}
            self.assertEqual(module.verify_file(root, entry), file)
            file.write_bytes(b"changed-source")
            with self.assertRaisesRegex(AssertionError, "hash mismatch"):
                module.verify_file(root, entry)

    def test_path_containment(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "assets"
            root.mkdir()
            other = Path(td) / "outside.txt"
            other.write_bytes(b"x")
            with self.assertRaisesRegex(AssertionError, "outside asset root"):
                module.verify_file(root.resolve(), {
                    "path": "../outside.txt", "sha256": module.digest(other)
                })

    def test_expected_roles_stable(self):
        self.assertEqual(len(module.ROLES), 13)
        self.assertEqual(len(set(module.ROLES)), 13)
        self.assertEqual(module.ANGLES, (67.5, 72.5))


if __name__ == "__main__":
    unittest.main()
