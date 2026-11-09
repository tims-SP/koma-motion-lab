#!/usr/bin/env python3
"""P15-04 source and Chromium evidence acceptance for reproducible HTML review."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
PRIVATE = (HERE / "private-assets").resolve()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify():
    q = read(HERE / "evidence/p15-facial-correspondence-qa.json")
    browser_file = PRIVATE / "p15-facial-strokes/browser/qa.json"
    browser = read(browser_file)
    if any(item["characterId"] != "p0_character_001" for item in (q, browser)):
        raise AssertionError("P0 source identity mismatch")
    if q["pairCount"] != 12 or len(q["pairs"]) != 12:
        raise AssertionError("semantic stroke pairs incomplete")
    if browser["status"] != "PASS_SOURCE_HASH_CHROMIUM" or browser["screenshotCount"] != 4:
        raise AssertionError("browser acceptance incomplete")
    if browser["javascriptErrors"] or browser["failedRequests"]:
        raise AssertionError("browser errors present")
    source_matches = sum(len(row["accepted"]) for row in q["pairs"].values())
    if source_matches != q["matchedStrokeCandidateCount"] or source_matches != browser["acceptedStrokeMatches"]:
        raise AssertionError("matched strokes mismatch between source and browser")
    referenced = set()
    for pair in q["pairs"].values():
        for entry in pair["source"].values():
            file = (PRIVATE / entry["path"]).resolve()
            if not file.is_relative_to(PRIVATE) or not file.exists() or sha(file) != entry["sha256"]:
                raise AssertionError("semantic original source SHA mismatch")
            referenced.add(entry["sha256"])
    checks = {}
    for path, expected in q["sourceMetadataSHA256"].items():
        known = {
            "P5ArtMesh": "p5-see-through/mv-candidate/parts.json",
            "P5Landmarks": "p5-see-through/mv-candidate/landmark-qa.json",
            "P9Palette": "p9-region-correspondence/qa.json",
            "P10StrokeBaseline": "p10-stroke-identity/qa.json",
        }[path]
        value = sha(PRIVATE / known)
        if value != expected:
            raise AssertionError("P0 metadata SHA changed: " + path)
        checks[path] = value
    for frame in browser["reviews"]:
        image = (HERE / frame["path"]).resolve()
        if not image.is_relative_to(PRIVATE) or sha(image) != frame["sha256"]:
            raise AssertionError("browser pixel capture SHA changed")
        if frame["sourceImagesHashVerified"] != 4:
            raise AssertionError("browser source image provenance incomplete")
    public = {
        "schema": "KOMA-P0-P15-04-FACIAL-CORRESPONDENCE-ACCEPTANCE-V1",
        "characterId": "p0_character_001",
        "engineeringStatus": "PASS_SOURCE_STROKE_AND_CHROMIUM_REVIEW",
        "semanticRoles": q["semanticRoles"],
        "sourceOriginalAngles": q["originalKeyAngles"],
        "generatedIntermediateAngles": q["intermediateCandidateAngles"],
        "semanticViewPairsVerified": q["pairCount"],
        "sourceRGBAHashesVerified": len(referenced),
        "highConfidenceStrokeCandidates": source_matches,
        "physicalReferenceType": "P5_APPROVED_KEYVIEW_LINEAR_PROJECTION",
        "landmarkImageOverlapType": "CANDIDATE_RGBA_ALPHA_SUPPORT",
        "sourceMetadataSHA256": checks,
        "chromiumCanvasScreenshots": browser["screenshotCount"],
        "chromiumSourceImagesHashVerified": browser["verifiedSourceImages"],
        "chromiumSummarySHA256": sha(browser_file),
        "sourceCorrespondenceSHA256": sha(HERE / "evidence/p15-facial-correspondence-qa.json"),
        "manualReviewPriority": ["eye.near", "nose", "mouth", "face.skin"],
        "manualReviewFinding": "MID_VIEW_PART_PAINTING_REQUIRES_FEATURE_STROKE_AND_LAYER_EDGE_REFINEMENT",
        "adoptedRenderBaseline": "P8_SEMANTIC_OCCLUSION_ARTMESH",
        "artisticAcceptance": "PENDING_INDEPENDENT_ARTISTIC_REVIEW",
    }
    path = HERE / "evidence/p15-04-acceptance.json"
    path.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": public["engineeringStatus"],
        "registeredPairs": public["semanticViewPairsVerified"],
        "strokeCandidates": source_matches,
        "captures": public["chromiumCanvasScreenshots"],
        "sourceHashesVerified": public["sourceRGBAHashesVerified"],
    }, ensure_ascii=False))
    return public


if __name__ == "__main__":
    verify()
