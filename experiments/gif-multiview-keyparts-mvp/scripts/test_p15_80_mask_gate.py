import hashlib,json,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];P=R/'private-assets/exports';D=P/'p15-80-front-hair'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
class P1580(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-80-mask-qa.json').read_text())
 def test_source_sha(self):self.assertEqual(sha(P/'p15-74-bangs-repair/hair.front.alpha-dedup.png'),self.q['sourceSHA256'])
 def test_roi(self):self.assertEqual(self.q['roi'],[605,370,740,470])
 def test_three_variants(self):self.assertEqual(set(self.q['variants']),{'median3','opening3','closing3'})
 def test_changes(self):self.assertEqual([self.q['variants'][n]['changedAlphaPixels'] for n in ['median3','opening3','closing3']],[375,735,586])
 def test_outside_roi_unchanged(self):self.assertTrue(all(v['changedOutsideROI']==0 for v in self.q['variants'].values()))
 def test_variant_hashes(self):
  for n,v in self.q['variants'].items():
   self.assertEqual(sha(D/(n+'-hair.png')),v['hairSHA256'])
   self.assertEqual(sha(D/(n+'-18.png')),v['frameSHA256'])
 def test_zigzag_not_improved(self):
  self.assertEqual(self.q['roiRasterZigzagOriginal'],0)
  self.assertEqual(self.q['variants']['median3']['rasterZigzagCount'],1)
 def test_zero_pose_exact(self):
  a=Image.open(P/'p15-56-edge-matting/candidate-erode-2.png').convert('RGBA')
  b=Image.open(D/'candidate-median3-00.png').convert('RGBA')
  self.assertIsNone(ImageChops.difference(a,b).getbbox())
 def test_three_frame_sha(self):
  for dx in (0,9,18):
   self.assertEqual(sha(D/f'candidate-median3-{dx:02d}.png'),self.q['reviewFrames'][str(dx)]['sha256'])
 def test_no_face_holes(self):self.assertTrue(all(f['transparentHoles']==0 for f in self.q['reviewFrames'].values()))
 def test_formal_rejected(self):
  self.assertFalse(self.q['selectedForFormalOrNativePipeline'])
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
 def test_visual_gate(self):self.assertTrue(self.q['visualGate'].startswith('FAIL_'))
 def test_html(self):
  h=(D/'index.html').read_text()
  self.assertIn('正式视觉门禁 FAIL',h)
  self.assertIn('id="shift"',h)
if __name__=='__main__':unittest.main()
