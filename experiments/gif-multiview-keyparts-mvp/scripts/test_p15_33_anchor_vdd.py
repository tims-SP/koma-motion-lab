import json,hashlib,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
Q=json.loads((R/'evidence/p15-33-anchor-vdd-qa.json').read_text())
REF=json.loads((R/'evidence/p15-32-mesh-vdd-qa.json').read_text())
class P15_33_Anchors(unittest.TestCase):
 def test_identity_and_source(self):
  self.assertEqual(Q['characterId'],'p0_character_001')
  self.assertEqual(len(Q['frames']),9)
  self.assertEqual(Q['registeredCameraAnchorSource'],'evidence/p15-12-camera-proxy-qa.json')
 def test_five_keyframes_byte_identical(self):
  source=[f for f in Q['frames'] if f['kind']=='exact-source-keyframe']
  self.assertEqual(len(source),5)
  for f in source:
   yaw=f['yaw'];slug='yaw'+(str(int(yaw)) if float(yaw).is_integer() else str(yaw).replace('.','p'))
   target=P/'p15-33-anchor-mesh'/slug/'composite.png'
   ref=P/'p15-32-mesh-vdd'/slug/'composite.png'
   self.assertEqual(target.read_bytes(),ref.read_bytes())
 def test_semantic_mesh_roles(self):
  mids=[f for f in Q['frames'] if f['kind']=='semantic-anchor-constrained-mesh']
  self.assertEqual([x['yaw'] for x in mids],[56.25,58.75,61.25,63.75])
  self.assertEqual(set(Q['meshRoles']),{'eye.far','hair.clip.cross_gold','hair.side'})
  for f in mids:
   for role,diag in f['meshDiagnostics'].items():
    self.assertEqual(diag['left']['triangleFlips'],0)
    self.assertEqual(diag['right']['triangleFlips'],0)
    self.assertGreater(diag['left']['minAreaRatio'],.5)
    self.assertGreater(diag['right']['minAreaRatio'],.5)
    self.assertLess(diag['left']['maxConstraintResidualPx'],.1)
    self.assertLess(diag['right']['maxConstraintResidualPx'],.1)
    self.assertGreater(diag['changedPixelsVsP15_32'],100)
 def test_semantic_features_have_unequivocal_provenance(self):
  self.assertTrue(Q['secondaryFeaturesAreUnapprovedAlphaDerivedProxies'])
  for role,labels in Q['roleFeatureTypes'].items():
   self.assertGreaterEqual(len(labels),2)
   self.assertTrue(any('camera' in label for label in labels))
   self.assertTrue(any('alpha.proxy' in label for label in labels))
 def test_other_ten_roles_identical_to_p15_32(self):
  roles=['body.reference','hair.back','face.skin','ear.near','ear.far','eye.near','nose','mouth','hair.front','hair.ahoge']
  for f in Q['frames']:
   if f['kind']!='semantic-anchor-constrained-mesh':continue
   name='yaw'+str(f['yaw']).replace('.','p')
   for role in roles:
    self.assertEqual((P/'p15-33-anchor-mesh'/name/(role+'.png')).read_bytes(),
                     (P/'p15-32-mesh-vdd'/name/(role+'.png')).read_bytes())
 def test_output_images_and_sha(self):
  for f in Q['frames']:
   y=f['yaw'];name='yaw'+(str(int(y)) if float(y).is_integer() else str(y).replace('.','p'))
   folder=P/'p15-33-anchor-mesh'/name
   self.assertEqual(hashlib.sha256((folder/'composite.png').read_bytes()).hexdigest(),f['compositeSha256'])
   with Image.open(folder/'composite.png') as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
   for role in Q['meshRoles']:
    with Image.open(folder/(role+'.png')) as im:self.assertEqual((im.mode,im.size),('RGBA',(443,443)))
 def test_art_gate_remains_closed(self):
  for key in ('physical3DModelUsed','trueNoseOcclusionVerified','clipPhysicalHairLockMountVerified',
              'independentOriginalPaint','artisticallyAccepted','productionVddModified'):
   self.assertFalse(Q[key])
 def test_archive_integrity(self):
  p=P/'exports/p15-33-anchor-vdd-review.zip'
  with zipfile.ZipFile(p) as z:
   self.assertIsNone(z.testzip())
   self.assertIn('index.html',z.namelist())
   self.assertIn('qa.json',z.namelist())
if __name__=='__main__':unittest.main()
