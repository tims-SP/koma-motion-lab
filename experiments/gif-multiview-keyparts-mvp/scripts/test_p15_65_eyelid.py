import hashlib,json,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-65-eyelid-refinement'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Eyelid(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-65-eyelid-qa.json').read_text())
 def test_source_identity(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_underpaint_reused_unchanged(self):self.assertEqual(sha(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png'),self.q['reusedLaMaUnderpaintSHA256'])
 def test_previous_layer_unchanged(self):self.assertEqual(sha(R/'private-assets/exports/p15-64-semantic-eye/eye.near.tight-layer.png'),self.q['previousNearEyeLayerSHA256'])
 def test_new_layer_hash(self):self.assertEqual(sha(D/'eye.near.refined-layer.png'),self.q['newNearEyeLayerSHA256'])
 def test_mask_hash(self):self.assertEqual(sha(D/'eye.near.refined-mask.png'),self.q['newMaskSHA256'])
 def test_alpha_counts(self):
  a=Image.open(D/'eye.near.refined-layer.png').getchannel('A')
  self.assertEqual(sum(x>0 for x in a.getdata()),self.q['newLayerNonzeroAlphaPixels'])
  self.assertLess(self.q['newLayerNonzeroAlphaPixels'],self.q['oldLayerNonzeroAlphaPixels'])
 def test_alpha_dimensions(self):
  with Image.open(D/'eye.near.refined-layer.png') as x:self.assertEqual((x.mode,x.size),('RGBA',(1024,1024)))
 def test_three_motion_frames(self):
  self.assertEqual([x['shiftPx'] for x in self.q['frames']],[0,9,18])
  for x in self.q['frames']:self.assertEqual(sha(D/x['image']),x['sha256'])
 def test_motion_alpha_composite_determinism(self):
  layer=Image.open(D/'eye.near.refined-layer.png').convert('RGBA')
  bg=Image.open(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png').convert('RGBA')
  for x in self.q['frames']:
   moved=Image.new('RGBA',bg.size);moved.alpha_composite(layer,(x['shiftPx'],0))
   produced=Image.open(D/x['image']).convert('RGBA')
   self.assertIsNone(ImageChops.difference(Image.alpha_composite(bg,moved),produced).getbbox())
 def test_no_transparency_holes(self):self.assertEqual(self.q['holesByShift'],{'0':0,'9':0,'18':0})
 def test_hair_overlay_rejected(self):
  self.assertEqual(self.q['foregroundHairGate'],'FAIL_POLYGON_SEAMS_ALL_THREE')
  self.assertFalse(self.q['acceptedForegroundHairOverlay'])
 def test_gate_not_approved(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_html_discloses_failure(self):
  h=(D/'index.html').read_text()
  self.assertIn('视觉准入尚未通过',h)
  self.assertIn('id="shift"',h)
  self.assertIn('hairB-test.png',h)
if __name__=='__main__':unittest.main()
