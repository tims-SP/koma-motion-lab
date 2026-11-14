#!/usr/bin/env python3
"""P15-197 root-relative pose versus source-shape validation."""
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-197-local-shape-registration-qa.json'
OUT=ROOT/'private-assets/exports/p15-197-local-shape-registration'
class NativeShapeRegistrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_native_source_landmarks_hashed_and_root_relative(self):
  self.assertEqual(set(self.q['source']),{'90.0','112.5','135.0'})
  for row in self.q['source'].values():
   self.assertEqual(len(row['sourceHash']),64)
   self.assertEqual(len(row['rootRelativeLandmarks']),5)
   self.assertEqual(row['rootRelativeLandmarks'][0],[0,0])
   self.assertGreater(row['rootToTipDistancePixels'],20)
 def test_all_registration_methods_and_comparisons(self):
  for name in ('90->112.5','135->112.5','90->135'):
   self.assertEqual(set(self.q['comparisons'][name]),{'translation','rigid','similarity','affine'})
   for mode,data in self.q['comparisons'][name].items():
    self.assertEqual(len(data['perLandmarkResidualPixels']),5)
    self.assertEqual(len(data['matrix']),(2))
    self.assertGreater(data['determinant'],0)
 def test_affine_improves_overlap_but_not_heldout_tip(self):
  for name in ('90->112.5','135->112.5'):
   cases=self.q['comparisons'][name]
   self.assertGreater(cases['affine']['maskIoU'],cases['translation']['maskIoU'])
   self.assertLess(cases['affine']['maskIoU'],.75)
   self.assertGreater(cases['affine']['heldOutTipErrorPixels'],5)
  self.assertFalse(self.q['gate']['affineExplainsMiddleViewShape'])
 def test_review_rendered(self):
  self.assertTrue((OUT/'index.html').exists())
  with Image.open(OUT/'registration-comparison.jpg') as im:
   self.assertEqual(im.size,(1840,680))
 def test_no_source_or_production_changes(self):
  self.assertFalse(self.q['sourceAssetsModified'])
  self.assertFalse(self.q['productionRendererUpdated'])
  self.assertFalse(self.q['visualAccepted'])
  self.assertFalse(self.q['gate']['productionApproved'])
  self.assertFalse(self.q['gate']['passes'])
if __name__=='__main__':unittest.main()
