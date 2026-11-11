import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-77-art-layer'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1577(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-77-layer-qa.json').read_text())
 def test_source_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'),self.q['sourcesSHA256']['source'])
 def test_eye_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['sourcesSHA256']['eye'])
 def test_base_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-70-seam-repair/forehead-seam-repaired.png'),self.q['sourcesSHA256']['base'])
 def test_clip_sha(self):self.assertEqual(sha(R/'private-assets/exports/p15-69-clip-separation/hair-clip-gold-independent.png'),self.q['sourcesSHA256']['clip'])
 def test_layer_sha(self):
  self.assertEqual(sha(D/'eye.upper-lash.same-view.png'),self.q['lashLayerSHA256'])
  self.assertEqual(sha(D/'eye.iris-lower.same-view.png'),self.q['irisLayerSHA256'])
 def test_mask_sha(self):self.assertEqual(sha(D/'eye.upper-lash-selection.png'),self.q['maskSHA256'])
 def test_true_layer_dimensions(self):
  for name in ('eye.upper-lash.same-view.png','eye.iris-lower.same-view.png'):
   with Image.open(D/name) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_upper_lash_count(self):
  a=Image.open(D/'eye.upper-lash.same-view.png').getchannel('A')
  self.assertEqual(sum(v>0 for v in a.getdata()),self.q['upperLashVisiblePixels'])
 def test_alpha_exact_reconstruction(self):self.assertTrue(self.q['sameEyeAlphaAfterSplit'])
 def test_eye_reconstruction_rgba_exact(self):
  original=Image.open(R/'private-assets/exports/p15-65-eyelid-refinement/eye.near.refined-layer.png').convert('RGBA')
  reconstruction=Image.open(D/'eye.reconstructed-layer-composite.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(original,reconstruction).getbbox())
 def test_dynamic_zero_pose_exact(self):
  src=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  frame=Image.open(D/'depth-lash-00.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(src,frame).getbbox())
 def test_dynamic_z_order_changes(self):
  values=[v['zOrderChangedPixelsEyeROI'] for v in self.q['movingLayerProof']]
  self.assertEqual(values,[0,48,143])
 def test_frames_sha(self):
  for v in self.q['movingLayerProof']:
   self.assertEqual(sha(D/f"depth-lash-{v['dx']:02d}.png"),v['depthSHA256'])
 def test_older_donors_rejected(self):
  self.assertFalse(self.q['olderYaw45DonorsAccepted'])
  self.assertFalse(self.q['olderFrontDonorsAccepted'])
 def test_gate(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertFalse(self.q['dynamicVisualGatePassed'])
 def test_html(self):
  h=(D/'index.html').read_text();self.assertIn('正式视觉门禁 FAIL',h);self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
