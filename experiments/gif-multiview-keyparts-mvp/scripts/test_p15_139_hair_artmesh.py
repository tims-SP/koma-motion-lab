import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_139_hair_artmesh.py')
spec=importlib.util.spec_from_file_location('p15_139_hair_artmesh',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class HairArtMeshTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=m.evaluate(save=False)
 def test_positive_triangle_areas(self):
  self.assertEqual(self.r['vertexCount'],400)
  self.assertEqual(self.r['triangleCount'],722)
  for result in self.r['geometryQuality'].values():
   self.assertEqual(result['folds'],0)
   self.assertGreater(result['minSignedArea'],1)
 def test_identical_key_material(self):
  self.assertTrue(self.r['sourcePixelSplitExact'])
  self.assertTrue(self.r['sourceKeyframeUnmodified'])
  self.assertTrue(self.r['nativeUnderpaintUnmodified'])
 def test_displacement_improves_local_coverage(self):
  a=self.r['composites']
  for displacement in ('12','24'):
   self.assertLess(a['hybrid_mesh'][displacement]['holes']['all'],
                   a['hybrid_translation'][displacement]['holes']['all'])
   self.assertLess(a['hybrid_mesh'][displacement]['rgbMAE'],
                   a['hybrid_translation'][displacement]['rgbMAE'])
 def test_mesh_pixel_identity_when_undeformed(self):
  v,f=m.geometry()
  from p15_135_closed_hair_mask import closed_mask,split
  from p15_134_underpaint_probe import rgba,SOURCE
  source=rgba(SOURCE);mask,_=closed_mask(source);hair,_=split(source,mask)
  self.assertTrue(np.array_equal(m.deform(v,0),v))
  self.assertTrue(np.array_equal(m.warp_triangles(hair,v,v,f),hair))
 def test_cross_view_validation_not_assumed(self):
  self.assertFalse(self.r['realCrossViewCorrespondence'])
  self.assertFalse(self.r['actualYawTransitionAccepted'])
  self.assertFalse(self.r['artistApprovedTopology'])
  self.assertFalse(self.r['visualAcceptance'])
if __name__=='__main__':unittest.main()
