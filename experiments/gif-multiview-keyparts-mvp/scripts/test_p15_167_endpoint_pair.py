import importlib.util,unittest,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).with_name('p15_167_endpoint_pair.py')
spec=importlib.util.spec_from_file_location('p15_167_endpoint_pair',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class EndpointPairTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.qa=m.render(save=False)
 def test_old_root_is_outside_painted_art(self):
  self.assertEqual(self.qa['legacyLandmarkDiagnostic']['sourceAlphaAtLegacyYaw112p5Root'],0)
  self.assertGreater(self.qa['keyviewPairs']['112.5']['sourceAlphaAtRoot'],200)
 def test_each_original_view_roundtrip_exact(self):
  source=m.keyframes()
  for a in m.KEYS:
   strand,crown,owned,meta=m.pair(source[a],a)
   reconstructed=crown.copy()
   reconstructed[owned]=strand[owned]
   self.assertTrue(np.array_equal(reconstructed,source[a]))
   self.assertEqual(meta['sourceSHA256RGBA'] if 'sourceSHA256RGBA' in meta else hashlib.sha256(source[a].tobytes()).hexdigest(),self.qa['keyviewPairs'][f'{a:g}']['sourceSHA256RGBA'])
   self.assertEqual(hashlib.sha256(strand.tobytes()).hexdigest(),self.qa['keyviewPairs'][f'{a:g}']['strandSHA256RGBA'])
   self.assertEqual(hashlib.sha256(crown.tobytes()).hexdigest(),self.qa['keyviewPairs'][f'{a:g}']['crownSHA256RGBA'])
 def test_root_material_and_free_tip_source_coverage(self):
  self.assertTrue(self.qa['gate']['allSourcePairsHaveRootMaterial'])
  self.assertTrue(self.qa['gate']['rootAnchorHasSourceAlpha'])
  self.assertTrue(self.qa['gate']['allSourceLoopMasksConnected'])
  self.assertTrue(self.qa['gate']['allSecondEndpointsAboveCrown'])
  for result in self.qa['keyviewPairs'].values():
   self.assertGreater(result['aboveCrownPixels'],900)
   self.assertGreater(result['rootSourcePixels'],30)
   self.assertTrue(result['headBelowY120Exact'])
 def test_intermediate_compositing_retains_native_keys(self):
  self.assertEqual(self.qa['renderAngles'],[90,101.25,112.5,123.75,135])
  self.assertTrue(self.qa['candidate']['originalKeyviewsPixelExact'])
  self.assertTrue(self.qa['gate']['preservesIntermediateCrownAlpha'])
  self.assertGreater(self.qa['candidate']['maxAdjacentRGBMAE'],self.qa['reference']['maxAdjacentRGBMAE'])
  self.assertEqual(self.qa['candidate']['topConnectedComponents'][1],2)
  self.assertFalse(self.qa['gate']['bothMidviewsSingleComponent'])
 def test_source_underpaint_and_artist_gates(self):
  self.assertTrue(self.qa['hiddenCrownGeneratedByInpainting'])
  self.assertFalse(self.qa['endpointLabelsArtistApproved'])
  self.assertFalse(self.qa['physicalHairRigAccepted'])
  self.assertFalse(self.qa['continuousYawVisualAccepted'])
  self.assertFalse(self.qa['productionRendererChanged'])
  self.assertFalse(self.qa['gate']['passes'])

if __name__=='__main__': unittest.main()
