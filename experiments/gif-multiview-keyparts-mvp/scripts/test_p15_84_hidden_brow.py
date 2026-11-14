import unittest,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-84-clean-brow-inpaint'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class P1584(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-84-qa.json').read_text())
 def test_source(self):self.assertEqual(sha(P/'p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_eye_source(self):self.assertEqual(sha(P/'p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['eyeLayerSHA256'])
 def test_brow_source(self):self.assertEqual(sha(P/'p15-79-brow-split/eyebrow.same-view.png'),self.q['browLayerSHA256'])
 def test_hair_source(self):self.assertEqual(sha(P/'p15-81-image-layered/sam3-027-aligned-alpha.png'),self.q['hairMaskSHA256'])
 def test_input_hash(self):self.assertEqual(sha(D/'input-512.png'),self.q['inputSHA256'])
 def test_mask_hash(self):self.assertEqual(sha(D/'mask-512.png'),self.q['maskSHA256'])
 def test_real_model_success(self):
  self.assertEqual(self.q['modelStatus'],'SUCCESS')
  self.assertGreater((D/'model-512.png').stat().st_size,1000)
  with Image.open(D/'model-512.png') as im:self.assertEqual(im.size,(512,512))
 def test_underpaint_hash(self):self.assertEqual(sha(D/'clean-hidden-face.png'),self.q['underpaintSHA256'])
 def test_underpaint_only_mask(self):self.assertEqual(self.q['modelChangedOutsideMaskPixels'],0)
 def test_model_changed_inside(self):self.assertGreater(self.q['modelChangedInsideMaskPixels'],1000)
 def test_frame00_hash(self):self.assertEqual(sha(D/'frame-00.png'),self.q['frameHashes']['0'])
 def test_frame9_hash(self):self.assertEqual(sha(D/'frame-09.png'),self.q['frameHashes']['9'])
 def test_frame18_hash(self):self.assertEqual(sha(D/'frame-18.png'),self.q['frameHashes']['18'])
 def test_eye_holes(self):self.assertEqual([self.q['motionFrames'][n]['holesROI'] for n in ('9','18')],[0,0])
 def test_underpaint_pixel_scope(self):
  s=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA').tobytes()
  b=Image.open(D/'clean-hidden-face.png').convert('RGBA').tobytes()
  m=Image.open(D/'mask-full.png').convert('L').tobytes()
  self.assertTrue(all(s[i:i+4]==b[i:i+4] for i,v in enumerate(m) if not v for i in [i*4]))
 def test_zero_pose_independent_source(self):
  a=Image.open(D/'frame-00.png').convert('RGBA').tobytes()
  b=Image.open(P/'p15-82-rest-underpaint/actual-rest-by-independent-parts.png').convert('RGBA').tobytes()
  self.assertEqual(a,b)
 def test_formal_not_approved(self):
  self.assertFalse(self.q['formalArtMeshAccepted']);self.assertFalse(self.q['formalKeyframeAccepted'])
if __name__=='__main__':unittest.main()
