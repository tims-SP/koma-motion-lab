import hashlib,json,unittest,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
E=json.loads((R/'evidence/p15-29-defade-bridge-qa.json').read_text())
C=json.loads((R/'evidence/p15-29-clip-mount-qa.json').read_text())
class P15_29_Recovery(unittest.TestCase):
 def test_source_identity_and_angles(self):
  self.assertEqual(E['characterId'],'p0_character_001')
  self.assertEqual(C['characterId'],E['characterId'])
  self.assertEqual(E['angles'],[55,57.5,60,62.5,65])
  self.assertEqual(C['angles'],E['angles'])
  self.assertEqual(hashlib.sha256((P/E['sourceP0_45']).read_bytes()).hexdigest(),E['sourceP0_SHA256'])
 def test_inverse_eye_source_mass_stability(self):
  masses=[f['restoredEyeMass'] for f in E['frames']]
  self.assertLess(max(masses)-min(masses),2.0)
  src=np.asarray(Image.open(P/E['sourceP0_45']).convert('RGBA'))[:,:,3].astype(float).sum()/255
  for mass in masses:self.assertLess(abs(mass-src),2)
 def test_inverse_eye_alpha_matches_registered_p0(self):
  original=np.asarray(Image.open(P/E['sourceP0_45']).convert('RGBA'))[:,:,3]>16
  for f in E['frames']:
   yaw=f['angle'];s='yaw'+(str(int(yaw)) if yaw%1==0 else str(yaw).replace('.','p'))
   recovered=np.asarray(Image.open(P/'p15-29-defade-bridge'/s/'inverse-fade.png').convert('RGBA'))[:,:,3]>16
   inter=np.count_nonzero(original&recovered);union=np.count_nonzero(original|recovered)
   self.assertGreater(inter/max(union,1),.95)
 def test_eye_fade_and_geometry_is_not_falsely_approved(self):
  self.assertFalse(E['geometryIsValidatedPhysical3D'])
  self.assertFalse(E['recoveryIsOriginalIndependentPainting'])
  self.assertFalse(E['artAccepted'])
  for f in E['frames']:
   self.assertTrue(f['nativeBaselineExact'])
   self.assertGreater(f['bridgeVisibleFractionOfRestored'],.40)
   self.assertLess(f['bridgeVisibleFractionOfRestored'],.75)
   self.assertGreater(f['wholeFrameChangedFromBaseline'],10000)
 def test_frame_source_hashes(self):
  for f in E['frames']:
   yaw=f['angle'];s='yaw'+(str(int(yaw)) if yaw%1==0 else str(yaw).replace('.','p'))
   for name,digest in f['images'].items():
    p=P/'p15-29-defade-bridge'/s/(name+'.png')
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),digest)
    with Image.open(p) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_clip_restoration_and_binding_status(self):
  masses=[f['recoveredMass'] for f in C['frames']]
  self.assertLess(max(masses)-min(masses),12)
  distance=[f['centerToAnchorPixels'] for f in C['frames']]
  self.assertEqual(distance,sorted(distance))
  for f in C['frames']:
   self.assertGreater(f['clipAttachedMassFraction'],.95)
   self.assertLess(f['clipAttachedMassFraction'],.99)
  self.assertFalse(C['hairMountingGeometricallyVerified3D'])
 def test_clip_hashes(self):
  for f in C['frames']:
   yaw=f['angle'];s='yaw'+(str(int(yaw)) if yaw%1==0 else str(yaw).replace('.','p'))
   for name,digest in f['images'].items():
    p=P/'p15-29-defade-bridge'/s/(name+'.png')
    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),digest)
    with Image.open(p) as im:self.assertEqual((im.mode,im.size),('RGBA',(1024,1024)))
 def test_production_unchanged(self):
  self.assertFalse(E['productionVddModified'])
  self.assertFalse(C['productionVddModified'])
  self.assertFalse(C['artAccepted'])
 def test_review_zip(self):
  with zipfile.ZipFile(P/'exports/p15-29-defade-geometry-review.zip') as z:
   self.assertIsNone(z.testzip());self.assertGreaterEqual(len(z.namelist()),55)
   self.assertIn('index.html',z.namelist())
if __name__=='__main__':unittest.main()
