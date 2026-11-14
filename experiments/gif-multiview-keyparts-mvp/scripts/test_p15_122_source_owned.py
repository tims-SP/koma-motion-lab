import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_122_source_owned.py');s=importlib.util.spec_from_file_location('p15_122_source_owned',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestOwner(unittest.TestCase):
 def test_clear_alpha(self):
  f=m.warp_source(np.zeros((8,8,4),dtype=np.uint8),np.zeros((8,8,2),dtype=np.float32),0.5,np.stack(np.indices((8,8),dtype=np.float32)[::-1],axis=-1))
  self.assertTrue(np.all(f==0))
 def test_native_keys(self):
  self.assertEqual(m.KEYS,(90,135,180))
  self.assertEqual(len(m.ANGLES),9)
if __name__=='__main__':unittest.main()
