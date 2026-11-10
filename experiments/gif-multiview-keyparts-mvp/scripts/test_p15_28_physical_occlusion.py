import json,hashlib,unittest
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-28-physical-occlusion-qa.json').read_text())
class PhysicalOcclusion(unittest.TestCase):
 def test_five_angles(self):self.assertEqual(Q['angles'],[55,57.5,60,62.5,65])
 def test_all_source_hashes(self):
  for f in Q['frames']:
   for v in f['files'].values():
    p=P/v['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),v['sha256'])
    with Image.open(p) as im:self.assertEqual(im.mode,'RGBA')
    self.assertIn(im.size,[(1024,1024),(443,443)])
 def test_exact_partition(self):
  for f in Q['frames']:
   self.assertEqual(f['decompositionError'],0.0)
   self.assertAlmostEqual(f['eyeSourceAlphaMass'],f['eyeVisibleAlphaMass']+f['eyeHiddenAlphaMass'],delta=.03)
 def test_no_added_global_fade(self):
  for f in Q['frames']:self.assertFalse(f['wholeEyeFadeApplied'])
 def test_not_falsely_claimed_occluded(self):
  for f in Q['frames']:self.assertGreater(f['eyeVisibleFraction'],.80);self.assertLess(f['eyeVisibleFraction'],.95)
  self.assertIn('do not add invented',Q['knownGap'])
 def test_production_unchanged(self):
  self.assertFalse(Q['sourceArtModified']);self.assertFalse(Q['productionVddModified'])
 def test_review_zip(self):
  import zipfile
  with zipfile.ZipFile(P/'exports/p15-28-physical-occlusion-review.zip') as z:
   self.assertIsNone(z.testzip());self.assertIn('index.html',z.namelist())
if __name__=='__main__':unittest.main()
