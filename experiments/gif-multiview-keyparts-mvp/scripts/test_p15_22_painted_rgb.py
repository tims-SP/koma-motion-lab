import hashlib,json,unittest,zipfile
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent.parent
A=R/'private-assets'
Q=json.loads((R/'evidence/p15-22-painted-rgb-candidate-qa.json').read_text())
class IndependentPaintRgb(unittest.TestCase):
 def test_identity_and_angles(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual([x['yaw'] for x in Q['views']],[57.5,60])
 def test_source_hashes(self):
  for x in Q['views']:
   self.assertEqual(hashlib.sha256((A/x['sourceImage']).read_bytes()).hexdigest(),x['sourceSHA256'])
 def test_26_rgba_layers(self):
  self.assertEqual(sum(len(x['roles']) for x in Q['views']),26)
  for v in Q['views']:
   for role in v['roles']:
    with Image.open(A/role['path']) as im:
     self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
     out=np.asarray(im)
    alpha=next(x for x in json.loads((R/'evidence/p15-21-intermediate-components-qa.json').read_text())['frames'] if x['yaw']==v['yaw'])
    a=next(p for p in alpha['roles'] if p['role']==role['role'])
    with Image.open(A/a['path']) as im:expected=np.asarray(im.convert('RGBA'))[:,:,3]
    self.assertTrue(np.array_equal(out[:,:,3],expected))
    self.assertEqual(hashlib.sha256((A/role['path']).read_bytes()).hexdigest(),role['sha256'])
 def test_source_rgb_is_distinct_from_old_vdd(self):
  for v in Q['views']:
   r=v['roles']
   self.assertTrue(all(x['independentRgb'] and not x['independentSilhouette'] for x in r))
   self.assertLess(v['sourceForegroundIoUWithSourceDerivedAlpha'],.92)
 def test_keypart_white_risk(self):
  for v in Q['views']:
   self.assertGreater(v['keyRoleRisks']['hair.ahoge'],.15)
   self.assertGreater(v['keyRoleRisks']['hair.clip.cross_gold'],.08)
 def test_new_generation_is_unavailable_and_not_approved(self):
  self.assertFalse(Q['newModelGenerationP15_22'])
  self.assertFalse(Q['artisticAcceptance'])
  self.assertEqual(Q['acceptedIndependentPaintedKeyparts'],0)
  self.assertEqual(Q['acceptedNewUnderpainting'],0)
 def test_bundle_integrity(self):
  with zipfile.ZipFile(A/'exports/p15-22-painted-rgb-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertEqual(len(z.namelist()),34)
if __name__=='__main__':unittest.main()
