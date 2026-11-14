import hashlib,json,unittest
from pathlib import Path
from PIL import Image,ImageChops
R=Path(__file__).resolve().parents[1];D=R/'private-assets/exports/p15-69-clip-separation'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class ClipSingleDraw(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=json.loads((R/'evidence/p15-69-clip-qa.json').read_text())
 def test_source_sha(self):self.assertEqual(self.q['sourceSHA256'],sha(R/'private-assets/exports/p15-56-edge-matting/candidate-erode-2.png'))
 def test_forehead_source_sha(self):self.assertEqual(self.q['foreheadBaseSHA256'],sha(R/'private-assets/exports/p15-68-forehead/forehead-neural-underpaint.png'))
 def test_clean_clip_underlay_sha(self):self.assertEqual(self.q['cleanClipUnderlaySHA256'],sha(R/'private-assets/exports/p15-55-registration/underlay--28.png'))
 def test_eye_underpaint_sha(self):self.assertEqual(self.q['neuralEyeUnderpaintSHA256'],sha(R/'private-assets/exports/p15-63-masked-lama/underpaint-full.png'))
 def test_clip_sha(self):self.assertEqual(self.q['independentClipSHA256'],sha(R/'private-assets/exports/p15-56-edge-matting/clip-erode-2.png'))
 def test_cleaned_assets_sha(self):
  for f,k in [('clip-and-eye-free-underpaint.png','cleanedBackgroundSHA256'),('hair-front-no-gold-candidate.png','cleanedHairSHA256'),('clip-cleanup-guard.png','clipGuardSHA256')]:
   self.assertEqual(sha(D/f),self.q[k])
 def test_gold_hair_pixels_removed(self):
  self.assertGreater(self.q['hairYellowPixelsBefore'],1000)
  self.assertEqual(self.q['hairYellowPixelsAfter'],0)
 def test_no_hair_alpha_near_clip_guard(self):
  h=Image.open(D/'hair-front-no-gold-candidate.png').convert('RGBA').getchannel('A')
  guard=Image.open(D/'clip-cleanup-guard.png').convert('L')
  self.assertEqual(ImageChops.multiply(h,guard).getextrema()[1],0)
 def test_eye_fixed_region_replaced(self):self.assertGreater(self.q['eyeCleanupMaskPixels'],10000)
 def test_clip_once_final_layer(self):
  self.assertEqual(self.q['zOrder'][-1],'independent_gold_clip_once')
  self.assertEqual(len(self.q['zOrder']),4)
 def test_frames_exact_sha(self):
  self.assertEqual([x['dx'] for x in self.q['frames']],[0,9,18])
  for f in self.q['frames']:self.assertEqual(sha(D/f['file']),f['sha256'])
 def test_rgba(self):
  for x in ['clip-and-eye-free-underpaint.png','hair-front-no-gold-candidate.png','hair-clip-gold-independent.png','eye-shift-18-clip-once.png']:
   with Image.open(D/x) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_no_formal_promotion(self):
  self.assertFalse(self.q['formalArtMeshAccepted'])
  self.assertFalse(self.q['formalKeyframeAccepted'])
  self.assertFalse(self.q['fullHairSemanticIdentityVerified'])
 def test_html(self):
  h=(D/'index.html').read_text()
  self.assertIn('id="shift"',h)
  self.assertIn('完整前发仍未正式通过',h)
if __name__=='__main__':unittest.main()
