#!/usr/bin/env python3
"""Pixel-ownership and deformation engineering fixtures; not visual art approval."""
import importlib.util
import sys
import unittest
from pathlib import Path

HAS_VISION=(importlib.util.find_spec("numpy") is not None and
            importlib.util.find_spec("cv2") is not None)

@unittest.skipUnless(HAS_VISION,"OpenCV and NumPy are required for vision fixtures")
class P0CandidateGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        cls.np=np
        path=Path(__file__).resolve().parents[1]/"scripts"
        for name,file in [("partition","build_semantic_partition.py"),
                          ("flow","flow_render.py")]:
            spec=importlib.util.spec_from_file_location(name,path/file)
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            setattr(cls,name,module)

    def image(self):
        np=self.np
        image=np.zeros((443,443,4),dtype=np.uint8)
        image[90:320,75:360]=[202,128,168,255]
        image[190:305,160:300]=[252,224,213,255]
        image[130:153,290:316]=[225,185,79,255]
        return image

    def test_visible_pixels_have_single_semantic_owner(self):
        im=self.image()
        for yaw in [0,45,90]:
            labels=self.partition.segment(im,yaw)
            self.assertTrue(self.np.all(labels[im[:,:,3]>0]<len(self.partition.IDS)))
            self.assertTrue(self.np.all(labels[im[:,:,3]==0]==255))

    def test_clip_visibility_is_anatomically_stable(self):
        im=self.image()
        x,y=300,141
        for yaw in [0,45]:
            self.assertEqual(int(self.partition.segment(im,yaw)[y,x]),
                             self.partition.IDS.index("hair.clip.cross_gold"))
        self.assertNotEqual(int(self.partition.segment(im,90)[y,x]),
                            self.partition.IDS.index("hair.clip.cross_gold"))

    def test_full_view_raster_can_be_losslessly_partitioned(self):
        im=self.image()
        labels=self.partition.segment(im,0)
        result=self.np.zeros_like(im)
        for k in range(len(self.partition.IDS)):
            choose=labels==k
            part=self.np.zeros_like(im)
            part[choose]=im[choose]
            result[choose]=part[choose]
        self.assertTrue(self.np.array_equal(result,im))

    def test_flow_endpoints_and_constant_identity(self):
        np=self.np
        image=self.image()
        zero=np.zeros((443,443,2),dtype=np.float32)
        yy,xx=np.indices((443,443),dtype=np.float32)
        grid=np.stack((xx,yy),axis=2)
        self.assertTrue(np.array_equal(self.flow.morph(image,image,zero,zero,0,grid),image))
        self.assertTrue(np.array_equal(self.flow.morph(image,image,zero,zero,1,grid),image))
        result=self.flow.morph(image,image,zero,zero,0.5,grid)
        self.assertLessEqual(int(np.abs(result.astype(np.int16)-image.astype(np.int16)).max()),1)

if __name__=="__main__":
    unittest.main()
