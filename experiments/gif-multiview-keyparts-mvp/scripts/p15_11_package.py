#!/usr/bin/env python3
"""Package source-hashed P15-11 artwork candidate comparison for offline review."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "private-assets"
GENERATED = ASSETS / "p15-11-generation"
ARCHIVE = ASSETS / "exports/p15-11-source-keyview-review.zip"
DELIVERY = ROOT / "evidence/p15-11-delivery.json"
TIMESTAMP = (2026, 11, 10, 0, 0, 0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run():
    registry = json.loads((ROOT/"metadata/p15-11-source-candidates.json").read_text())
    quality = json.loads((ROOT/"evidence/p15-11-source-candidate-qa.json").read_text())
    browser = json.loads((GENERATED/"browser/qa.json").read_text())
    if not (registry["characterId"] == quality["characterId"] == browser["characterId"] == "p0_character_001"):
        raise AssertionError("Identity source registry mismatch")
    if quality["generatedCandidateCount"] != 4 or quality["independentPaintingAccepted"] != 0:
        raise AssertionError("Candidate review state differs")
    if browser["status"] != "SOURCE_PREVIEW_AND_BROWSER_VERIFIED":
        raise AssertionError("Chromium proof missing")
    paths = {
        "review/p15-11-keyview-art.html",
        "metadata/p15-11-source-candidates.json",
        "evidence/p15-11-source-candidate-qa.json",
        "private-assets/p15-11-generation/browser/qa.json",
        "private-assets/" + quality["candidateContactPath"],
    }
    for item in registry["referenceImages"]:
        paths.add("private-assets/" + item["path"])
    matte_rows = []
    for item in registry["candidates"]:
        file = "private-assets/p15-11-generation/" + item["file"]
        rgba = "private-assets/p15-11-generation/rgba/" + item["file"]
        matte = ROOT / rgba
        if not matte.is_file():
            raise FileNotFoundError(matte)
        qa_path = matte.with_suffix(".qa.json")
        matte_qa = json.loads(qa_path.read_text())
        if matte_qa["sourceArtworkSHA256"] != item["sha256"]:
            raise AssertionError("Matte source hash mismatch: "+item["file"])
        if sha(matte.read_bytes()) != matte_qa["outputPNG_SHA256"]:
            raise AssertionError("RGBA SHA mismatch: "+item["file"])
        matte_rows.append({
            "image": rgba,
            "sourceSHA256": item["sha256"],
            "matteSHA256": matte_qa["outputPNG_SHA256"],
            "foregroundPixels": matte_qa["alphaForegroundPixelsGt16"]
        })
        paths.update({file, rgba, str(qa_path.relative_to(ROOT))})
    for item in browser["screenshots"]:
        paths.add(item["path"])
    checked = []
    for path in sorted(paths):
        f = ROOT / path
        if not f.is_file():
            raise FileNotFoundError(f)
        raw = f.read_bytes()
        checked.append((path, raw))
    manifest = {
        "schema": "KOMA-P15-11-PRIVATE-ARTWORK-REVIEW-V1",
        "characterId": "p0_character_001",
        "html": "review/p15-11-keyview-art.html",
        "sourceAngles": [45, 65],
        "candidateAngles": [57.5, 60],
        "candidateImageCount": 4,
        "transparentCandidateCount": len(matte_rows),
        "matteSources": matte_rows,
        "artisticStatus": quality["formalArtGate"],
        "acceptedIndependentPaintings": 0,
        "files": [{"path": path, "bytes": len(raw), "sha256": sha(raw)} for path, raw in checked]
    }
    checked.append(("manifest.json", (json.dumps(manifest, ensure_ascii=False,
                         sort_keys=True, indent=2)+"\n").encode("utf-8")))
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(ARCHIVE, "w", compression=ZIP_DEFLATED, compresslevel=4) as archive:
        for path, raw in checked:
            info = ZipInfo(path, TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compress_type=ZIP_DEFLATED, compresslevel=4)
    with ZipFile(ARCHIVE, "r") as archive:
        if archive.testzip() is not None:
            raise AssertionError("Archive CRC mismatched")
        for f in manifest["files"]:
            if sha(archive.read(f["path"])) != f["sha256"]:
                raise AssertionError("Archive member changed: "+f["path"])
    data = {
        "schema": "KOMA-P15-11-SOURCE-DELIVERY-V1",
        "characterId": "p0_character_001",
        "archivePath": str(ARCHIVE.relative_to(ROOT)),
        "sha256": sha(ARCHIVE.read_bytes()),
        "bytes": ARCHIVE.stat().st_size,
        "entries": len(checked),
        "inputCandidateCount": len(registry["candidates"]),
        "transparentCandidateCount": len(matte_rows),
        "browserCaptures": browser["captureCount"],
        "artisticStatus": quality["formalArtGate"],
        "htmlEntry": "review/p15-11-keyview-art.html"
    }
    DELIVERY.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    run()
