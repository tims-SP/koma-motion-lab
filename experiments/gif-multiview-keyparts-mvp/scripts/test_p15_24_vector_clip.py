import hashlib,json,unittest,zipfile
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
Q=json.loads((R/'evidence/p15-24-vector-cross-clip-qa.json').read_text())
class NewClipPaint(unittest.TestCase):
 def test_five_views_and_one_role(self):
  self.assertEqual(Q['angles'],[55,57.5,60,62.5,65])
  self.assertEqual(Q['semanticRolesCreated'],['hair.clip.cross_gold'])
  self.assertEqual(len(Q['results']),5)
 def test_p0_reference_integrity(self):
  clip=P/'p15-20-canonical-source-views/yaw045/hair.clip.cross_gold.png'
  self.assertEqual(hashlib.sha256(clip.read_bytes()).hexdigest(),Q['sourceHeroClip45SHA256'])
 def test_rgba_and_distinct_alpha(self):
  for f in Q['results']:
   p=P/f['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f['pathSHA256'])
   with Image.open(p) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
   with Image.open(p) as im:new=np.asarray(im.getchannel('A'))
   old=P/'p15-21-intermediate-components'/('yaw'+str(f['angle']).replace('.0','').replace('.','p'))/'hair.clip.cross_gold.png'
   with Image.open(old) as im:old_a=np.asarray(im.getchannel('A'))
   self.assertFalse(np.array_equal(new,old_a))
   self.assertGreater(f['paintedVisiblePixels'],1500)
   self.assertGreater(f['clipAlphaIoUWithVDD'],.45)
 def test_native_composition_unchanged_for_baseline(self):
  for f in Q['results']:self.assertEqual(f['baselineCompositeDiffPixels'],0)
 def test_diagnostic_files_and_different_composite(self):
  for f in Q['results']:
   p=P/f['diagnostic'];self.assertTrue(p.is_file())
   self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f['diagnosticSHA256'])
   self.assertFalse(f['productionPromoted'])
 def test_source_and_art_provenance(self):
  self.assertTrue(Q['notDiffusionOutput'])
  self.assertEqual(Q['referenceEditAttempt'],'ZERO_GPU_QUOTA_EXCEEDED')
  self.assertFalse(Q['artisticAcceptance'])
  self.assertEqual(Q['rolesAccepted'],0)
  self.assertEqual(Q['hiddenUnderpaintAccepted'],0)
 def test_archive(self):
  with zipfile.ZipFile(P/'exports/p15-24-cross-clip-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertIn('index.html',z.namelist())
   self.assertIn('qa.json',z.namelist())
if __name__=='__main__':unittest.main()
