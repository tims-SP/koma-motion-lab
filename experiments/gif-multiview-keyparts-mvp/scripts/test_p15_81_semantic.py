import json,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-81-image-layered';P=R/'private-assets/exports'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
class P1581(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((R/'evidence/p15-81-sam3-qa.json').read_text())
  cls.auth=json.loads((R/'evidence/p15-81-sam3-authenticated.json').read_text())
  cls.official=json.loads((R/'evidence/p15-81-layered-provider.json').read_text())
 def test_source_sha(self):self.assertEqual(sha(P/'p15-56-edge-matting/candidate-erode-2.png'),self.q['sourceSHA256'])
 def test_input_sha(self):self.assertEqual(sha(D/'input-head-640.png'),self.q['inputSHA256'])
 def test_qwen_failed(self):self.assertEqual(self.official['status'],'FAILED')
 def test_sam3_inference(self):self.assertEqual(self.auth['status'],'MODEL_RETURNED')
 def test_sam3_mask_hashes(self):
  for name in ('027','083'):
   self.assertEqual(sha(D/f'sam3-mask-{name}.png'),self.q['masks'][name]['rawMaskSHA256'])
 def test_asset_hashes(self):
  for name in ('027','083'):
   self.assertEqual(sha(D/f'sam3-{name}-hair-rgba.png'),self.q['masks'][name]['hairSHA256'])
   self.assertEqual(sha(D/f'sam3-{name}-aligned-alpha.png'),self.q['masks'][name]['alignedMaskSHA256'])
 def test_rgba_dimensions(self):
  for name in ('027','083'):
   with Image.open(D/f'sam3-{name}-hair-rgba.png') as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_sampling_excludes_eyes_cheek_clip(self):
  a=self.q['masks']['027']['anchorAlpha']
  self.assertEqual([a[k] for k in ('nearIris','cheekSkin','goldClip')],[0,0,0])
  self.assertGreater(a['frontHair'],128)
 def test_wide_mask_not_bangs_only(self):
  self.assertEqual(self.q['masks']['027']['anchorAlpha']['sideHair'],0)
  self.assertGreater(self.q['masks']['083']['anchorAlpha']['sideHair'],128)
 def test_actual_rest_not_exact(self):
  src=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  for name in ('027','083'):
   frame=Image.open(D/f'sam3-{name}-rest-composite.png').convert('RGBA')
   self.assertIsNotNone(ImageChops.difference(src,frame).getbbox())
 def test_actual_rest_diff_counts(self):
  self.assertEqual([self.q['masks'][k]['actualRestPoseChangedPixels'] for k in ('027','083')],[8409,8475])
 def test_model_outputs_referenced(self):
  self.assertTrue(all(sha(D/x['name'])==x['sha256'] for x in self.auth['outputs']))
 def test_motion_sha(self):
  for name in ('027','083'):
   for dx in (9,18):
    self.assertEqual(sha(D/f'sam3-{name}-motion-{dx:02d}.png'),self.q['masks'][name][f'dynamic{dx}SHA256'])
 def test_no_new_face_alpha_holes(self):
  for k in ('027','083'):self.assertEqual(self.q['masks'][k]['newHolesByOffset'],{'9':0,'18':0})
 def test_not_approved(self):
  self.assertFalse(self.q['realRestPoseExact']);self.assertFalse(self.q['formalArtMeshAccepted']);self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_html(self):
  h=(D/'index.html').read_text();self.assertIn('正式 ArtMesh 门禁 FAIL',h);self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
