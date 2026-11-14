import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-54-edge-landmark-review'
class P1554(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-54-edge-landmark-qa.json').read_text())
 def test_input_output_hashes(self):
  self.assertEqual(hashlib.sha256((R/'private-assets/exports/p15-53-gold-clip-repair/candidate-gold-cross-restored.png').read_bytes()).hexdigest(),self.q['inputSHA256'])
  self.assertEqual(hashlib.sha256((D/'candidate-refined.png').read_bytes()).hexdigest(),self.q['outputSHA256'])
 def test_rgba_dimensions(self):
  with Image.open(D/'candidate-refined.png') as x:self.assertEqual((x.mode,x.size),('RGBA',(1024,1024)))
 def test_clip_pixel_cleanup_is_bounded(self):self.assertEqual(self.q['refinedPixels'],110)
 def test_face_landmarks_close_to_proxy(self):
  for n in ['near_eye_iris','far_eye_iris','nose_tip','mouth_center','chin']:
   x=next(z for z in self.q['landmarks'] if z['name']==n);self.assertLessEqual(x['distance_px'],8)
 def test_clip_offset_not_hidden(self):
  x=next(z for z in self.q['landmarks'] if z['name']=='gold_clip_center');self.assertGreater(x['distance_px'],30)
 def test_landmark_estimates_are_manual(self):
  self.assertTrue(all(x['source']=='manual_visual_estimate' for x in self.q['landmarks']))
 def test_yaw_not_certified(self):self.assertFalse(self.q['cameraYaw65Verified'])
 def test_not_formal_artmesh(self):self.assertFalse(self.q['formalKeyframeAccepted']);self.assertFalse(self.q['artMeshModified'])
 def test_clip_review_assets(self):
  for n in ['before-clip-detail.png','after-clip-detail.png','landmark-comparison.png','preview-light.png','preview-blue.png','preview-pink.png']:
   self.assertTrue((D/n).exists())
 def test_html_declares_measurement_limit(self):
  h=(D/'index.html').read_text();self.assertIn('37px',h);self.assertIn('不准入',h)
if __name__=='__main__':unittest.main()
