import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_146_strand_identity.py')
spec=importlib.util.spec_from_file_location('p15_146_strand_identity',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class StrandIdentityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=m.audit(save=False)
 def test_provisional_strand_pixel_partition(self):
  for a in m.KEYS:
   original,pieces,remaining,masks,combined=m.view_parts(a)
   self.assertEqual(set(pieces),set(m.LABELS))
   counts=sum(v.astype(np.uint8) for v in masks.values())
   self.assertTrue(np.array_equal(counts,combined.astype(np.uint8)))
   reconstructed=remaining.copy()
   for label,mask in masks.items():
    reconstructed[mask]=pieces[label][mask]
   self.assertTrue(np.array_equal(reconstructed,original))
   self.assertTrue(all(mask.sum()>2000 for mask in masks.values()))
 def test_no_face_pixel_ownership(self):
  for a in m.KEYS:
   _,_,_,masks,_=m.view_parts(a)
   protected=m.protect_mask(a,strength=1.25)
   for mask in masks.values():
    self.assertFalse(np.any(mask&protected))
 def test_native_keyframes_and_nonfolding(self):
  for candidate in self.q['methods'].values():
   self.assertTrue(candidate['nativeKeysPixelExact'])
   for r in candidate['meshGeometry'].values():
    self.assertEqual(r['folds'],0)
    self.assertGreater(r['minimumTriangleArea'],0)
 def test_failed_candidate_gate_is_enforced(self):
  self.assertFalse(self.q['motionCandidateGate']['passes'])
  self.assertFalse(self.q['motionCandidateGate']['selectedForProduction'])
  self.assertTrue(all(r['maxAdjacentRGBMAE']>self.q['referenceP15_145']['maxAdjacentRGBMAE']
                      for r in self.q['methods'].values()))
 def test_source_art_status_is_accurate(self):
  self.assertTrue(self.q['sourceArtPreserved'])
  self.assertTrue(self.q['pixelPerfectSourceReassembly'])
  self.assertFalse(self.q['artistApprovedStrandLabels'])
  self.assertFalse(self.q['trueAnatomicalRootTipCorrespondenceVerified'])
  self.assertFalse(self.q['fullYawVisualAccepted'])
if __name__=='__main__':unittest.main()
