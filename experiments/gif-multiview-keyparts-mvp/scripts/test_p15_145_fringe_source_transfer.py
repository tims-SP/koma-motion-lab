import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_145_fringe_source_transfer.py')
s=importlib.util.spec_from_file_location('p15_145_fringe_source_transfer',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class FringeSourceTransferTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.audit(save=False)
 def test_canonical_owned_pixels(self):
  source=m.rgba(m.SOURCE)
  registered=m.rgba(m.PRIOR/'registered-bangs.png')
  mask=m.old_bangs_mask(source)
  for weight in m.PARAMS:
   out,weights=m.paint_registered(source,registered,mask,weight)
   self.assertTrue(np.array_equal(out[...,3],source[...,3]))
   self.assertTrue(np.array_equal(out[~mask],source[~mask]))
   self.assertTrue(np.array_equal(out[m.eye_mask()],source[m.eye_mask()]))
   self.assertTrue(np.all(weights[~mask]==0))
 def test_source_partition_exact(self):
  src=m.rgba(m.SOURCE)
  mask=m.old_bangs_mask(src)
  hair,remaining=m.cutout(src,mask)
  reconstructed=remaining.copy();reconstructed[mask]=hair[mask]
  self.assertTrue(np.array_equal(reconstructed,src))
 def test_native_endpoints_preserved(self):
  self.assertTrue(all(v['native90And135Exact'] for v in self.qa['variants'].values()))
  self.assertTrue(self.qa['sourceMaskRecompositionExact'])
 def test_transfer_does_not_create_new_alpha_holes(self):
  samples=self.qa['variants']
  baseline=samples['canonical']['stress']['24']['alphaHoles']
  self.assertTrue(all(s['stress']['24']['alphaHoles']==baseline for s in samples.values()))
 def test_midpoint_continuity_metric(self):
  q=self.qa['variants']
  self.assertLess(q['transfer_050']['maxAdjacentRGBMAE'],q['canonical']['maxAdjacentRGBMAE'])
  self.assertFalse(self.qa['artistApprovedStrandIdentity'])
  self.assertFalse(self.qa['fullYawVisualAccepted'])
 def test_originals_are_unchanged(self):
  self.assertTrue(self.qa['sourceKeyRGBAUnmodified'])
  self.assertTrue(self.qa['eyesProtected'])
if __name__=='__main__':unittest.main()
