#!/usr/bin/env python3
"""Prepare an already-initialized official Cubism 5-r.4 demo for real Three.js parity QA.

Run after prepare-native-sample.py. Assets and Cubism Core remain in the
private sample cache and are not copied into this source repository.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil


def replace_exact(path: Path, old: str, new: str) -> None:
    data = path.read_text(encoding="utf-8")
    if data.count(old) != 1:
        raise RuntimeError(f"Expected one match in {path}: {old!r}; found {data.count(old)}")
    path.write_text(data.replace(old, new), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=Path, required=True,
                    help="Private checkout of official CubismWebSamples 5-r.4, prepared with native sample script")
    ap.add_argument("--adapter", type=Path, required=True,
                    help="Path to cubism-three-adapter.ts in koma-motion-lab")
    args = ap.parse_args()
    samples, adapter = args.samples.resolve(), args.adapter.resolve()
    if not adapter.is_file():
        raise FileNotFoundError(adapter)
    demo = samples / "Samples/TypeScript/Demo"
    if not (demo / "src/lappmodel.ts").exists():
        raise RuntimeError("Missing prepared official Cubism TypeScript demo")

    define = demo / "src/lappdefine.ts"
    source = define.read_text(encoding="utf-8")
    source, n = re.subn(
        r"export const CanvasSize: \{ width: number; height: number \} \| 'auto' = 'auto';",
        "export const CanvasSize: { width: number; height: number } | 'auto' = {width:640,height:640};",
        source,
    )
    if n != 1:
        raise RuntimeError("Unexpected CanvasSize declaration; require CubismWebSamples 5-r.4")
    define.write_text(source, encoding="utf-8")

    sub = demo / "src/lappsubdelegate.ts"
    replace_exact(sub, "gl.clearColor(0.0, 0.0, 0.0, 1.0);",
                  "gl.clearColor(0.0, 0.0, 0.0, 0.0);")

    view = demo / "src/lappview.ts"
    replace_exact(view, "this._back.render(this._programId);",
                  "// Background suppressed for transparent same-frame model comparison.")
    replace_exact(view, "this._gear.render(this._programId);",
                  "// UI sprite suppressed for model-only comparison.")

    target = demo / "src/r1999-three-adapter.ts"
    shutil.copy2(adapter, target)
    index = demo / "index.html"
    replace_exact(index, "<!-- Build script -->",
                  '<script src="./src/r1999-three-adapter.ts" type="module"></script>\n  <!-- Build script -->')
    print("C03_SAMPLE_PREPARED", {
        "sampleRoot": str(samples),
        "adapter": str(adapter),
        "newModule": str(target),
        "resolution": [640, 640],
        "threeVersion": "0.181.0",
    })


if __name__ == "__main__":
    main()
