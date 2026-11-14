import hashlib,json,unittest,zipfile
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent.parent
AS=R/'private-assets'
QA=json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())
ROLES={'hair.side','hair.ahoge','hair.clip.cross_gold','eye.far'}
class P15LayeredIntermediate(unittest.TestCase):
 def test_roles_and_frames(self):
  self.assertEqual(QA['angles'],[55,57.5,60,62.5,65])
  self.assertEqual(len(QA['frames']),5)
  self.assertEqual(QA['roleCount'],13)
  self.assertEqual(sum(len(f['roles']) for f in QA['frames']),65)
 def test_exact_443px_composition(self):
  for f in QA['frames']:
   self.assertEqual(f['nativeRoundtripMaxPixelDelta'],0)
   self.assertEqual(f['nativeRoundtripChangedPixels'],0)
   self.assertTrue(f['unchangedFromP15_17Baseline'])
 def test_layers_file_integrity(self):
  for f in QA['frames']:
   for part in f['roles']:
    for key,digest,size in [('path','sha256',(1024,1024)),('native','nativeSHA256',(443,443))]:
     p=AS/part[key]
     self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),part[digest])
     with Image.open(p) as im:self.assertEqual((im.mode,im.size),('RGBA',size))
 def test_nonempty_keyparts_and_hidden_roles(self):
  for f in QA['frames']:
   parts={x['role']:x for x in f['roles']}
   for role in ROLES:self.assertGreater(parts[role]['visiblePixels'],100, (f['yaw'],role))
   self.assertEqual(parts['ear.far']['visiblePixels'],0)
   self.assertEqual(f['nonEmptyParts'],12)
 def test_covered_pixels_are_recorded(self):
  for f in QA['frames']:
   self.assertEqual(set(f['hiddenOccludedPixelInstances']),set(QA['roles']))
   self.assertGreater(f['hiddenOccludedPixelInstances']['face.skin'],0)
 def test_far_eye_and_clip_alpha_fade_monotonically(self):
  for role in ('eye.far','hair.clip.cross_gold'):
   totals=[]
   for f in QA['frames']:
    entry=next(p for p in f['roles'] if p['role']==role)
    with Image.open(AS/entry['native']) as im:
     totals.append(float(np.asarray(im.getchannel('A')).sum())/255)
   self.assertTrue(all(totals[i]>totals[i+1] for i in range(4)),(role,totals))
 def test_no_false_art_pass(self):
  self.assertFalse(QA['artisticAcceptance'])
  self.assertFalse(QA['hiddenUnderpaintArtApproval'])
  self.assertEqual(QA['newIndependentPaintingCount'],0)
  self.assertIn('SOURCE_DERIVED',QA['assetType'])
 def test_offline_archive(self):
  with zipfile.ZipFile(AS/'exports/p15-21-layered-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertEqual(len(z.namelist()),72)
if __name__=='__main__':unittest.main()
