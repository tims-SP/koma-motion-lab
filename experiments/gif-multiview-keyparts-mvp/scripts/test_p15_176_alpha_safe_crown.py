import importlib.util
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).with_name('p15_176_alpha_safe_crown.py')
spec=importlib.util.spec_from_file_location('p15_176_alpha_safe_crown',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class AlphaSafeCrownTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.q=m.run(save=False)
 def test_three_views_have_independent_rgba_assets(self):
  self.assertTrue(self.q['gate']['allThreePairsPresent'])
  for a in m.KEYS:
   folder=m.OUT/m.TAGS[a]
   for name in ('ahoge.png','crown-motion-underpaint.png','crown-static-alpha-safe.png'):
    with Image.open(folder/name) as im:
     self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(443,443))
 def test_static_alpha_over_has_no_double_owned_pixels(self):
  self.assertTrue(self.q['gate']['noDoubleAlphaOwnership'])
  self.assertTrue(self.q['gate']['staticCrownTransparentUnderStrand'])
  self.assertTrue(self.q['gate']['standardAlphaOverChangesOnlyRootBand'])
  for a in m.KEYS:
   src,strand,motion,static,owner,comp,info=m.make(a)
   self.assertTrue(np.array_equal(m.rgba_over(static,strand),comp))
   self.assertEqual(info['doubleAlphaPixels'],0)
   self.assertEqual(info['visibleDiffOutsideRootBand'],0)
 def test_motion_underpaint_keeps_reconstructed_head(self):
  self.assertTrue(self.q['gate']['motionUnderpaintRetained'])
  self.assertTrue(self.q['gate']['deepUnderpaintPreserved'])
  for a in m.KEYS:
   src,strand,motion,static,owner,comp,info=m.make(a)
   self.assertTrue(np.any(motion[owner,3]>0))
   self.assertTrue(np.array_equal(motion[125:],src[125:]))
 def test_source_key_identity_is_recorded(self):
  for a in m.KEYS:
   src=m.make(a)[0]
   self.assertEqual(self.q['perView'][f'{a:g}']['sourceSHA256'],m.hashlib.sha256(src.tobytes()).hexdigest())
 def test_visual_and_motion_gate_remains_closed(self):
  self.assertFalse(self.q['gate']['visualRootRepairApproved'])
  self.assertFalse(self.q['gate']['rootlessCrownVisualAccepted'])
  self.assertFalse(self.q['gate']['passes'])
  self.assertFalse(self.q['midYawRendered'])
  self.assertFalse(self.q['productionRendererUpdated'])
if __name__=='__main__':unittest.main()
