import unittest,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-66-front-bang'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class FrontBang(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-66-front-bang-qa.json').read_text())
 def test_source_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_underpaint_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png'),self.q['neuralUnderpaintSHA256'])
 def test_eye_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['eyeLayerSHA256'])
 def test_original_mask_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-63-masked-lama/mask-full.png'),self.q['originalInpaintMaskSHA256'])
 def test_old_hair_is_different_asset(self):
  self.assertEqual(sha(R/'private-assets/exports/p15-41-profile-candidate/layers/hair.front.png'),self.q['older45BangLayerSHA256'])
  self.assertFalse(self.q['older45BangReusedAsNewArtwork'])
 def test_alpha(self):
  p=D/'hair.front.eye-overlap.png'
  with Image.open(p) as im:
   self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
   self.assertEqual(list(im.getchannel('A').getbbox()),self.q['localBangAlphaBBox'])
   alpha=list(im.getchannel('A').getdata())
  self.assertEqual(sum(a>0 for a in alpha),self.q['localBangAlphaPixels'])
  self.assertEqual(sum(0<a<255 for a in alpha),self.q['localBangPartialAlphaPixels'])
 def test_local_mask_restricted_to_inpaint_area(self):
  mask=Image.open(D/'hair.front.eye-overlap-mask.png').convert('L')
  original=Image.open(R/'private-assets/exports/p15-63-masked-lama/mask-full.png').convert('L')
  self.assertIsNone(ImageChops.subtract(mask,original).getbbox())
 def test_no_holes(self):self.assertTrue(all(f['transparentHolePixels']==0 for f in self.q['frames']))
 def test_frame_offsets(self):self.assertEqual([f['dx'] for f in self.q['frames']],[0,9,18])
 def test_frame_hashes(self):
  for f in self.q['frames']:
   self.assertEqual(sha(D/f"eye-shift-{f['dx']:02d}-with-occlusion.png"),f['sha256'])
 def test_local_occlusion_actually_changes_image(self):
  self.assertTrue(all(f['changedRGBPixelsNearBang']>0 for f in self.q['frames']))
 def test_composite_determinism(self):
  eye=Image.open(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
  bg=Image.open(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png').convert('RGBA')
  hair=Image.open(D/'hair.front.eye-overlap.png').convert('RGBA')
  for f in self.q['frames']:
   moved=Image.new('RGBA',bg.size);moved.alpha_composite(eye,(f['dx'],0))
   out=Image.alpha_composite(Image.alpha_composite(bg,moved),hair)
   saved=Image.open(D/f"eye-shift-{f['dx']:02d}-with-occlusion.png").convert('RGBA')
   self.assertIsNone(ImageChops.difference(out,saved).getbbox())
 def test_full_artmesh_not_approved(self):
  self.assertFalse(self.q['fullIndependentFrontHairAvailable'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_review(self):
  h=(D/'index.html').read_text()
  self.assertIn('id="shift"',h)
  self.assertIn('完整前发 ArtMesh 仍失败',h)
if __name__=='__main__':unittest.main()
