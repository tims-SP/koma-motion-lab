import json,hashlib,unittest
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
OUT=P/'exports/p15-17-anatomical-review'
Q=json.loads((OUT/'qa.json').read_text())
class AnatomicalReview(unittest.TestCase):
 def test_five_ordered_frames(self):
  self.assertEqual([f['angle'] for f in Q['frames']],[55,57.5,60,62.5,65])
  self.assertTrue(all(f['size']==[1024,1024] for f in Q['frames']))
 def test_source_hashes(self):
  for f in Q['frames']:
   p=OUT/f['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f['sha256'])
 def test_pair_continuity_gate(self):
  self.assertEqual(len(Q['adjacentAlphaIoU']),4)
  self.assertTrue(all(x['alphaIoU']>=.95 for x in Q['adjacentAlphaIoU']))
 def test_registered_source_and_nonpromotion(self):
  self.assertEqual(Q['registeredValidPairs'],22)
  self.assertTrue(Q['profilePSDVerified'])
  self.assertEqual(Q['approvedIndependentPaintings'],0)
  self.assertEqual(Q['approvedHiddenUnderpainting'],0)
 def test_archive(self):
  import zipfile
  with zipfile.ZipFile(P/'exports/p15-17-anatomical-review.zip') as z:self.assertIsNone(z.testzip())
if __name__=='__main__':unittest.main()
