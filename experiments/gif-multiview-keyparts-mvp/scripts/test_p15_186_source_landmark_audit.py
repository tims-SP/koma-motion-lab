#!/usr/bin/env python3
import json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/p15-186-source-landmark-audit-qa.json'
OUT=ROOT/'private-assets/exports/p15-186-source-landmark-audit'
class SourceLandmarkAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads(E.read_text())
 def test_three_source_views_and_preview(self):
  self.assertEqual(self.q['sourceAngles'],[90.0,112.5,135.0])
  self.assertTrue((OUT/'index.html').is_file())
  self.assertTrue((OUT/'source-landmark-overlay.jpg').is_file())
  with Image.open(OUT/'source-landmark-overlay.jpg') as im:self.assertEqual(im.size,(1080,1140))
 def test_source_owned_masks_and_skeleton_endpoints(self):
  for angle,view in self.q['sourceGeometry'].items():
   self.assertTrue(view['sourcePairRecompositionExact'])
   self.assertEqual(view['skeleton']['endpointCount'],2)
   self.assertGreater(view['skeleton']['orderedPathPixels'],50)
   self.assertGreater(view['skeletonRadiusWidth']['median'],0)
   self.assertGreater(view['skeletonRadiusWidth']['p90'],view['skeletonRadiusWidth']['p10'])
   self.assertEqual(len(view['orderedRootToTipLandmarks']),11)
 def test_legacy_curve_is_a_clipped_boundary_not_centerline(self):
  self.assertTrue(self.q['legacyCurveUsesCropBoundaryInsteadOfFullSilhouette'])
  for view in self.q['sourceGeometry'].values():
   self.assertEqual(view['legacyCropBoundaryY'],54)
   self.assertEqual(view['legacyCurvePointsInsideFullSourceMaskRatio'],1.0)
   self.assertAlmostEqual(view['legacyCurveMeanDistanceTransformRadius'],1.0,places=2)
 def test_cross_view_geometry_mismatch_is_quantified(self):
  pair=self.q['pairwiseCorrespondence']
  self.assertGreater(pair['90-112.5']['endpointAlignedLandmarkRMS'],20)
  self.assertGreater(pair['112.5-135']['endpointAlignedLandmarkRMS'],8)
  self.assertGreater(pair['90-112.5']['widthProfileRMS'],2)
  self.assertFalse(self.q['gate']['semanticCrossViewCorrespondenceEstablished'])
  self.assertFalse(self.q['gate']['productionGeometryApproved'])
  self.assertFalse(self.q['gate']['passes'])
 def test_no_production_asset_was_changed(self):
  self.assertFalse(self.q['productionRendererUpdated'])
  self.assertFalse(self.q['visualAccepted'])
if __name__=='__main__':unittest.main()
