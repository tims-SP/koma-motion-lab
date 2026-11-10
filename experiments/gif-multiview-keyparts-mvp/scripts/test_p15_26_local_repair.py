import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-26-local-repair-qa.json').read_text())
class Repair(unittest.TestCase):
 def test_five_frames_three_roles(self):
  self.assertEqual(Q['angles'],[55,57.5,60,62.5,65])
  self.assertEqual(len(Q['frames']),5)
  self.assertEqual(sum(len(f['roles']) for f in Q['frames']),15)
 def test_original_source_sha(self):
  for f in Q['frames']:
   slug='yaw'+(str(int(f['angle'])) if f['angle']%1==0 else str(f['angle']).replace('.','p'))
   for role in f['roles']:
    old=P/'p15-21-intermediate-components'/slug/(role['role']+'.png')
    self.assertEqual(hashlib.sha256(old.read_bytes()).hexdigest(),role['sourceSHA256'])
 def test_RGBA_and_deltas(self):
  for f in Q['frames']:
   for role in f['roles']:
    target=P/role['path']
    self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),role['sha256'])
    with Image.open(target) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
    self.assertGreater(role['rgbChangedPixels']+role['alphaChangedPixels'],0)
 def test_preservation_gate(self):
  for f in Q['frames']:
   self.assertTrue(f['baselineRoundtripExact'])
   self.assertGreaterEqual(f['compositeAlphaIoU'],.995)
   self.assertLess(f['compositeAlphaIoU'],1.00001)
 def test_role_specific_changes(self):
  for f in Q['frames']:
   roles={p['role']:p for p in f['roles']}
   self.assertGreater(roles['hair.side']['rgbChangedPixels'],0)
   self.assertEqual(roles['hair.side']['alphaChangedPixels'],0)
   self.assertGreater(roles['hair.ahoge']['alphaChangedPixels'],0)
   self.assertGreater(roles['eye.far']['alphaChangedPixels'],0)
 def test_no_false_original_art_approval(self):
  self.assertFalse(Q['independentPaintingProduced'])
  self.assertFalse(Q['formalArtAccepted'])
  self.assertFalse(Q['productionVddChanged'])
 def test_offline_archive(self):
  with zipfile.ZipFile(P/'exports/p15-26-local-repair-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertIn('index.html',z.namelist())
   self.assertIn('qa.json',z.namelist())
if __name__=='__main__':unittest.main()
