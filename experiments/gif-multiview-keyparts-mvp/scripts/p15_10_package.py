#!/usr/bin/env python3
"""Create and verify a source-hashed offline P15-10 semantic ArtMesh review."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from p15_09_anchor_pose import ASSETS, BASE
from p15_10_semantic_arc import OUT, STEPS, QA65
from p15_10_semantic_key55 import CHECK, OUTPUT
from p8_semantic_occlusion import output_frame_id

DEST = ASSETS / "exports/p15-10-artmesh-correspondence-review.zip"
PUBLIC = BASE / "evidence/p15-10-delivery.json"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    key = json.loads(CHECK.read_text())
    arc = json.loads((BASE / "evidence/p15-10-semantic-arc-qa.json").read_text())
    browser = json.loads((ASSETS / "p15-10-semantic-pose/browser/qa.json").read_text())
    source65 = json.loads(QA65.read_text())
    if not (key["pixelExactComposite"] and browser["status"] == "INTERACTIVE_ARTMESH_HTML_VERIFIED"):
        raise ValueError("Source ownership and real browser QA must pass")
    required = {
        "review/p15-10-semantic.html",
        "review/p15-10-semantic.js",
        "evidence/p15-10-semantic-source-qa.json",
        "evidence/p15-10-semantic-arc-qa.json",
        "private-assets/p15-10-semantic-pose/browser/qa.json",
        "private-assets/p15-10-semantic-pose/arc/p15-10-semantic-arc-contact.jpg",
        "private-assets/p15-09-anchor-pose/yaw055-p5-anchor-reference.png",
        "private-assets/p2-views/whole/yaw045.png",
        "private-assets/p15-independent-candidates/yaw065-source-rgba.png",
    }
    for part in key["semanticLayers"]:
        required.add("private-assets/" + part["outputPath"])
    for part in source65["semanticLayers"]:
        required.add("private-assets/" + part["path"])
    for angle in STEPS:
        name = output_frame_id(angle)
        for folder in ("p15-07-wholekey-preview", "p15-09-midarc",
                       "p15-10-semantic-pose/arc"):
            required.add("private-assets/" + folder + "/" + name)
        partdir = OUT / name.replace(".png", "") / "parts"
        for role in arc["roles"]:
            required.add("private-assets/" + str((partdir / (role + ".png")).relative_to(ASSETS)))
    for shot in browser["screenshots"]:
        required.add(shot["path"])
    files = []
    for rel in sorted(required):
        f = BASE / rel
        if not f.is_file():
            raise FileNotFoundError(f)
        content = f.read_bytes()
        files.append((rel, content))
    manifest = {
        "schema": "KOMA-P15-10-OFFLINE-ARTMESH-REVIEW-V1",
        "characterId": "p0_character_001",
        "html": "review/p15-10-semantic.html",
        "angles": STEPS,
        "semanticRoles": arc["roles"],
        "source55": key["P5Pose55SHA256"],
        "source65": arc["source65SHA256"],
        "artSourceStatus": arc["artisticStatus"],
        "files": [{"path": rel, "size": len(data), "sha256": hash_bytes(data)}
                  for rel, data in files]
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DEST, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=4) as z:
        for rel, data in files + [("manifest.json",
            (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode())]:
            entry = zipfile.ZipInfo(rel, (2026, 11, 10, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            z.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=4)
    with zipfile.ZipFile(DEST) as z:
        if z.testzip() is not None:
            raise AssertionError("Archive ZIP CRC mismatch")
        for f in manifest["files"]:
            if hash_bytes(z.read(f["path"])) != f["sha256"]:
                raise AssertionError("Archive content differs: " + f["path"])
    result = {
        "schema": "KOMA-P15-10-DELIVERY-V1",
        "characterId": "p0_character_001",
        "archivePath": str(DEST.relative_to(BASE)),
        "sha256": hash_bytes(DEST.read_bytes()),
        "sizeBytes": DEST.stat().st_size,
        "entriesVerified": len(files) + 1,
        "html": manifest["html"],
        "semanticRoles": 13,
        "capturedScreenshots": browser["screenshotCount"],
        "artisticStatus": manifest["artSourceStatus"]
    }
    PUBLIC.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
