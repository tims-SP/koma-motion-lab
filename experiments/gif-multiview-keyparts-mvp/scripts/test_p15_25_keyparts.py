import hashlib,json,unittest,zipfile
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-25-original-keypart-paint-qa.json').read_text())
REVIEW=P/'exports/p15-25-four-role-review'
class NewPaintParts(unittest.TestCase):
 def test_scope(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(Q['angles'],[55,57.5,60,62.5,65])
  self.assertEqual(Q['roles'],['hair.side','hair.ahoge','eye.far'])
  self.assertEqual(sum(len(x['parts']) for x in Q['frames']),15)
 def test_new_alpha_and_sha(self):
  for frame in Q['frames']:
   name='yaw'+(str(int(frame['angle'])) if frame['angle']%1==0 else str(frame['angle']).replace('.','p'))
   for row in frame['parts']:
    path=P/row['path']
    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row['sha256'])
    with Image.open(path) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
    old=P/'p15-21-intermediate-components'/name/(row['role']+'.png')
    with Image.open(old) as im:a=np.asarray(im.getchannel('A'))
    with Image.open(path) as im:b=np.asarray(im.getchannel('A'))
    self.assertFalse(np.array_equal(a,b))
    self.assertGreater(row['visiblePixels'],50)
 def test_every_baseline_exact(self):
  self.assertTrue(all(f['baselineExact'] for f in Q['frames']))
  self.assertFalse(Q['productionVddModified'])
 def test_full_underpaint_not_falsely_approved(self):
  self.assertTrue(Q['hiddenFarEyeIrisPixelsDrawn'])
  self.assertFalse(Q['hiddenFarEyeOcclusionCorrectnessVerified'])
  self.assertFalse(Q['artisticAcceptance'])
  self.assertEqual(Q['independentPartsArtisticallyApproved'],0)
 def test_five_view_four_role_review(self):
  data=json.loads((REVIEW/'qa.json').read_text())
  self.assertEqual(len(data['views']),5)
  for view in data['views']:
   self.assertEqual(len(view['roles']),4)
   self.assertTrue(0.85<view['alphaIoU']<1)
   for role in view['roles']:
    with Image.open(REVIEW/role['file']) as im:
     self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_zip(self):
  with zipfile.ZipFile(P/'exports/p15-25-four-role-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertIn('index.html',z.namelist())
   self.assertIn('qa.json',z.namelist())
if __name__=='__main__':unittest.main()
