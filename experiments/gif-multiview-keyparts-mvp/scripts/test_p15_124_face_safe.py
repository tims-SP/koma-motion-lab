import importlib.util,unittest
from pathlib import Path
import numpy as np
p=Path(__file__).with_name('p15_124_face_safe.py')
s=importlib.util.spec_from_file_location('p15_124_face_safe',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestFaceSafe(unittest.TestCase):
 def test_keyframes_exact(self):
  keys=m.load()
  for a in m.KEYS:self.assertTrue(np.array_equal(m.compose(a),keys[a]))
 def test_head_source_retention(self):
  for a in (112.5,157.5):
   o=m.compose(a)
   ref=m.source(a,'122-source-owned')
   self.assertTrue(np.array_equal(o[:300],ref[:300]))
 def test_rgba_composition(self):
  a=np.zeros((4,4,4),dtype=np.uint8);a[:,:,0]=255;a[:,:,3]=255
  b=np.zeros_like(a);b[:,:,2]=255;b[:,:,3]=255
  result=m.blend_premultiplied(a,b,np.full((4,4,1),.5,dtype=np.float32))
  self.assertTrue(np.all(result[...,3]==255))
if __name__=='__main__':unittest.main()
