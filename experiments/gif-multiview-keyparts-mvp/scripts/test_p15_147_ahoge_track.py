import importlib.util
import unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_147_ahoge_track.py')
spec=importlib.util.spec_from_file_location('p15_147_ahoge_track',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AhogeRootTipTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=m.evaluate(save=False)
 def test_tracks_are_defined_for_all_keyframes(self):
  self.assertEqual(len(self.r['sourceAnchors']),3)
  for points in self.r['sourceAnchors'].values():
   self.assertEqual(set(points),set(m.ROLES))
   self.assertGreater(np.linalg.norm(np.asarray(points['hair.ahoge.root'])-np.asarray(points['hair.ahoge.apex'])),40)
 def test_affine_root_tip_endpoints(self):
  tracks=m.native_tracks()
  target=m.pose_at(90.,112.5,.5,tracks)
  a,_=m.matrix_for(tracks[90.],target,1.0)
  for role in m.ROLES:
   src=tracks[90.][role]
   dst=a[:,:2]@src+a[:,2]
   self.assertTrue(np.allclose(dst,target[role],atol=.01))
 def test_native_keys_preserved(self):
  self.assertTrue(all(v['nativeKeyframesPixelExact'] for v in self.r['variants'].values()))
  self.assertTrue(self.r['sourceRGBAUnchanged'])
 def test_motion_gate_rejects_failed_visual_quality(self):
  self.assertFalse(self.r['motionCandidateGate']['passes'])
  self.assertFalse(self.r['motionCandidateGate']['selectedForProduction'])
  self.assertTrue(all(v['maxAdjacentRGBMAE']>self.r['referenceMaxAdjacentRGBMAE']
                      for name,v in self.r['variants'].items() if name!='reference'))
 def test_artist_identity_not_inferred_from_proxies(self):
  self.assertFalse(self.r['trueStrandEndpointsArtistApproved'])
  self.assertFalse(self.r['hiddenMaterialAtCrownVerified'])
  self.assertFalse(self.r['fullYawVisualAccepted'])
if __name__=='__main__':unittest.main()
