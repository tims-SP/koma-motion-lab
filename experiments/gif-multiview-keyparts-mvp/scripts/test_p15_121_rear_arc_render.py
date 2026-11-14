import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('p15_121_rear_arc_render.py')
s=importlib.util.spec_from_file_location('p15_121_rear_arc_render',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestRearArc(unittest.TestCase):
 def test_key_angles_and_provenance(self):
  self.assertEqual(m.KEYS,(90,135,180))
  self.assertEqual(len(m.ANGLES),9)
  self.assertEqual([m.ANGLES[i] for i in (0,4,8)],[90,135,180])
  self.assertTrue(all((m.P/f'extracted/whole/yaw{a:03}.png').is_file() for a in m.KEYS))
 def test_native_compositing(self):
  import numpy as np
  a=m.load()[90]
  self.assertTrue(np.array_equal(m.blend(a,a,0),a) or np.max(np.abs(m.blend(a,a,0).astype(int)-a.astype(int)))<=1)
if __name__=='__main__': unittest.main()
