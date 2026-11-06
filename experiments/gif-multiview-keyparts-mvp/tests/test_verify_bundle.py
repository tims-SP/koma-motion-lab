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


    def test_frame_order_and_physical_ids(self):
        spec = importlib.util.spec_from_file_location(
            "gif_extractor", Path(__file__).resolve().parents[1] / "scripts" / "extract_keyparts.py")
        extract = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extract)
        contract = json.loads(
            (Path(__file__).resolve().parents[1] / "contract.json").read_text())
        self.assertEqual(extract.key_name("whole",4,contract),
                         ("yaw180.png",180,"head.whole"))
        self.assertEqual(extract.key_name("face",5,contract),
                         ("yaw045/face.skin.png",45,"face.skin"))
        self.assertEqual(extract.key_name("face",14,contract),
                         ("yaw090/ear.near.png",90,"ear.near"))
        self.assertEqual(extract.key_name("identity",5,contract),
                         ("yaw090/hair.clip.cross_gold.png",90,"hair.clip.cross_gold"))
        mapping=contract["identity"]["anatomicalSideMapping"]
        self.assertEqual(mapping["yaw090"]["eye.near"],"right")
        self.assertEqual(mapping["yaw090"]["hair.clip.cross_gold"],"left")

    def test_extraction_audit_requires_raw_source(self):
        spec = importlib.util.spec_from_file_location(
            "gif_extractor", Path(__file__).resolve().parents[1] / "scripts" / "extract_keyparts.py")
        extract = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extract)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            result=extract.extract(root,Path(__file__).resolve().parents[1] / "contract.json",
                                   root/"extraction-qa.json")
            self.assertEqual(result["status"],"SOURCE_FRAME_AUDIT_REQUIRED")
            self.assertEqual(result["extractedFrames"],0)
            self.assertEqual(len(result["sourceChecks"]),4)

if __name__=="__main__":
    unittest.main(verbosity=2)
