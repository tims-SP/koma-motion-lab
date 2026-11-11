import unittest,hashlib,json
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-86-semantic-ownership'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
class TestP1586(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-86-qa.json').read_text())
 def test_input_hashes(self):
  for k,v in self.q['inputSHA256'].items():
   mapping={'source':'p15-56-edge-matting/candidate-erode-2.png','oldUnderpaint':'p15-84-clean-brow-inpaint/clean-hidden-face.png','cleanSameViewUnderpaint':'p15-70-seam-repair/forehead-seam-repaired.png','oldSAM3Hair':'p15-81-image-layered/sam3-027-hair-rgba.png','sourceEye':'p15-65-eyelid-refinement/eye.near.refined-layer.png','oldSourceBangMask':'p15-82-rest-underpaint/mask.owner-bangs.png','oldSourceEyeMask':'p15-82-rest-underpaint/mask.owner-eye.png','oldSourceFaceMask':'p15-82-rest-underpaint/mask.owner-face.png','oldSourceClipMask':'p15-82-rest-underpaint/mask.owner-clip.png','sourceClip':'p15-82-rest-underpaint/part.source-clip.png','priorInpaintMask':'p15-84-clean-brow-inpaint/mask-full.png'}
   self.assertEqual(sha(P/mapping[k]),v)
 def test_source_mask_sha(self):
  for n,s in self.q['sourceMaskSHA256'].items():self.assertEqual(sha(D/f'owner-{n}.png'),s)
 def test_source_parts_sha(self):
  for n,s in self.q['sourcePartSHA256'].items():self.assertEqual(sha(D/f'part-{n}.png'),s)
 def test_rest_sha(self):
  a=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA').tobytes()
  b=Image.open(D/'rest-from-reassigned-ownership.png').convert('RGBA').tobytes()
  self.assertTrue(all(a[i:i+4]==b[i:i+4] or a[i+3]==0 for i in range(0,len(a),4)))
 def test_rest_actual_recomposite(self):
  im=Image.new('RGBA',(1024,1024))
  for n in ('face','eye','bangs','clip'):im=Image.alpha_composite(im,Image.open(D/f'part-{n}.png').convert('RGBA'))
  self.assertEqual(im.tobytes(),Image.open(D/'rest-from-reassigned-ownership.png').convert('RGBA').tobytes())
 def test_owner_partition(self):
  masks=[Image.open(D/f'owner-{n}.png').convert('L').tobytes() for n in ('face','eye','bangs','clip')]
  self.assertTrue(all(sum(m[i]>0 for m in masks)==1 for i in range(1024*1024)))
 def test_owner_transfer(self):self.assertEqual(self.q['transferredBangToEyePixels'],391)
 def test_reassigned_eye_owner_growth(self):
  self.assertEqual(self.q['newEyeOwnerPixelCount']-self.q['originalEyeOwnerPixelCount'],391)
 def test_original_rest_zero(self):self.assertEqual(self.q['restVisiblePixelDiff'],0)
 def test_rest_alpha_zero(self):self.assertEqual(self.q['restAlphaPixelDiff'],0)
 def test_static_lash_removed(self):
  self.assertEqual((self.q['stationaryDarkPixelsBefore'],self.q['stationaryDarkPixelsAfter']),(8,0))
 def test_no_new_models(self):self.assertEqual(self.q['newModelCalls'],0)
 def test_no_cloning(self):self.assertEqual(self.q['newCloneOperations'],0)
 def test_frame_sha(self):
  for dx in (0,9,18):self.assertEqual(sha(D/f'frame-reassigned-{dx:02d}.png'),self.q['frameQA'][str(dx)]['sha256'])
 def test_no_face_holes(self):self.assertTrue(all(v['faceHoles']==0 for v in self.q['frameQA'].values()))
 def test_zero_same_reference(self):self.assertEqual(self.q['frameQA']['0']['visibleChangedFromP1584'],0)
 def test_gate_visual_fail(self):self.assertIn('FAIL',self.q['visualGate'])
 def test_not_accepted(self):self.assertFalse(self.q['candidateAccepted'])
 def test_formal_rejected(self):self.assertFalse(self.q['formalArtMeshAccepted']);self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_html_gate(self):self.assertIn('正式 ArtMesh 视觉门禁 FAIL',(D/'index.html').read_text())
if __name__=='__main__':unittest.main()
