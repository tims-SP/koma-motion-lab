import unittest,hashlib,json
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-82-rest-underpaint'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class TestP1582(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-82-source-decomposition-qa.json').read_text())
 def test_source_sha(self):self.assertEqual(sha(P/'p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_sam3_sha(self):self.assertEqual(sha(P/'p15-81-image-layered/sam3-027-aligned-alpha.png'),self.q['sam3AlphaSHA256'])
 def test_base_sha(self):self.assertEqual(sha(P/'p15-70-seam-repair/forehead-seam-repaired.png'),self.q['priorFaceSHA256'])
 def test_eye_sha(self):self.assertEqual(sha(P/'p15-65-eyelid-refinement/eye.near.refined-layer.png'),self.q['priorEyeSHA256'])
 def test_clip_sha(self):self.assertEqual(sha(P/'p15-69-clip-separation/hair-clip-gold-independent.png'),self.q['priorClipSHA256'])
 def test_layer_sha(self):
  for n,entry in self.q['sourceOwnedLayers'].items():
   self.assertEqual(sha(D/f'part.source-{n}.png'),entry['layerSHA256'])
   self.assertEqual(sha(D/f'mask.owner-{n}.png'),entry['maskSHA256'])
 def test_mask_partition_one_owner(self):
  ms=[Image.open(D/f'mask.owner-{n}.png').convert('L').tobytes() for n in ('clip','bangs','eye','face')]
  self.assertTrue(all(sum(b[i]>0 for b in ms)==1 for i in range(1024*1024)))
 def test_rest_visible_rgba_exact(self):
  orig=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA').tobytes()
  dest=Image.open(D/'actual-rest-by-independent-parts.png').convert('RGBA').tobytes()
  self.assertFalse(any(orig[i:i+4]!=dest[i:i+4] and orig[i+3]>0 for i in range(0,len(orig),4)))
 def test_rest_not_byte_exact(self):
  self.assertFalse(self.q['actualIndependentPartRestExactRGBA'])
  self.assertEqual(self.q['transparentRGBOnlyDifferences'],19603)
 def test_rest_generated_from_parts(self):
  im=Image.new('RGBA',(1024,1024))
  for n in ['face','eye','bangs','clip']:
   im=Image.alpha_composite(im,Image.open(D/f'part.source-{n}.png').convert('RGBA'))
  self.assertEqual(im.tobytes(),Image.open(D/'candidate-00.png').convert('RGBA').tobytes())
 def test_underpaint_sha(self):self.assertEqual(sha(D/'underpaint.clean-eye-region.png'),self.q['underpaintSHA256'])
 def test_dynamic_sha(self):
  for n,entry in self.q['selectedFrameQA'].items():
   self.assertEqual(sha(D/f'candidate-{int(n):02d}.png'),entry['sha256'])
 def test_no_new_holes(self):
  self.assertEqual([x['faceHoles'] for x in self.q['selectedFrameQA'].values()],[0,0,0])
 def test_real_moving_eye(self):
  self.assertIn('independently moving eye',self.q['selectedDynamicCandidate'])
 def test_0px_gate(self):
  self.assertTrue(self.q['finalZeroPoseVisuallyExact'])
  self.assertFalse(self.q['finalZeroPoseRawRGBAExact'])
 def test_reject_dynamic_formal_gate(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertIn('SEAMS_REMAIN',self.q['dynamicVisualGate'])
 def test_html(self):
  s=(D/'index.html').read_text();self.assertIn('正式动态画质：FAIL',s);self.assertIn('id="shift"',s)
if __name__=='__main__':unittest.main()
