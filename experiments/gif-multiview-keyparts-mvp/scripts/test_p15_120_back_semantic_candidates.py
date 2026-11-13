from pathlib import Path
import importlib.util,unittest
p=Path(__file__).with_name('p15_120_back_semantic_candidates.py')
s=importlib.util.spec_from_file_location('p15_120_back_semantic_candidates',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_native_partition(self):
  for angle in (135,180):
   r=m.segment(angle,write=False)
   self.assertTrue(r['pixelReconstructionExact'])
   self.assertTrue(r['alphaExclusive'])
   self.assertGreater(r['pixelCounts']['hair.visible'],15000)
   self.assertGreater(r['pixelCounts']['garment.visible'],10000)
 def test_skin_and_source(self):
  for angle in (135,180):
   r=m.segment(angle,write=False)
   self.assertEqual(len(r['sha256']),64)
   self.assertFalse(r['physicalUnderpaintExists'])
if __name__=='__main__':unittest.main()
