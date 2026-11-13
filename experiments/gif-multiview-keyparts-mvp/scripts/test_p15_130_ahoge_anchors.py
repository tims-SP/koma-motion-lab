import importlib.util,unittest
from pathlib import Path
import numpy as np
path=Path(__file__).with_name('p15_130_ahoge_anchors.py')
spec=importlib.util.spec_from_file_location('p15_130_ahoge_anchors',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AhogeAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=m.make(save=False)
    def test_proxy_anchors_exist(self):
        self.assertEqual(set(self.result['sourceAnchorPixels']),{'90.0','112.5','135.0'})
        for point in self.result['sourceAnchorPixels'].values():
            self.assertTrue(all(0<=v<443 for v in point))
    def test_endpoints_source_exact(self):
        self.assertTrue(self.result['nativeKeyframesPixelExact'])
        self.assertEqual(len(self.result['trajectories']),5)
        for step in self.result['trajectories']:
            if step['yaw'] in m.KEYS:self.assertEqual(step['deltaXY'],[0,0])
    def test_no_claim_of_true_physical_anchor(self):
        self.assertFalse(self.result['physicalRootTipCorrespondenceVerified'])
        self.assertFalse(self.result['garmentAnchorVerified'])
        self.assertFalse(self.result['visualAccepted'])
    def test_composite_keeps_lower_pixels(self):
        a=np.zeros((443,443,4),dtype=np.uint8)
        b=a.copy();b[...,0]=200;b[...,3]=255
        out=m.compose_head_top(a,b)
        self.assertTrue(np.array_equal(out[93:],a[93:]))
        self.assertTrue(np.array_equal(out[:35],b[:35]))
if __name__=='__main__':unittest.main()
