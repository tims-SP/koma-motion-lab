"""Unit tests for CORE-023 Task A deterministic canonicalization (v2)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import canonicalize_candidates as cc  # noqa: E402

CONFIG = ROOT / "config" / "canonicalization-v2.json"


def sha(path: Path) -> str:
    return cc.sha256_file(path)


def write_image(path: Path, size=(200, 200), box=(20, 20, 60, 60), bg=(255, 255, 255),
                fg=(20, 20, 20)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", size, bg)
    ImageDraw.Draw(im).rectangle(box, fill=fg)
    im.save(path, format="PNG")


def write_transparent_palette_png(path: Path) -> None:
    """Indexed-color PNG: palette[0] is black and index 0 is transparent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("P", (8, 8))
    im.putpalette([0, 0, 0] + [255, 0, 0] * 255)
    im.info["transparency"] = 0
    im.putpixel((0, 0), 0)
    im.save(path, format="PNG", transparency=0)


def build_world(root: Path, blank_candidate: bool = False):
    """Synthetic input tree mirroring the real out/ + evidence/ layout."""
    out = root / "out"
    ev = root / "evidence"
    src = out / "identity" / "source_A_aka_front.png"
    a = out / "candidates" / "pilot-A-001.png"
    c = out / "candidates" / "pilot-C-001.png"
    write_image(src)
    # candidates: wrong canvas and ink touching the edge -> original framing FAIL
    write_image(a, size=(300, 300), box=(0, 0, 120, 120))
    write_image(c, size=(300, 300), box=(0, 0, 120, 120))
    if blank_candidate:
        Image.new("RGB", (300, 300), (255, 255, 255)).save(c, format="PNG")
    (out / "identity" / "reference_manifest.json").write_text(json.dumps({
        "image_A": "source_A_aka_front.png", "image_A_sha256": sha(src)}))
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "candidate-manifest.json").write_text(json.dumps({
        "candidates": [
            {"candidate_id": "pilot-A-001", "sha256": sha(a)},
            {"candidate_id": "pilot-C-001", "sha256": sha(c)},
        ]}))
    (ev / "source_freeze.json").write_text(json.dumps({
        "schema": "koma-source-freeze/1",
        "identity_file": "identity/source_A_aka_front.png",
        "identity_sha256": sha(src),
    }))
    return out, ev


def rewrite_candidate_hash(ev: Path, candidate_id: str, path: Path) -> None:
    data = json.loads((ev / "candidate-manifest.json").read_text())
    for entry in data["candidates"]:
        if entry["candidate_id"] == candidate_id:
            entry["sha256"] = sha(path)
    (ev / "candidate-manifest.json").write_text(json.dumps(data))


class CanonicalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="core023-"))
        self.out, self.ev = build_world(self.tmp)
        self.outdir = self.tmp / "runtime"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---------------------------------------------------------------- geometry
    def test_matrix_round_trip(self):
        cfg = cc.load_config(CONFIG)
        tr = cc.fit_transform(640, 480, cfg)
        f = tr["source_to_canonical"]
        i = tr["canonical_to_source"]
        for pt in [(0.0, 0.0), (123.5, 77.25), (639.5, 479.5)]:
            x, y = pt
            cx = f["a"] * x + f["b"] * y + f["c"]
            cy = f["d"] * x + f["e"] * y + f["f"]
            bx = i["a"] * cx + i["b"] * cy + i["c"]
            by = i["d"] * cx + i["e"] * cy + i["f"]
            self.assertAlmostEqual(bx, x, places=9)
            self.assertAlmostEqual(by, y, places=9)
        self.assertGreaterEqual(tr["offset_px"][0], cfg["min_margin_px"] - 1e-9)
        self.assertGreaterEqual(tr["offset_px"][1], cfg["min_margin_px"] - 1e-9)

    def test_pillow_bicubic_marker_geometry(self):
        """Supervisor case: 4x4 marker at (1,1), scale=4, translation=4.

        The edge-domain inverse tuple (0.25,0,-1,0,0.25,-1) must place the
        source pixel footprint at output block 8..11 with centroid 9.5, with
        NO extra half-pixel shift.
        """
        im = Image.new("RGB", (4, 4), (255, 255, 255))
        im.putpixel((1, 1), (0, 0, 0))
        matrix = {"a": 0.25, "b": 0.0, "c": -1.0, "d": 0.0, "e": 0.25, "f": -1.0}
        out = cc.transform_with_matrix(im, (20, 20), matrix, (255, 255, 255))
        arr = np.asarray(out)
        ys, xs = np.where(arr.min(axis=2) < 128)
        self.assertEqual((int(xs.min()), int(xs.max())), (8, 11))
        self.assertEqual((int(ys.min()), int(ys.max())), (8, 11))
        self.assertAlmostEqual(float(xs.mean()), 9.5, places=6)
        self.assertAlmostEqual(float(ys.mean()), 9.5, places=6)

    def test_fit_transform_uses_edge_domain_inverse(self):
        """The inverse fed to Pillow must be the edge-domain inverse (no shift)."""
        cfg = cc.load_config(CONFIG)
        tr = cc.fit_transform(4, 4, cfg)
        inv = tr["canonical_to_source"]
        self.assertAlmostEqual(inv["a"], 1.0 / tr["scale"], places=12)
        self.assertAlmostEqual(inv["c"], -tr["offset_px"][0] / tr["scale"], places=12)

    # ------------------------------------------------------- alpha compositing
    def test_transparent_palette_png_composites_over_white(self):
        """P-mode PNG with palette[0]=black and transparency=0 must load white."""
        p = self.tmp / "p.png"
        write_transparent_palette_png(p)
        rgb = cc.load_rgb(p)
        self.assertEqual(rgb.mode, "RGB")
        self.assertEqual(rgb.getpixel((0, 0)), (255, 255, 255))

    def test_rgba_transparent_composites_over_white(self):
        p = self.tmp / "rgba.png"
        Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(p, format="PNG")
        self.assertEqual(cc.load_rgb(p).getpixel((0, 0)), (255, 255, 255))

    def test_blank_transparent_candidate_rejected(self):
        """A fully transparent candidate is blank after compositing and is rejected."""
        c = self.out / "candidates" / "pilot-C-001.png"
        Image.new("RGBA", (300, 300), (0, 0, 0, 0)).save(c, format="PNG")
        rewrite_candidate_hash(self.ev, "pilot-C-001", c)
        with self.assertRaises(cc.CanonicalizationError) as ctx:
            cc.run(self.out, self.outdir, CONFIG, self.ev)
        self.assertIn("MARGIN_OR_CANVAS_FAIL", str(ctx.exception))

    # ------------------------------------------------------------- pipeline
    def test_run_produces_derivatives_and_report(self):
        report = cc.run(self.out, self.outdir, CONFIG, self.ev)
        self.assertEqual(report["schema"], cc.REPORT_SCHEMA)
        self.assertEqual(len(report["items"]), 3)
        for item in report["items"]:
            self.assertTrue(item["hash_verified"])
            self.assertEqual(item["derivative"]["dimensions"], [1024, 1024])
            self.assertEqual(item["derivative"]["framing_gate"], "PASS")
            self.assertGreaterEqual(min(item["derivative"]["margins_ltrb_px"]), 48)
            self.assertTrue((self.outdir / item["derivative"]["file"]).exists())
            self.assertTrue(item["derivative"]["file"].endswith("-canonical-v2.png"))

    def test_original_bytes_preserved(self):
        before = {p: sha(p) for p in sorted(self.out.rglob("*.png"))}
        cc.run(self.out, self.outdir, CONFIG, self.ev)
        after = {p: sha(p) for p in sorted(self.out.rglob("*.png"))
                 if p.parent != self.outdir / "canonical"}
        self.assertEqual(before, after)

    def test_deterministic_output(self):
        r1 = cc.run(self.out, self.outdir / "r1", CONFIG, self.ev)
        r2 = cc.run(self.out, self.outdir / "r2", CONFIG, self.ev)
        h1 = {i["id"]: i["derivative"]["sha256"] for i in r1["items"]}
        h2 = {i["id"]: i["derivative"]["sha256"] for i in r2["items"]}
        self.assertEqual(h1, h2)
        self.assertEqual((self.outdir / "r1" / "report.json").read_text().replace("r1", "rX"),
                         (self.outdir / "r2" / "report.json").read_text().replace("r2", "rX"))

    def test_missing_input_fails_closed(self):
        (self.out / "candidates" / "pilot-A-001.png").unlink()
        with self.assertRaises(cc.CanonicalizationError):
            cc.run(self.out, self.outdir, CONFIG, self.ev)

    def test_hash_mismatch_fails_closed(self):
        p = self.out / "candidates" / "pilot-C-001.png"
        write_image(p, size=(300, 300), box=(10, 10, 90, 90))
        with self.assertRaises(cc.CanonicalizationError) as ctx:
            cc.run(self.out, self.outdir, CONFIG, self.ev)
        self.assertIn("HASH_MISMATCH", str(ctx.exception))

    def test_invalid_config_fails_closed(self):
        bad = self.tmp / "bad.json"
        cfg = cc.load_config(CONFIG)
        cfg["resampling"] = "MAGIC"
        bad.write_text(json.dumps(cfg))
        with self.assertRaises(cc.CanonicalizationError):
            cc.run(self.out, self.outdir, bad, self.ev)

    def test_unsupported_transform_and_color_settings_rejected(self):
        for key, value in (("transform", "rotation 45 degrees"),
                           ("color_handling", "linearize to scRGB"),
                           ("coordinate_domain", "pixel_index_centers"),
                           ("derivative_naming", "whatever")):
            bad = self.tmp / f"bad-{key}.json"
            cfg = cc.load_config(CONFIG)
            cfg[key] = value
            bad.write_text(json.dumps(cfg))
            with self.assertRaises(cc.CanonicalizationError) as ctx:
                cc.load_config(bad)
            self.assertIn("CONFIG_INVALID", str(ctx.exception))

    def test_scalar_settings_reject_empty_and_partial_strings(self):
        """Scalar settings are compared by exact equality, not substring membership.

        Empty and partial strings must be rejected for transform, color_handling
        and coordinate_domain, while the unmodified v2 config still loads.
        """
        for key in ("transform", "color_handling", "coordinate_domain"):
            supported = getattr(cc, {
                "transform": "SUPPORTED_TRANSFORM",
                "color_handling": "SUPPORTED_COLOR_HANDLING",
                "coordinate_domain": "SUPPORTED_COORDINATE_DOMAIN",
            }[key])
            for bad_value in ("", supported[:len(supported) // 2],
                              supported[:max(1, len(supported) // 2)]):
                with self.subTest(key=key, value=bad_value):
                    bad = self.tmp / f"bad-scalar-{key}.json"
                    cfg = cc.load_config(CONFIG)
                    cfg[key] = bad_value
                    bad.write_text(json.dumps(cfg))
                    with self.assertRaises(cc.CanonicalizationError) as ctx:
                        cc.load_config(bad)
                    self.assertIn("CONFIG_INVALID", str(ctx.exception))
        # The normal v2 config still loads unchanged.
        loaded = cc.load_config(CONFIG)
        self.assertEqual(loaded["fit"], cc.SUPPORTED_FIT[0])
        self.assertIn(loaded["fit"], cc.SUPPORTED_FIT)

    def test_unknown_config_key_rejected(self):
        bad = self.tmp / "bad-unknown.json"
        cfg = cc.load_config(CONFIG)
        cfg["rotation_deg"] = 15
        bad.write_text(json.dumps(cfg))
        with self.assertRaises(cc.CanonicalizationError):
            cc.load_config(bad)

    def test_config_type_and_range_validation(self):
        for mutate in (lambda c: c.update(min_margin_px="48"),
                       lambda c: c.update(ink_threshold_rgb_min=0),
                       lambda c: c.update(fit_inset_px=-1),
                       lambda c: c["canvas"].update(width=0),
                       lambda c: c["canvas"].update(background_rgb=[255, 255]),
                       lambda c: c["canvas"].update(mode="RGBA"),
                       lambda c: c["canvas"].update(alpha="keep transparency")):
            cfg = cc.load_config(CONFIG)
            mutate(cfg)
            bad = self.tmp / "bad-types.json"
            bad.write_text(json.dumps(cfg))
            with self.assertRaises(cc.CanonicalizationError):
                cc.load_config(bad)

    def test_invalid_transform_fails_closed(self):
        cfg = cc.load_config(CONFIG)
        cfg["min_margin_px"] = 600
        with self.assertRaises(cc.CanonicalizationError):
            cc.fit_transform(200, 200, cfg)

    def test_framing_gate_records_original_fail(self):
        report = cc.run(self.out, self.outdir, CONFIG, self.ev)
        summary = report["original_frame_gate_summary"]
        self.assertEqual(summary["pilot-A-001"], "FAIL")
        self.assertEqual(summary["pilot-C-001"], "FAIL")
        self.assertEqual(report["frame_gate_summary"]["pilot-A-001"], "PASS")

    def test_no_artistic_promotion(self):
        report = cc.run(self.out, self.outdir, CONFIG, self.ev)
        blob = json.dumps(report)
        self.assertEqual(report["benchmark"]["ranking"], "NONE_ACCEPTED")
        self.assertEqual(report["benchmark"]["full_ABCD_benchmark"], "NOT_TESTED")
        self.assertEqual(report["approval_state"], "NOT_APPROVED")
        self.assertFalse(report["golden"])
        for gate in ("anatomy", "identity", "angle", "style"):
            self.assertEqual(report["artistic_gates"][gate], "NOT_TESTED")
        self.assertEqual(report["artistic_gates"]["human_approval"], "MANUAL_REVIEW_REQUIRED")
        for banned in ("APPROVED", "GOLDEN"):
            self.assertNotIn(f'"status": "{banned}"', blob)
            self.assertNotIn(f'"{banned}": true', blob)

    # ------------------------------------------------------------ provenance
    def test_identity_derivative_is_derived_reference_over_source_truth(self):
        report = cc.run(self.out, self.outdir, CONFIG, self.ev)
        by_id = {i["id"]: i for i in report["items"]}
        src = by_id["source-A-aka-front"]
        self.assertEqual(src["authority"], "SOURCE_TRUTH")
        self.assertEqual(src["role"], "DERIVED_REFERENCE")
        self.assertEqual(src["provenance"]["parent_state"], "SOURCE_TRUTH")
        self.assertEqual(src["provenance"]["derivative_kind"], "DERIVED_REFERENCE")
        self.assertEqual(src["provenance"]["promotion"], "NONE")
        for cid in ("pilot-A-001", "pilot-C-001"):
            cand = by_id[cid]
            self.assertEqual(cand["authority"], "GENERATED_CANDIDATE")
            self.assertNotEqual(cand["role"], "DERIVED_REFERENCE")
            self.assertEqual(cand["provenance"]["parent_state"], "GENERATED_CANDIDATE")

    # ------------------------------------------------- hash authority / forge
    def test_forged_runtime_manifest_cannot_bypass_committed_hash(self):
        """Replace the image AND the runtime manifest: the committed freeze wins."""
        src = self.out / "identity" / "source_A_aka_front.png"
        write_image(src, size=(200, 200), box=(30, 30, 90, 90))
        (self.out / "identity" / "reference_manifest.json").write_text(json.dumps({
            "image_A": "source_A_aka_front.png", "image_A_sha256": sha(src)}))
        with self.assertRaises(cc.CanonicalizationError) as ctx:
            cc.run(self.out, self.outdir, CONFIG, self.ev)
        self.assertIn("HASH_MISMATCH", str(ctx.exception))

    def test_runtime_manifest_inconsistency_fails_closed(self):
        (self.out / "identity" / "reference_manifest.json").write_text(json.dumps({
            "image_A": "source_A_aka_front.png", "image_A_sha256": "0" * 64}))
        with self.assertRaises(cc.CanonicalizationError) as ctx:
            cc.run(self.out, self.outdir, CONFIG, self.ev)
        self.assertIn("RUNTIME_MANIFEST_INCONSISTENT", str(ctx.exception))

    def test_missing_runtime_manifest_fails_closed(self):
        (self.out / "identity" / "reference_manifest.json").unlink()
        with self.assertRaises(cc.CanonicalizationError) as ctx:
            cc.run(self.out, self.outdir, CONFIG, self.ev)
        self.assertIn("EVIDENCE_MISSING", str(ctx.exception))

    # ------------------------------------------------------------ alias guard
    def test_alias_output_rejected_and_originals_untouched(self):
        src = self.out / "identity" / "source_A_aka_front.png"
        before = sha(src)
        cfg = cc.load_config(CONFIG)
        with self.assertRaises(cc.CanonicalizationError) as ctx:
            cc.canonicalize_file(src, src, cfg)
        self.assertIn("SOURCE_OUTPUT_ALIAS", str(ctx.exception))
        self.assertEqual(sha(src), before)

        link = self.tmp / "alias.png"
        link.symlink_to(src)
        before = sha(src)
        with self.assertRaises(cc.CanonicalizationError) as ctx:
            cc.canonicalize_file(src, link, cfg)
        self.assertIn("SOURCE_OUTPUT_ALIAS", str(ctx.exception))
        self.assertEqual(sha(src), before)
        self.assertFalse(link.exists() and not link.is_symlink())


if __name__ == "__main__":
    unittest.main()
