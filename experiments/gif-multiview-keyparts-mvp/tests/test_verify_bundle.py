#!/usr/bin/env python3
"""Technical fixtures only; no synthetic image can satisfy art review."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "verify_bundle.py"
SPEC = importlib.util.spec_from_file_location("verify_bundle", SOURCE)
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)

class TestP0Ingestion(unittest.TestCase):
    def test_native_alpha_and_bbox(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"part.png"
            image = Image.new("RGBA", (1024, 1024))
            ImageDraw.Draw(image).ellipse((300,280,650,700), fill=(190,95,140,220))
            image.save(path)
            stats = verify.layer_stats(path)
            self.assertEqual(stats["bbox"], [300,280,651,701])
            self.assertGreater(stats["softAlphaPixels"],10)
            self.assertTrue(stats["transparentCorners"])
            self.assertEqual(len(verify.sha256(path)),64)

    def test_palette_conversion_does_not_count_as_native(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"bad.png"
            Image.new("P",(1024,1024)).save(path)
            with self.assertRaisesRegex(ValueError,"RGBA"):
                verify.layer_stats(path)

    def test_wrong_canvas(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"wrong.png"
            Image.new("RGBA",(512,511)).save(path)
            with self.assertRaisesRegex(ValueError,"1024"):
                verify.layer_stats(path)

    def test_artmesh_topology(self):
        mesh={"vertexIds":["tl","tr","br","bl"],
              "vertices":[[300,280],[650,280],[650,700],[300,700]],
              "triangles":[[0,1,2],[0,2,3]]}
        self.assertEqual(verify.check_mesh(mesh)["triangles"],2)
        with self.assertRaises(ValueError):
            verify.check_mesh({**mesh,"vertexIds":["tl","tl","br","bl"]})
        with self.assertRaises(ValueError):
            verify.check_mesh({**mesh,"triangles":[[0,1,1],[0,2,3]]})

    def test_anatomical_anchors(self):
        anchors=[{"id":"tip","xy":[320,410]},{"id":"root","xy":[370,410]},
                 {"id":"middle","xy":[340,430]}]
        self.assertEqual(len(verify.check_anchors(anchors)),3)
        anchors[2]["xy"]=[340,410]
        with self.assertRaisesRegex(ValueError,"collinear"):
            verify.check_anchors(anchors)

    def test_missing_raw_assets_closes_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/"report.json"
            report=verify.run(Path(directory)/"assets",out)
            self.assertEqual(report["status"],"BLOCKED_SOURCE_ASSETS")
            self.assertEqual(report["passed"],0)
            self.assertGreater(report["failed"],0)
            self.assertEqual(json.loads(out.read_text())["failed"],report["failed"])

    def test_wrong_gif_count_and_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            path=root/"gifs"/"face.gif"
            path.parent.mkdir()
            frames=[Image.new("RGBA",(120,120)) for _ in range(2)]
            frames[0].putpixel((60,60),(200,100,130,255))
            frames[1].putpixel((40,40),(200,100,130,255))
            frames[0].save(path,save_all=True,append_images=frames[1:],duration=200,disposal=2)
            report=verify.run(root,root/"report.json")
            gates={a["name"]:a for a in report["checks"]}
            self.assertFalse(gates["gif_count_face"]["pass"])
            self.assertFalse(gates["gif_canvas_face"]["pass"])
            self.assertNotEqual(report["status"],"PASS_ENGINEERING_AND_VISUAL_GATES")

if __name__=="__main__":
    unittest.main(verbosity=2)
