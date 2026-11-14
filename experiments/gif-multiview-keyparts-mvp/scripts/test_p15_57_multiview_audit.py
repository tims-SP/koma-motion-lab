import json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-57-multiview-audit'
class ArcAudit(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-57-multiview-audit.json').read_text())
 def test_thirteen_angles(self):self.assertEqual(len(self.q['frames']),13)
 def test_expected_angle_coverage(self):self.assertEqual(self.q['sourceArcAngles'],[45,47.5,50,52.5,55,56.25,57.5,58.75,60,61.25,62.5,63.75,65])
 def test_zero_artistically_approved(self):self.assertEqual(self.q['independentlyPaintedKeyframesApproved'],0);self.assertFalse(self.q['fullArcArtistAcceptance'])
 def test_inbetween_is_not_identity_proof(self):
  x=[f for f in self.q['frames'] if f['kind']=='cross-view-role-inbetween']
  self.assertEqual(len(x),3);self.assertTrue(all(.97<f['alphaIoU']<.99 for f in x))
 def test_p0_identity_provenance_flag(self):self.assertFalse(self.q['sourceP0HeroSHA256Verified'])
 def test_45_original_preserved(self):self.assertTrue(self.q['registeredFull45DegreeOriginalPreserved'])
 def test_absolute_yaw_unverified(self):self.assertFalse(self.q['absoluteYaw65Verified'])
 def test_identity_not_approved(self):self.assertFalse(self.q['identityContinuityApproved'])
 def test_formal_keyframe_not_approved(self):self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_preview_assets(self):
  for f in self.q['frames']:
   if 'preview' in f:self.assertTrue((D/f['preview']).exists())
  self.assertTrue((D/'p15-56-current-candidate.png').exists())
 def test_html_reports_limits(self):
  h=(D/'index.html').read_text();self.assertIn('不能证明眼睛',h);self.assertIn('绝对 yaw 未校准',h)
if __name__=='__main__':unittest.main()
