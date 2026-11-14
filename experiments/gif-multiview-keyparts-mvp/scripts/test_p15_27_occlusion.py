import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-27-occlusion-audit.json').read_text())
class P15Occlusion(unittest.TestCase):
 def test_angles_source_identity(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(Q['angles'],[55,57.5,60,62.5,65])
 def test_every_diagnostic_source_provenance(self):
  for f in Q['frames']:
   self.assertEqual(len(f['paths']),7)
   for v in f['paths'].values():
    p=P/v['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),v['sha256'])
    with Image.open(p) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_exact_partition(self):
  for f in Q['frames']:
   m=f['metrics']
   self.assertLess(m['maxEyeDecompositionError'],1e-12)
   self.assertAlmostEqual(m['eyeSourceAlphaMass'],
    m['visibleEyeAlphaMass']+m['hiddenEyeAlphaMass'],delta=.02)
 def test_far_eye_occlusion_not_art_accepted(self):
  for f in Q['frames']:
   m=f['metrics']
   self.assertGreater(m['visibleEyeFraction'],.80)
   self.assertLess(m['visibleEyeFraction'],.95)
  self.assertFalse(Q['formalArtisticAcceptance'])
 def test_clip_hair_union_coverage(self):
  for f in Q['frames']:
   m=f['metrics']
   self.assertGreater(m['clipMountCoverageFraction'],.95)
   self.assertLess(m['clipMountCoverageFraction'],1)
   self.assertAlmostEqual(m['clipSourceAlphaMass'],
    m['clipOverHairAlphaMass']+m['clipWithoutHairAlphaMass'],delta=.02)
 def test_production_untouched(self):
  self.assertFalse(Q['productionVddModified'])
  self.assertFalse(Q['newOriginalPaintingCreated'])
 def test_zip(self):
  with zipfile.ZipFile(P/'exports/p15-27-occlusion-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertGreaterEqual(len(z.namelist()),42)
   self.assertIn('index.html',z.namelist())
   self.assertIn('qa.json',z.namelist())
if __name__=='__main__':unittest.main()
