import json,unittest
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'private-assets/exports/p15-40-profile-review'
AUD=json.loads((ROOT/'evidence/p15-40-profile-qa.json').read_text())
class Review(unittest.TestCase):
 def test_monotonic_far_eye(self):
  ratios=[f["eyeVisibleRatio"] for f in AUD["frames"]]
  self.assertTrue(all(b<=a for a,b in zip(ratios,ratios[1:])))
  self.assertLess(ratios[-1],.04)
 def test_clip_attachment_improves(self):
  for f in AUD["frames"]:
   self.assertGreaterEqual(f["clipContactAfter"],f["clipContactBefore"])
   self.assertLessEqual(max(map(abs,f["clipShiftXY"])),3)

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
 def test_eye_source_underpaint_preserved(self):
  for f in AUD['frames']:
   d=DATA/f['tag']
   source=np.asarray(Image.open(ROOT/'private-assets/p15-38-p0-registered-arc'/f['tag']/'eye.far.png'))
   hidden=np.asarray(Image.open(d/'far-eye-underpaint.png'))
   self.assertTrue(np.array_equal(source,hidden))
 def test_local_changes_only(self):
  for f in AUD['frames']:
   self.assertGreater(f['changedPixels'],0)
   self.assertLess(f['changedPixels'],10000)
   self.assertLessEqual(f['farEyeVisibleAlpha'],f['farEyeSourceAlpha'])
 def test_review_and_admission_distinct(self):
  self.assertTrue((DATA/'index.html').is_file());self.assertFalse(AUD['artisticApproval'])
if __name__=='__main__':unittest.main()
