import json,unittest
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'private-assets/exports/p15-39-occlusion-review'
AUD=json.loads((ROOT/'evidence/p15-39-depth-review-qa.json').read_text())
class Review(unittest.TestCase):
 def test_frame_count(self):self.assertEqual(len(AUD['frames']),13)
 def test_sources_untouched(self):
  import hashlib
  for f in AUD['frames']:
   p=ROOT/'private-assets/p15-38-p0-registered-arc'/f['tag']/'composite-native.png'
   self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f['sourceSHA256'])
 def test_all_layers_are_native_rgba(self):
  for f in AUD['frames']:
   for p in ('source.png','candidate.png','far-eye-visible.png','far-eye-underpaint.png'):
    with Image.open(DATA/f['tag']/p) as im:self.assertEqual((im.mode,im.size),('RGBA',(443,443)))
 def test_eye_alpha_partition(self):
  for f in AUD['frames']:
   d=DATA/f['tag'];orig=np.asarray(Image.open(ROOT/'private-assets/p15-38-p0-registered-arc'/f['tag']/'eye.far.png'))[:,:,3].astype('int16')
   a=np.asarray(Image.open(d/'far-eye-visible.png'))[:,:,3].astype('int16')
   b=np.asarray(Image.open(d/'far-eye-underpaint.png'))[:,:,3].astype('int16')
   self.assertLessEqual(int(np.abs(orig-a-b).max()),1)
 def test_local_changes_only(self):
  for f in AUD['frames']:
   self.assertGreater(f['changedPixels'],0)
   self.assertLess(f['changedPixels'],2500)
   self.assertLessEqual(f['farEyeVisibleAlpha'],f['farEyeSourceAlpha'])
 def test_review_and_admission_distinct(self):
  self.assertTrue((DATA/'index.html').is_file());self.assertFalse(AUD['heroVerified']);self.assertFalse(AUD['formalArtistApproval'])
if __name__=='__main__':unittest.main()
