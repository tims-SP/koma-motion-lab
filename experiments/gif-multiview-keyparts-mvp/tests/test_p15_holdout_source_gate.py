#!/usr/bin/env python3
"""P15-06 approved P0 identity and held-out artwork source gate checks."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import p15_holdout_source_gate as gate


class P15HoldoutSourceGateTests(unittest.TestCase):
    def test_canonical_character_and_view_count(self):
        self.assertEqual(gate.CHARACTER,"p0_character_001")
        self.assertEqual(gate.HOLDOUTS,(65.0,77.5))
        self.assertEqual(gate.SOURCE_ANGLES,(0,45,90))
        self.assertEqual(len(gate.ROLES),13)
        self.assertEqual(len(set(gate.ROLES)),13)

    def test_sha_checks_content(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"hero.png"
            path.write_bytes(b"hero canonical source")
            original=gate.sha(path)
            path.write_bytes(b"other generated source")
            self.assertNotEqual(original,gate.sha(path))

    def test_holdouts_are_distinct_from_source_keys(self):
        self.assertTrue(set(gate.HOLDOUTS).isdisjoint(gate.SOURCE_ANGLES))
        self.assertNotEqual(gate.HOLDOUTS[0],gate.HOLDOUTS[1])

    def test_provenance_contract_is_independent_art(self):
        base=Path(__file__).resolve().parents[1]
        contract=json.loads((base/"metadata/p15-holdout-generation-contract.json").read_text())
        self.assertEqual(contract["characterId"],gate.CHARACTER)
        self.assertEqual(contract["renderRequirements"]["sourceRole"],"INDEPENDENT_AUTHORED_2D_KEYFRAME")
        self.assertEqual(contract["canvas"],[1024,1024])
        self.assertEqual(contract["holdingYawAngles"],list(gate.HOLDOUTS))
        self.assertEqual(len(contract["assetsPerView"]),13)
        self.assertEqual(contract["sourceOriginalViews"][0]["yaw"],0)
        self.assertEqual(contract["sourceOriginalViews"][-1]["yaw"],90)

    def test_hero_gate_uses_exact_expected_checksum(self):
        base=Path(__file__).resolve().parents[1]
        report=json.loads((base/"evidence/p15-06-source-readiness.json").read_text())
        contract=json.loads((base/"metadata/p15-holdout-generation-contract.json").read_text())
        self.assertEqual(report["approvedIdentityExpectedSHA256"],
                         contract["originalHeroExpectedSHA256"])
        matching=[c for c in report["approvedHeroCandidateInventory"]
                  if c["matchesApprovedHeroSHA256"]]
        self.assertEqual(report["approvedHeroDirectSourceSHA256Verified"],bool(matching))
        self.assertEqual(report["plannedIndependentSemanticAssets"],26)
        self.assertEqual(report["independentlyPaintedHoldoutAssetsAccepted"],0)


if __name__=="__main__":
    unittest.main()
