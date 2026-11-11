import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-61-semantic-feasibility'
class SemanticFeasibility(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-61-semantic-feasibility-qa.json').read_text())
 def test_target_provenance(self):
  p=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['candidateSHA256'])
 def test_canonical45(self):
  p=R/'private-assets/p2-views/whole/yaw045.png'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['canonical45SHA256'])
 def test_visible_cutouts(self):
  self.assertEqual(self.q['roiLayerCount'],5)
  self.assertEqual(len(self.q['visibleROIroles']),5)
  for role in self.q['visibleROIroles']:
   p=D/(role['role']+'.visible.png')
   self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),role['cutoutSHA256'])
   with Image.open(p) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_not_true_independent_art(self):
  self.assertTrue(all(not x['trueSemanticPurityVerified'] for x in self.q['visibleROIroles']))
  self.assertTrue(all(not x['hiddenUnderpaintAvailable'] for x in self.q['visibleROIroles']))
 def test_exact_reassembly_is_only_visible_partition(self):
  original=Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  reconstructed=Image.open(D/'reconstructed.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(original,reconstructed).getbbox())
  self.assertTrue(self.q['reconstruction']['pixelExact'])
 def test_eye_shift_opens_real_holes(self):
  self.assertGreater(self.q['movingEye']['transparentHolePixelsInNearEyeROI'],1000)
  self.assertEqual(self.q['movingEye']['offsetPx'],[18,0])
 def test_clip_reconstruction(self):
  src=Image.open(D/'hair.clip.cross_gold.independent.png').convert('RGBA')
  self.assertEqual(hashlib.sha256((R/'private-assets/exports/p15-56-edge-matting/clip-erode-2.png').read_bytes()).hexdigest(),self.q['realIndependentClipSHA256'])
  self.assertEqual(src.getchannel('A').getbbox(),(693,281,758,368))
  self.assertTrue(self.q['realClipReconstructionExact'])
 def test_missing_underpaint(self):
  self.assertFalse(self.q['independentUnderpaintForEyesAndFace'])
  self.assertEqual(len(self.q['remainingFusedRoles']),7)
 def test_rejected(self):
  self.assertTrue(self.q['semanticSeparationGate'].startswith('FAIL_'))
  self.assertTrue(self.q['viewDependentVDDGate'].startswith('FAIL_'))
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertFalse(self.q['formalArtMeshModified'])
 def test_review_files(self):
  h=(D/'index.html').read_text()
  for name in ['eye-shift-with-hole-face.png','eye.near.visible.png','eye.far.visible.png','reconstructed.png','hair.clip.cross_gold.independent.png']:
   self.assertTrue((D/name).exists());self.assertIn('src="'+name+'"',h)
if __name__=='__main__':unittest.main()
