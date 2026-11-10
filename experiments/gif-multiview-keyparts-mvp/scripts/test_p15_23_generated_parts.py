import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
Q=json.loads((R/'evidence/p15-23-model-generated-keypart-qa.json').read_text())
class P15GeneratedSourceParts(unittest.TestCase):
 def test_identity_roles(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(Q['targetAngle'],60)
  self.assertEqual(Q['modelGeneratedSourceCount'],4)
  self.assertEqual({x['role'] for x in Q['parts']},
    {'hair.side','hair.ahoge','eye.far','hair.clip.cross_gold'})
 def test_file_sha_and_transparency(self):
  for part in Q['parts']:
   for key,sha in [('source','sourceSHA256'),('isolated','isolatedSHA256'),('registered','registeredSHA256')]:
    p=P/part[key];self.assertTrue(p.is_file())
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),part[sha])
   for key in ['isolated','registered']:
    with Image.open(P/part[key]) as im:
     self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_genuinely_new_alpha_pixels(self):
  for part in Q['parts']:
   newer=np.asarray(Image.open(P/part['registered']).convert('RGBA'))[:,:,3]
   older=np.asarray(Image.open(P/'p15-21-intermediate-components/yaw60'/(part['role']+'.png')).convert('RGBA'))[:,:,3]
   self.assertFalse(np.array_equal(newer,older))
   self.assertGreater(int(np.count_nonzero(newer>16)),500)
   self.assertFalse(part['reusedOldVddAlpha'])
   self.assertTrue(part['originalModelSilhouetteRetained'])
 def test_registered_location_and_bbox(self):
  for part in Q['parts']:
   pix=np.asarray(Image.open(P/part['registered']).convert('RGBA'))[:,:,3]>16
   ys,xs=np.where(pix)
   x0,y0,x1,y1=part['registeredTargetBBox']
   self.assertGreaterEqual(int(xs.min()),x0)
   self.assertGreaterEqual(int(ys.min()),y0)
   self.assertLess(int(xs.max()),x1)
   self.assertLess(int(ys.max()),y1)
 def test_diagnostic_composite(self):
  path=P/Q['diagnosticComposite']
  self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),Q['diagnosticCompositeSHA256'])
  with Image.open(path) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_no_false_art_approval(self):
  self.assertEqual(Q['approvedIndependentSemanticPaintingCount'],0)
  self.assertFalse(Q['hiddenUnderpaintApproval'])
  self.assertIn('FAIL_',Q['formalArtGate'])
  self.assertEqual(Q['isolatedNativeSemanticSourcesCount'],0)
  self.assertTrue(all(not x['generatedSourceWasIsolated'] for x in Q['parts']))
 def test_archive(self):
  with zipfile.ZipFile(P/'exports/p15-23-model-keyparts-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertGreaterEqual(len(z.namelist()),17)
   self.assertIn('index.html',z.namelist())
   self.assertIn('qa.json',z.namelist())
if __name__=='__main__':unittest.main()
