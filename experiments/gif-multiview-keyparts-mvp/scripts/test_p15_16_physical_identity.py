import hashlib,json,unittest
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
Q=json.loads((R/'evidence/p15-16-physical-identity-qa.json').read_text())
OLD=json.loads((R/'evidence/p15-15-role-routing-qa.json').read_text())
def read(p):return np.asarray(Image.open(p).convert('RGBA'))
class PhysicalIdentity(unittest.TestCase):
 def test_45_anchor(self):
  frame=next(v for v in Q['views'] if v['view']=='yaw045')
  self.assertLess(frame['nearEyeAnchorX768'],frame['farEyeAnchorX768'])
  self.assertEqual(frame['physicalSideConfidence'],'P5_ANCHOR_SUPPORTED')
 def test_diagnostic_preserves_original_layer_sets(self):
  for v in Q['views']:
   self.assertTrue(all(v['conservesNearFarPixelSets'].values()))
   orig=next(x for x in OLD['views'] if x['yaw']==v['view'])
   prev={x['role']:x for x in orig['roles']}
   for row in v['roles']:
    path=P/row['path']
    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row['sha256'])
    if v['view']=='yaw045' and row['role'] in ['eye.near','eye.far','ear.near','ear.far']:
     inverse=row['role'].replace('near','TEMP').replace('far','near').replace('TEMP','far')
     self.assertTrue(np.array_equal(read(path),read(P/prev[inverse]['path'])))
 def test_unresolved_not_accepted(self):
  self.assertFalse(Q['artisticAcceptance'])
  self.assertEqual(Q['approvedIndependentPaintedLayers'],0)
  self.assertFalse(Q['underpaintArtAcceptance'])
  self.assertEqual(next(x for x in Q['views'] if x['view']=='yaw077p5')['physicalSideConfidence'],'SINGLE_EYE_UNRESOLVED')
if __name__=='__main__':unittest.main()
