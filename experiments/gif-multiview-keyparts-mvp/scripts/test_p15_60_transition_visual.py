import hashlib,json,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-60-transition-visual'
class TransitionVisual(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.q=json.loads((R/'evidence/p15-60-transition-visual-qa.json').read_text())
 def test_source_identity(self):
  p=R/'private-assets/p2-views/whole/yaw045.png';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['source45SHA256'])
 def test_target_identity(self):
  p=R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.q['targetRelativePlus20SHA256'])
 def test_nine_frames(self):
  self.assertEqual(len(self.q['frames']),9)
  self.assertEqual([f['nominalYawParameter'] for f in self.q['frames']],[45,47.5,50,52.5,55,57.5,60,62.5,65])
 def test_frame_hashes(self):
  for f in self.q['frames']:
   p=D/f['frame'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f['frameSHA256'])
 def test_endpoint_pixel_equality(self):
  self.assertEqual(Image.open(D/'frame-00.png').convert('RGBA').tobytes(),Image.open(R/'private-assets/p2-views/whole/yaw045.png').convert('RGBA').tobytes())
  self.assertEqual(Image.open(D/'frame-08.png').convert('RGBA').tobytes(),Image.open(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png').convert('RGBA').tobytes())
 def test_midpoint_generated(self):
  self.assertTrue((D/'face-04.png').is_file());self.assertAlmostEqual(self.q['frames'][4]['blendFactor'],.5)
 def test_support_iou(self):self.assertGreater(self.q['metrics']['supportIoU'],.8)
 def test_eye_region_delta(self):self.assertGreater(self.q['metrics']['eyeRegionMeanRGBDelta'],30)
 def test_frame_sizes(self):
  for f in self.q['frames']:
   with Image.open(D/f['frame']) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_diagnostic_gate_fail(self):self.assertEqual(self.q['visualGate'],'FAIL_DOUBLE_FEATURE_EXPOSURE_MIDPOINT')
 def test_not_real_vdd_or_artmesh(self):
  self.assertFalse(self.q['trueViewDependentDeformation'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertFalse(self.q['productionArtMeshModified'])
 def test_html_slider(self):
  h=(D/'index.html').read_text();self.assertIn('id="frameSlider"',h);self.assertIn('face-04.png',h);self.assertIn('Crossfade',h)
if __name__=='__main__':unittest.main()
