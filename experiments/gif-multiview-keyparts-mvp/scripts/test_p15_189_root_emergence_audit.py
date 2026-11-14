#!/usr/bin/env python3
"""Regression tests for native/interpolated root-emergence continuity."""
import json,unittest,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-189-root-emergence-audit-qa.json'
OUT=ROOT/'private-assets/exports/p15-189-root-emergence-audit'
class RootEmergenceAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_thirteen_samples_and_review(self):
  self.assertEqual(len(self.q['renderAngles']),13)
  self.assertEqual(len(self.q['diagnostics']),13)
  self.assertTrue((OUT/'index.html').is_file())
  with Image.open(OUT/'13-yaw-root-contact.jpg') as img:
   self.assertEqual(img.size,(2730,225))
 def test_root_crossings_are_all_measurable(self):
  self.assertTrue(self.q['gate']['allCrossingsMeasured'])
  for d in self.q['diagnostics'].values():
   self.assertTrue(d['hasCrossing'])
   self.assertEqual(len(d['crossing']),2)
   self.assertEqual(len(d['tangent']),2)
   self.assertGreaterEqual(d['crownAlphaAtEmergence'],0)
 def test_source_keyviews_are_marked(self):
  for a in ('90','112.5','135'):
   self.assertTrue(self.q['diagnostics'][a]['nativeKeyframe'])
   self.assertGreater(self.q['diagnostics'][a]['sourceMedialRootToProposalPixels'],0)
  self.assertTrue(self.q['gate']['sourceKeysPresent'])
 def test_middle_key_discontinuity_is_explicit(self):
  left=self.q['middleKeyTransitions']['108.75-112.5']
  right=self.q['middleKeyTransitions']['112.5-116.25']
  self.assertGreater(left['crossingDisplacementPixels'],10)
  self.assertGreater(right['crossingDisplacementPixels'],5)
  self.assertGreater(left['rootColorSeamDelta'],20)
  self.assertGreater(right['rootColorSeamDelta'],20)
  self.assertFalse(self.q['gate']['middleKeyContinuityAccepted'])
 def test_production_and_artist_gate_unchanged(self):
  self.assertFalse(self.q['sourceImagesModified'])
  self.assertFalse(self.q['productionRendererUpdated'])
  self.assertFalse(self.q['visualAccepted'])
  self.assertFalse(self.q['gate']['sourceRootSemanticsVerified'])
  self.assertFalse(self.q['gate']['passes'])
if __name__=='__main__':unittest.main()
