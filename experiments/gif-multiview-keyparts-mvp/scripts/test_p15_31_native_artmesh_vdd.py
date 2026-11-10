import json,hashlib,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-31-native-vdd-qa.json').read_text())
O=P/'exports/p15-31-native-artmesh-review'
class NativeArtMeshVdd(unittest.TestCase):
 def test_nine_frames_13_roles(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(Q['roleCount'],13)
  self.assertEqual(len(Q['frames']),9)
  self.assertEqual(sum(len(f['parts']) for f in Q['frames']),117)
 def test_keyframes_identical(self):
  five=[f for f in Q['frames'] if f['kind']=='tracked-keyframe']
  self.assertEqual(len(five),5)
  self.assertTrue(all(f['keyframePixelError']==0 for f in five))
 def test_midframes_are_independent_role_interpolation(self):
  mids=[f for f in Q['frames'] if f['kind']=='true-native-per-role-vdd']
  self.assertEqual([f['yaw'] for f in mids],[56.25,58.75,61.25,63.75])
  self.assertFalse(Q['fullFrameCrossfadeUsed'])
  self.assertTrue(Q['actualIndependentRoleFramesGenerated'])
  self.assertIn('PREMULTIPLIED',Q['interpolation'])
 def test_sha_and_alpha(self):
  for f in Q['frames']:
   name=P/f['composite']
   self.assertEqual(hashlib.sha256(name.read_bytes()).hexdigest(),f['compositeSHA256'])
   with Image.open(name) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
   for role in f['parts']:
    p=P/role['path']
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),role['sha256'])
    with Image.open(p) as im:self.assertEqual((im.mode,im.size),('RGBA',(443,443)))
 def test_continuity(self):
  for f in Q['frames'][1:]:
   self.assertGreater(f['previousAlphaIoU'],.97)
   self.assertLess(f['previousMeanAbsChannelDelta'],5)
 def test_review_no_mixed_sources_missing(self):
  review=json.loads((O/'qa.json').read_text())
  self.assertEqual(len(review['frames']),9)
  for f in review['frames']:
   directory=O/f['dir']
   self.assertEqual(len(f['parts']),5)
   for role in f['parts']:self.assertTrue((directory/role['src']).exists())
   self.assertEqual(f['changedVsFullFrame'],0 if f['key'] else f['changedVsFullFrame'])
   if not f['key']:self.assertGreater(f['changedVsFullFrame'],50000)
 def test_production_guardrail(self):
  self.assertFalse(Q['productionVddModified'])
  self.assertFalse(Q['artisticallyAccepted'])
  self.assertEqual(Q['newIndependentPaintings'],0)
  self.assertTrue(Q['nasalBridgeMaskIsOnlyP15_29Proxy'])
 def test_review_archive(self):
  with zipfile.ZipFile(P/'exports/p15-31-native-artmesh-review.zip') as z:
   self.assertIsNone(z.testzip())
   self.assertIn('index.html',z.namelist())
   self.assertIn('qa.json',z.namelist())
if __name__=='__main__':unittest.main()
