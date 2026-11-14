#!/usr/bin/env python3
"""Multi-key artwork geometry bridge with independent held-out view QA.

The original P0 views and P14 painted 67.5/72.5-degree sources drive rendering.
P15 independent 65/77.5-degree art is read only by the QA comparator, never
by the renderer. Pixel masks are interpolated as signed-distance fields;
colour follows a single warped keyview to preserve anime ink strokes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from flow_render import get_flow
from p8_semantic_occlusion import output_frame_id

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "private-assets"
N = 1024
FLOW = 443
STOPS = (45.0, 67.5, 72.5, 90.0)
ART = {
    45.0: "p2-views/whole/yaw045.png",
    67.5: "p14-authored-candidates/yaw067p5-artmesh/yaw067p5-painted-semantic-composite.png",
    72.5: "p14-authored-candidates/yaw072p5-artmesh/yaw072p5-p0-source-mapped-artmesh.png",
    90.0: "p2-views/whole/yaw090.png",
}
HOLDOUT = {
    65.0: "p15-independent-candidates/yaw065-source-rgba.png",
    77.5: "p15-independent-candidates/yaw077p5-source-rgba.png",
}
METHODS = ("source-owner", "source-mix", "semantic-sdf", "semantic-flow")
MODES = ("benchmark", "render")


def sha(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(part)
    return hasher.hexdigest()


def read_json(rel: str) -> dict:
    return json.loads((P / rel).read_text())


def get_art() -> tuple[dict, dict]:
    manifest = read_json("p5-see-through/mv-candidate/parts.json")
    qa67 = read_json("p14-authored-candidates/yaw067p5-artmesh/qa.json")
    qa72 = read_json("p14-authored-candidates/yaw072p5-artmesh/qa.json")
    if not all(q["characterId"] == "p0_character_001" for q in (manifest, qa67, qa72)):
        raise ValueError("P0 original character lineage mismatch")
    originals = {float(q["yawDeg"]): q for q in manifest["wholeViews"]}
    expected = {
        45.0: originals[45.0]["sha256"],
        90.0: originals[90.0]["sha256"],
        67.5: qa67["composite"]["sha256"],
        72.5: qa72["composite"]["sha256"],
    }
    expected_paths = {
        45.0: originals[45.0]["path"],
        90.0: originals[90.0]["path"],
        67.5: qa67["composite"]["path"],
        72.5: qa72["composite"]["path"],
    }
    pictures = {}
    trace = {}
    for angle, rel in ART.items():
        if rel != expected_paths[angle]:
            raise ValueError(f"Registered source path mismatch {angle}")
        path = P / rel
        if sha(path) != expected[angle]:
            raise ValueError(f"Registered source SHA mismatch {angle}")
        with Image.open(path) as im:
            if im.size != (N, N) or im.mode != "RGBA":
                raise ValueError(f"Key artwork must be 1024 RGBA: {rel}")
            pictures[angle] = np.asarray(im).copy()
        trace[str(angle)] = {"path": rel, "sha256": expected[angle]}
    return pictures, trace


def field(source: np.ndarray, target: np.ndarray):
    a = cv2.resize(source, (FLOW, FLOW), interpolation=cv2.INTER_AREA)
    b = cv2.resize(target, (FLOW, FLOW), interpolation=cv2.INTER_AREA)
    return get_flow(a, b, mode="dis")


def warp(picture: np.ndarray, displacement: np.ndarray, factor: float, coords):
    arr = picture.astype(np.float32) / 255.
    arr[:, :, :3] *= arr[:, :, 3:]
    xx, yy = coords
    dx = cv2.resize(displacement[:, :, 0], (N, N)) * (N / FLOW)
    dy = cv2.resize(displacement[:, :, 1], (N, N)) * (N / FLOW)
    return cv2.remap(arr, xx - dx * factor, yy - dy * factor,
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def sdf(alpha: np.ndarray):
    fg = np.uint8(alpha >= .5)
    inside = cv2.distanceTransform(fg, cv2.DIST_L2, 3)
    outside = cv2.distanceTransform(1-fg, cv2.DIST_L2, 3)
    return inside - outside


def compose(a: np.ndarray, b: np.ndarray, t: float, method: str,
            semantic: np.ndarray | None):
    am = a[:, :, 3]
    bm = b[:, :, 3]
    if method == "semantic-flow":
        assert semantic is not None
        return semantic
    if method == "source-mix":
        mix = (1-t)*a+t*b
        return unpremul(mix)
    mask = np.clip((1-t)*sdf(am) + t*sdf(bm) + .5, 0, 1)
    if method == "source-owner":
        preferred, fallback = (a, b) if t < .5 else (b, a)
        owner_rgb = np.where(preferred[:, :, 3:] > .03, preferred[:, :, :3],
                             fallback[:, :, :3])
        owner_a = np.where(preferred[:, :, 3:] > .03, preferred[:, :, 3:],
                           fallback[:, :, 3:])
        rgba = np.concatenate([owner_rgb, owner_a], axis=2)
        rgba[:, :, :3] *= mask[:, :, None] / np.maximum(rgba[:, :, 3:], 1e-6)
        rgba[:, :, 3] = mask
        return unpremul(rgba)
    if method == "semantic-sdf":
        assert semantic is not None
        raw = semantic.astype(np.float32) / 255.
        raw[:, :, :3] *= raw[:, :, 3:]
        preferred, fallback = (a, b) if t < .5 else (b, a)
        missing = raw[:, :, 3:] <= .02
        preferred_rgb = np.where(preferred[:, :, 3:] > .02, preferred[:, :, :3],
                                 fallback[:, :, :3])
        preferred_a = np.maximum(preferred[:, :, 3:], fallback[:, :, 3:])
        raw[:, :, :3] = np.where(missing, preferred_rgb, raw[:, :, :3])
        raw[:, :, 3:] = np.where(missing, preferred_a, raw[:, :, 3:])
        raw[:, :, :3] *= mask[:, :, None] / np.maximum(raw[:, :, 3:], 1e-6)
        raw[:, :, 3] = mask
        return unpremul(raw)
    raise ValueError(method)


def unpremul(f):
    a = np.clip(f[:, :, 3:], 0, 1)
    rgb = np.clip(f[:, :, :3] / np.maximum(a, 1e-6), 0, 1)
    return np.uint8(np.rint(np.concatenate([rgb, a], axis=2) * 255))


def mask_score(actual: np.ndarray, independent: np.ndarray) -> dict:
    x = actual[:, :, 3] >= 128
    y = independent[:, :, 3] >= 128
    both = np.logical_and(x, y).sum()
    either = np.logical_or(x, y).sum()
    area = abs(int(x.sum()) - int(y.sum())) / max(int(y.sum()), 1)
    head = np.logical_and(x[:710], y[:710]).sum()/max(1,np.logical_or(x[:710],y[:710]).sum())
    return {"silhouetteIoU": round(float(both / max(either,1)), 6),
            "relativeAreaError": round(float(area), 6),
            "headSilhouetteIoU": round(float(head), 6)}


def run(angles, out: Path, mode: str):
    art, trace = get_art()
    coords = np.meshgrid(np.arange(N, dtype=np.float32),
                         np.arange(N, dtype=np.float32))
    flows = {}
    for a,b in zip(STOPS[:-1], STOPS[1:]):
        if any(a < deg < b for deg in angles):
            flows[a,b] = field(art[a], art[b])
    out.mkdir(parents=True, exist_ok=True)
    all_results = {}
    records = []
    for angle in angles:
        if angle in art:
            methods = {m: art[angle] for m in METHODS}
        else:
            a,b = next(((x,y) for x,y in zip(STOPS[:-1], STOPS[1:]) if x<angle<y), (None,None))
            if a is None: raise ValueError(f"No geometry source interval for angle {angle}")
            t = (angle-a)/(b-a)
            fa,fb = flows[a,b]
            wa = warp(art[a],fa,t,coords)
            wb = warp(art[b],fb,1-t,coords)
            semantic_file = P / "p14-authored-candidates/p14-vdd-smooth" / output_frame_id(angle)
            if not semantic_file.is_file():
                raise FileNotFoundError(f"Full-resolution semantic baseline absent: {semantic_file}")
            with Image.open(semantic_file) as im:
                semantic = np.asarray(im.convert("RGBA")).copy()
            methods = {m: compose(wa.copy(),wb.copy(),t,m,semantic) for m in METHODS}
        if mode == "benchmark":
            all_results[angle] = methods
            for method, result in methods.items():
                Image.fromarray(result,"RGBA").save(out / f"yaw{str(angle).replace('.','p')}-{method}.png")
        else:
            result = methods["source-owner"]
            file = out / output_frame_id(angle)
            Image.fromarray(result,"RGBA").save(file)
            records.append({"angle":angle,"path":str(file.relative_to(P)),
                            "sha256":sha(file)})
    baseline = {}
    checks = {}
    if mode == "benchmark":
        for angle, rel in HOLDOUT.items():
            if angle not in all_results: continue
            with Image.open(P / rel) as im:
                independent = np.asarray(im.convert("RGBA")).copy()
            checks[str(angle)] = {
                "reference":{"path":rel,"sha256":sha(P/rel)},
                "methods":{k:mask_score(v,independent) for k,v in all_results[angle].items()}
            }
            for candidate, dr in [("P8","p8-semantic-occlusion/selective-sequence"),
                                  ("P14_semantic","p14-authored-candidates/p14-vdd-smooth"),
                                  ("P14_whole","p14-authored-candidates/p14-whole-holdout")]:
                path=P/dr/output_frame_id(angle)
                if path.is_file():
                    with Image.open(path) as img:
                        baseline[candidate]=mask_score(np.asarray(img.convert("RGBA")),independent)
            checks[str(angle)]["baselines"]=baseline.copy()
            baseline.clear()
    qa={"schema":"KOMA-P15-07-SOURCE-ONLY-GEOMETRY-BRIDGE-V1",
        "characterId":"p0_character_001",
        "renderSourceAngles":list(STOPS),
        "sourceManifests":trace,
        "holdoutRole":"strictly-evaluation-only",
        "methods":list(METHODS),
        "tests":checks,
        "frames":records,
        "status":"RENDERING_VALIDATION_CANDIDATE",
        "artisticAcceptance":"PENDING"}
    (out/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":qa["status"],"checks":checks},ensure_ascii=False))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--angles",default="65,77.5")
    parser.add_argument("--out",default="private-assets/p15-07-geometry-benchmark")
    parser.add_argument("--mode",choices=MODES,default="benchmark")
    args=parser.parse_args()
    destination=Path(args.out)
    if not destination.is_absolute():destination=(ROOT/destination)
    run([float(a) for a in args.angles.split(",")],destination,args.mode)
