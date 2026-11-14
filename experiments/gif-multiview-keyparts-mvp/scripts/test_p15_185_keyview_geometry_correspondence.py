#!/usr/bin/env python3
"""P15-185 three-key control-point continuity and visual acceptance gates."""
import json
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-185-keyview-geometry-correspondence-qa.json'
OUT=ROOT/'private-assets/exports/p15-185-keyview-geometry-correspondence'
class KeyviewGeometryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads(E.read_text())
 def test_artifacts(self):
  self.assertEqual(len(self.q['angles']),13)
  for mode in ('linear','pchip'):
   files=list((OUT/mode).glob('yaw*.png'))
   self.assertEqual(len(files),13)
   for path in files:
    with Image.open(path) as img:self.assertEqual(img.size,(443,443))
 def test_pchip_control_derivative_is_smoother(self):
  a=self.q['metrics']
  self.assertTrue(self.q['gate']['derivativeJumpReduced'])
  self.assertLess(a['pchip']['middleKeyDerivativeJump'],a['linear']['middleKeyDerivativeJump'])
  self.assertGreater(a['pchip']['maxAdjacentCurveRMSStep'],a['linear']['maxAdjacentCurveRMSStep'])
 def test_exact_keys_and_connected_strand(self):
  for data in self.q['metrics'].values():
   self.assertTrue(data['allNativeKeysExact'])
   self.assertTrue(data['allDeepBodyExact'])
   self.assertTrue(data['singleConnectedStrand'])
   self.assertTrue(data['freeTipPreserved'])
 def test_pchip_hermite_preserves_control_points(self):
  import sys
  sys.path.insert(0,str(ROOT/'scripts'))
  from p15_185_keyview_geometry_correspondence import pchip_three
  vals=np.array([[1.,8.],[5.,3.],[3.,9.]])
  for a,expected in ((90.,vals[0]),(112.5,vals[1]),(135.,vals[2])):
   np.testing.assert_allclose(pchip_three(vals,a),expected,atol=1e-8)
  # At the middle key an extremum has zero derivative instead of overshooting.
  y=np.array([0.,4.,0.])
  self.assertLessEqual(float(pchip_three(y,112.5-.01)),4.)
  self.assertLessEqual(float(pchip_three(y,112.5+.01)),4.)
 def test_temporal_quality_gate_is_independent_of_geometric_continuity(self):
  self.assertFalse(self.q['gate']['pchipLocalTemporalBeatsLinear'])
  self.assertFalse(self.q['gate']['pchipLocalTemporalBeatsDIS'])
  self.assertFalse(self.q['gate']['visualAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
