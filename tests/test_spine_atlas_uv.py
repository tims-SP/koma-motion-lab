#!/usr/bin/env python3
"""Small, independent regression tests for full atlas UV mapping."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from spine_atlas_uv import parse_atlas, to_atlas_uv, convert_mesh_uvs

ATLAS="""hero.png
size: 100,100
filter:Linear,Linear
region_0
bounds:10,20,30,40
region_90
bounds:10,20,30,40
rotate:90
region_180
bounds:10,20,30,40
rotate:180
region_270
bounds:10,20,30,40
rotate:270
trimmed
bounds:10,20,20,20
offsets:3,5,25,30
"""

class AtlasUvTests(unittest.TestCase):
    def test_parse_region_counts(self):
        x=parse_atlas(ATLAS)
        self.assertEqual(len(x),5)
        self.assertEqual(x["region_90"].degrees,90)
        self.assertEqual(x["trimmed"].original_width,25)
    def test_unrotated(self):
        r=parse_atlas(ATLAS)["region_0"]
        self.assertEqual(to_atlas_uv(r,0,0),(.10,.20))
        self.assertEqual(to_atlas_uv(r,1,1),(.40,.60))
    def test_rotate_90(self):
        r=parse_atlas(ATLAS)["region_90"]
        self.assertEqual(to_atlas_uv(r,0,0),(.10,.50))
        self.assertEqual(to_atlas_uv(r,1,1),(.50,.20))
    def test_rotate_180(self):
        r=parse_atlas(ATLAS)["region_180"]
        self.assertEqual(to_atlas_uv(r,0,0),(.40,.60))
        self.assertEqual(to_atlas_uv(r,1,1),(.10,.20))
    def test_rotate_270(self):
        r=parse_atlas(ATLAS)["region_270"]
        self.assertEqual(to_atlas_uv(r,0,0),(.50,.20))
        self.assertEqual(to_atlas_uv(r,1,1),(.10,.50))
    def test_trimmed(self):
        r=parse_atlas(ATLAS)["trimmed"]
        self.assertEqual(to_atlas_uv(r,0,0),(.07,.15))
        self.assertEqual(to_atlas_uv(r,1,1),(.32,.45))
    def test_missing_fails_closed(self):
        with self.assertRaises(KeyError):
            convert_mesh_uvs([(0,0)],atlas=parse_atlas(ATLAS),
                attachment={},attachment_name="missing",expected_page="hero.png")
    def test_attachment_path_override(self):
        uv,region=convert_mesh_uvs([(0,0)],atlas=parse_atlas(ATLAS),
            attachment={"path":"region_90"},attachment_name="wrong",expected_page="hero.png")
        self.assertEqual(region.name,"region_90")
        self.assertEqual(uv[0],(.1,.5))

if __name__=="__main__":
    unittest.main(verbosity=2)
