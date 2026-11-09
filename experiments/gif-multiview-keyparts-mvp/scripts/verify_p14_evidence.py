#!/usr/bin/env python3
"""Verify source-bound P14 ArtMesh, 37-frame motion, and Chromium review evidence.

Private source images remain under private-assets/. The generated public JSON
contains only portable asset-relative paths, content hashes, and QA findings.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

CHARACTER = "p0_character_001"
ROOT_NAME = "p14-authored-candidates"
ANGLES = (67.5, 72.5)
ROLES = (
    "body.reference", "hair.back", "face.skin", "ear.far",
    "ear.near", "hair.side", "eye.far", "eye.near",
    "nose", "mouth", "hair.front", "hair.ahoge",
    "hair.clip.cross_gold",
)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as reader:
        for data in iter(lambda: reader.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_file(root, entry, sha_key="sha256"):
    path = (root / entry["path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise AssertionError("Referenced private asset missing or outside asset root")
    if digest(path) != entry[sha_key]:
        raise AssertionError("Private source hash mismatch: " + str(path.relative_to(root)))
    return path


def verify(root, output):
    root = Path(root).resolve()
    base = root / ROOT_NAME
    evidence = {
        "paint67": base / "yaw067p5-artmesh/qa.json",
        "paint72": base / "yaw072p5-artmesh/qa.json",
        "motion": base / "p14-vdd-smooth/qa.json",
        "temporal": base / "p14-vdd-smooth/temporal-qa.json",
        "texture": base / "p14-vdd-smooth/texture-qa.json",
        "chromium": base / "p14-browser/browser-qa.json",
        "quality": base / "p14-quality/quality-qa.json",
        "baseline": root / "p8-semantic-occlusion/selective-sequence/qa.json",
    }
    q = {name: read(path) for name, path in evidence.items()}
    if any(v["characterId"] != CHARACTER for v in q.values()):
        raise AssertionError("P0 character identity mismatch")

    quality = q["quality"]
    assert quality["artisticAcceptance"] == "PENDING"
    assert quality["gate"]["adoptedRenderer"] == "P8_SEMANTIC_OCCLUSION_ARTMESH"
    assert quality["gate"]["sourceRgbaPartInvariants"] == "PASS"
    assert quality["gate"]["keyFrameSourceSHA256"] == "PASS"

    layer_summary = {}
    for angle, qa, layer_key in (
        (67.5, q["paint67"], "parts"),
        (72.5, q["paint72"], "semanticLayerRecords"),
    ):
        layers = qa[layer_key]
        assert len(layers) == 13 and {v["semanticId"] for v in layers} == set(ROLES)
        for layer in layers:
            p = verify_file(root, layer)
            with Image.open(p) as img:
                assert img.mode == "RGBA" and img.size == (1024, 1024)
        verify_file(root, qa["composite"])
        layer_summary[str(angle)] = {
            "layerCount": len(layers),
            "compositeSHA256": qa["composite"]["sha256"],
            "qaSHA256": digest(evidence["paint67" if angle == 67.5 else "paint72"]),
        }

    motion = q["motion"]
    assert motion["frameCount"] == 37
    frames = motion["frames"]
    assert len(frames) == 37 and len({f["angle"] for f in frames}) == 37
    for frame in frames:
        path = verify_file(root, frame)
        with Image.open(path) as img:
            assert img.mode == "RGBA" and img.size == (1024, 1024)
    assert q["temporal"]["status"] == "PASS_TEMPORAL_CONTINUITY"
    assert q["texture"]["status"] == "PASS_TEXTURE_EDGE_DIAGNOSTIC"
    assert q["texture"]["failed"] == 0

    browser = q["chromium"]
    assert browser["status"] == "PASS_REAL_P0_PAINTED_KEYVIEW_REVIEW"
    assert browser["screenshotCount"] == 12
    assert len(browser["sourceScreenshots"]) == 6
    assert not browser["javascriptErrors"] and not browser["failedRequests"]
    for record in browser["sourceScreenshots"]:
        assert record["originalSHA256VerifiedImages"] == 5
        for frame in record["screenshots"].values():
            file = Path(frame["path"]).resolve()
            if not file.is_relative_to(root) or digest(file) != frame["sha256"]:
                raise AssertionError("Chromium image provenance mismatch")

    reviews = []
    for item in quality["reviewFrames"]:
        basegap = item["alphaGapPixels"]["P8"]
        candidate = item["alphaGapPixels"]["P14-Painted-Warp"]
        reviews.append({
            "angle": item["angle"],
            "baselineGapPixels": basegap,
            "candidateGapPixels": candidate,
            "candidateMinusBaselinePixels": candidate - basegap,
        })
    compare = verify_file(root, {
        "path": quality["visualComparisonPath"],
        "sha256": quality["visualComparisonSHA256"],
    })
    assert q["baseline"]["frameCount"] == 37
    assert quality["fullRGBAFrames"] == 37
    assert quality["paintedSemanticRolesPerAngle"] == 13

    public = {
        "schema": "KOMA-P0-P14-PAINTED-VIEW-ENGINEERING-QA-V1",
        "characterId": CHARACTER,
        "sourceKeyAngles": [0, 45, 90],
        "generatedCandidateAngles": list(ANGLES),
        "artMesh": {
            "semanticRoleCount": len(ROLES),
            "sourceRgbaCanvas": [1024, 1024],
            "candidateLayersVerified": 26,
            "registeredViewLayers": layer_summary,
            "sourceMethod": "generated multi-view artwork with original-P0 semantic part reprojection",
        },
        "motion": {
            "framesVerified": len(frames),
            "frameFirstSHA256": frames[0]["sha256"],
            "frameLastSHA256": frames[-1]["sha256"],
            "temporalStatus": q["temporal"]["status"],
            "medianAdjacentDelta": quality["temporalMetrics"]["medianDelta"],
            "maximumAdjacentDelta": quality["temporalMetrics"]["maximumDelta"],
            "outliers": quality["temporalMetrics"]["outliers"],
            "textureStatus": q["texture"]["status"],
            "textureHoldoutEdgeDensityRatios": quality["textureRatios"],
        },
        "browser": {
            "engine": "Chromium Playwright",
            "screenshotCount": browser["screenshotCount"],
            "sampleCount": len(browser["sourceScreenshots"]),
            "sourceImagesHashVerifiedPerSample": 5,
            "scriptErrors": len(browser["javascriptErrors"]),
            "failedRequests": len(browser["failedRequests"]),
            "status": browser["status"],
        },
        "visualComparison": {
            "sourcePath": str(compare.relative_to(root)),
            "sha256": quality["visualComparisonSHA256"],
            "alphaGapProxy": reviews,
            "metricRole": "relative structural diagnostic; artistic stroke and identity require visual review",
            "adoptedRenderer": "P8_SEMANTIC_OCCLUSION_ARTMESH",
            "candidateStatus": "ARTISTIC_ACCEPTANCE_PENDING",
            "focusAngles": [65, 67.5, 72.5, 77.5],
            "focusParts": ["face.skin", "eye.near", "ear.near", "hair.front", "hair.back", "hair.ahoge"],
        },
        "evidenceHashes": {name: digest(path) for name, path in evidence.items()},
        "status": "P14_ENGINEERING_EVIDENCE_VERIFIED",
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return public


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Private asset root directory")
    parser.add_argument("--out", required=True, help="Git-tracked public QA JSON")
    args = parser.parse_args()
    result = verify(args.root, args.out)
    print(json.dumps({
        "status": result["status"],
        "semanticLayers": result["artMesh"]["candidateLayersVerified"],
        "frames": result["motion"]["framesVerified"],
        "browserScreenshots": result["browser"]["screenshotCount"],
        "artisticStatus": result["visualComparison"]["candidateStatus"],
    }, ensure_ascii=False))
