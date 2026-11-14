import importlib.util,unittest
from pathlib import Path
s=Path(__file__).with_name('p15_133_semantic_layer_source.py')
spec=importlib.util.spec_from_file_location('p15_133_semantic_layer_source',s)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SemanticSourceTests(unittest.TestCase):
 def test_all_angles_recompose_without_data_loss(self):
  for angle in (90.,112.5,135.):
   result=m.split(angle,write=False)
   self.assertTrue(result['recompositionByteExact'])
   self.assertEqual(result['paintedHiddenPixels'],0)
   self.assertEqual(sum(result['layerVisiblePixelCounts'].values()),result['sourceAlphaPixels'])
 def test_expected_role_coverage(self):
  self.assertEqual(len(m.ROLES),5)
  mid=m.split(112.5,write=False)
  self.assertGreater(mid['layerVisiblePixelCounts']['hair.visible'],10000)
  self.assertGreater(mid['layerVisiblePixelCounts']['skin.visible'],1000)
 def test_separation_not_formal_artmesh(self):
  self.assertFalse('artist-approved' in m.split(112.5,write=False)['semanticClass'])
if __name__=='__main__':unittest.main()
