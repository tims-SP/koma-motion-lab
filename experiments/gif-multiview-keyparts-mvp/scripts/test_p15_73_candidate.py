import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1]
D=R/'private-assets/exports/p15-73-interactive-sam'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Candidate(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-73-mask-extraction-qa.json').read_text())
 def test_source(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_real_sam_label(self):self.assertEqual(sha(D/'sam-mask-1.png'),self.q['samLabelSHA256'])
 def test_layer_sha(self):self.assertEqual(sha(D/'front-bangs-rgba.png'),self.q['hairLayerSHA256'])
 def test_layer_rgba_size(self):
  with Image.open(D/'front-bangs-rgba.png') as x:self.assertEqual((x.mode,x.size),('RGBA',(1024,1024)))
 def test_alpha_extent(self):
  a=Image.open(D/'front-bangs-rgba.png').getchannel('A')
  self.assertEqual(list(a.getbbox()),self.q['hairLayerAlphaBBox'])
  self.assertEqual(sum(v>0 for v in a.getdata()),self.q['hairLayerAlphaPixels'])
 def test_positive_and_negative_anchors(self):
  self.assertTrue(self.q['positiveAnchorPointsInMask'])
  self.assertTrue(self.q['negativeVerificationPointsOutsideMask'])
  self.assertTrue(self.q['goldHairpinAnchorOutside'])
  self.assertTrue(self.q['eyeAndCheekAnchorsOutside'])
 def test_original_pixel_perfect_decomposition_only(self):
  src=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  candidate=Image.open(D/'reconstruction-0px.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(src,candidate).getbbox())
  self.assertTrue(self.q['sourceReconstructionExact'])
 def test_actual_motion_composite_not_exact_original(self):
  src=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  frame=Image.open(D/'p15-73-composite-00.png').convert('RGBA')
  self.assertIsNotNone(ImageChops.difference(src,frame).getbbox())
  self.assertIsNotNone(self.q['p15_56CompositeDiffBBox'])
 def test_three_offsets(self):
  self.assertEqual(sorted(self.q['motionFrames']),['0','18','9'])
  for dx in (0,9,18):
   self.assertEqual(sha(D/f'p15-73-composite-{dx:02d}.png'),self.q['motionFrames'][str(dx)]['sha256'])
 def test_zero_holes_in_roi(self):
  self.assertTrue(all(f['alphaHoleBBox'] is None for f in self.q['motionFrames'].values()))
 def test_interactive_point_mask_rejected(self):self.assertEqual(self.q['uiPointPromptAttempt'],'FAILED_OVERSEGMENTED_HEAD_MASK')
 def test_no_formal_approval(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_html_discloses_limitation(self):
  h=(D/'index.html').read_text()
  self.assertIn('正式 ArtMesh 仍不准入',h)
  self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
