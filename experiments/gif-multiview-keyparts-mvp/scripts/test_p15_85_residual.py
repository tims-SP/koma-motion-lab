import unittest,hashlib,json
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-85-outer-eye-seam'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class TestP1585(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-85-qa.json').read_text())
 def test_source(self):self.assertEqual(sha(P/'p15-84-clean-brow-inpaint/clean-hidden-face.png'),self.q['sourceUnderpaintSHA256'])
 def test_old_mask(self):self.assertEqual(sha(P/'p15-84-clean-brow-inpaint/mask-full.png'),self.q['oldMaskSHA256'])
 def test_sam3_mask(self):self.assertEqual(sha(P/'p15-81-image-layered/sam3-027-aligned-alpha.png'),self.q['samMaskSHA256'])
 def test_input(self):self.assertEqual(sha(D/'input-512.png'),self.q['inputSHA256'])
 def test_target_mask(self):self.assertEqual(sha(D/'mask-512.png'),self.q['maskSHA256'])
 def test_not_widen_old_mask(self):self.assertEqual(self.q['oldMaskOverlapPixels'],0)
 def test_small_region(self):self.assertEqual(self.q['maskPixelCount'],198)
 def test_mask_bbox(self):self.assertEqual(self.q['maskBBox'],[515,442,534,457])
 def test_real_infer(self):
  self.assertEqual(self.q['status'],'MODEL_RETURNED')
  self.assertGreater(self.q['modelBytes'],10000)
  self.assertEqual(sha(D/'model-512.png'),self.q['modelSHA256'])
 def test_candidate_sha(self):self.assertEqual(sha(D/'revised-hidden-face.png'),self.q['revisedUnderpaintSHA256'])
 def test_no_external_changes(self):self.assertEqual(self.q['changedOutsideMaskPixels'],0)
 def test_changed_pixels(self):self.assertEqual(self.q['changedInsideMaskPixels'],196)
 def test_zero_pose(self):self.assertEqual(self.q['frames']['0']['changedAgainstP1584'],0)
 def test_frame_sha(self):
  for dx in (0,9,18):self.assertEqual(sha(D/f'frame-{dx:02d}.png'),self.q['frames'][str(dx)]['sha256'])
 def test_no_holes(self):self.assertTrue(all(x['newTransparentHolesROI']==0 for x in self.q['frames'].values()))
 def test_visible_difference(self):
  self.assertEqual(self.q['visibleChangedPixelsMotion'],{'9':31,'18':31})
 def test_invisible_difference(self):
  self.assertEqual(self.q['invisibleRGBAChangedPixelsMotion'],{'9':19603,'18':19603})
 def test_visual_rejected(self):
  self.assertFalse(self.q['formalArtMeshAccepted']);self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertFalse(self.q['candidateAccepted'])
 def test_review_gate(self):self.assertIn('正式视觉门禁 FAIL',(D/'index.html').read_text())
if __name__=='__main__':unittest.main()
