import importlib.util, unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_158_loop_correspondence.py')
spec=importlib.util.spec_from_file_location('p15_158_loop_correspondence',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LoopAnchorCorrespondenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.evaluate(save=False)
 def test_source_geometry_and_affine_anchors(self):
  for a,b in ((90.,112.5),(112.5,135.)):
   source=m.anchors(a)
   dest=m.anchors(a)*.5+m.anchors(b)*.5
   mat=m.similarity(source,dest)
   reconstructed=source@mat[:,:2].T+mat[:,2]
   self.assertTrue(np.allclose(reconstructed,dest,atol=.001))
 def test_all_three_original_keys_pixel_exact(self):
  self.assertTrue(self.q['sourceKeyframesUnmodified'])
  self.assertEqual(self.q['sampleAngles'],[90,101.25,112.5,123.75,135])
  for variant in self.q['variants'].values():
   self.assertTrue(variant['nativeKeyframesPixelExact'])
 def test_loop_mask_fusion_is_weak(self):
  for label in ('mask_1','mask_3','mask_5'):
   self.assertLess(self.q['variants'][label]['intermediate']['101.25']['maskPixels'],250)
   self.assertGreater(self.q['variants'][label]['topConnectedComponents'][1],1)
 def test_nearest_owner_retains_source_material(self):
  q=self.q['variants']['nearest_owner']
  self.assertGreater(q['intermediate']['101.25']['maskPixels'],800)
  self.assertGreater(q['maxAdjacentRGBMAE'],self.q['reference']['maxAdjacentRGBMAE'])
 def test_gate_rejects_failed_visual_output(self):
  self.assertFalse(self.q['acceptanceGate']['passes'])
  self.assertFalse(self.q['physicalAnchorApproval'])
  self.assertFalse(self.q['artistVerifiedHairCurve'])
  self.assertFalse(self.q['matchedUnderpaintAvailable'])
  self.assertFalse(self.q['fullFrameVisualAccepted'])
if __name__=='__main__':unittest.main()
