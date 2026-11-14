#!/usr/bin/env python3
"""Validate external SAM3 annotation hashes, source pixel identity, and review evidence."""
import unittest,hashlib,json
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
A=R/'private-assets';D=A/'exports/p15-94-sam3-yaw060'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class SAM3(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((R/'evidence/p15-94-sam3-provider-qa.json').read_text())
  cls.b=json.loads((R/'evidence/p15-94-browser-qa.json').read_text())
 def test_actual_model(self):self.assertEqual(self.q['status'],'MODEL_RETURNED')
 def test_source(self):self.assertEqual(self.q['sourceSHA256'],sha(A/'exports/p15-92-angle-keyart/yaw060-registered.png'))
 def test_annotations(self):
  self.assertEqual(len(self.q['outputs']),3)
  for out in self.q['outputs']:
   self.assertEqual(out['sha256'],sha(R/out['path']))
 def test_resized_masks(self):
  for i,entry in enumerate(self.q['segmentationValidation']['candidateMasks']):
   self.assertEqual(entry['maskSHA256'],sha(D/f'hair-candidate-{i}-alpha1024.png'))
   self.assertGreater(entry['alpha128Pixels'],50000)
 def test_original_colors(self):
  source=Image.open(A/'exports/p15-92-angle-keyart/yaw060-registered.png').convert('RGBA')
  for i,entry in enumerate(self.q['segmentationValidation']['candidateMasks']):
   with Image.open(D/f'hair-candidate-{i}-source-rgba.png') as art:
    self.assertEqual(source.convert('RGB').tobytes(),art.convert('RGB').tobytes())
    self.assertEqual(entry['rgbaSHA256'],sha(D/f'hair-candidate-{i}-source-rgba.png'))
 def test_mask_relationship(self):self.assertGreater(self.q['segmentationValidation']['frontWithinAllRatio'],0.95)
 def test_browser(self):
  self.assertEqual(self.b['status'],'PASS')
  self.assertEqual(len(self.b['checks']),4)
 def test_no_final_accept(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['segmentationValidation']['semanticMaskApproved'])
  self.assertFalse(self.q['segmentationValidation']['sourceUnderdrawingAvailable'])
if __name__=='__main__':unittest.main()
