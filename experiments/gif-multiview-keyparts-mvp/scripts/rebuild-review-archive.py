#!/usr/bin/env python3
"""Reconstruct and verify the P0 multi-view GIF review archive from PR assets."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

PACKAGE = "gif_multiview_asset_review_2026-11-05.zip"
SHA256 = "8ce3596f60a01b82df49926304c47041d8a8734689ae2a3126acada583666547"
BYTES = 5129540
PARTS = 12
EXPECTED_ENTRIES = 53

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", type=Path, default=Path(__file__).resolve().parents[1] / "private-assets" / "transport")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.transport.resolve()
    manifest = json.loads((root / "asset-transport-manifest.json").read_text())
    assert manifest["archive"]["sha256"] == SHA256
    assert len(manifest["parts"]) == PARTS
    args.output.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    with args.output.open("wb") as dest:
        for part in manifest["parts"]:
            path = root / part["filename"]
            if path.parent != root or not path.is_file():
                raise ValueError("Missing or invalid part path: " + str(path))
            payload = path.read_bytes()
            if len(payload) != part["bytes"]:
                raise ValueError("Part length mismatch: " + path.name)
            dest.write(payload)
            digest.update(payload)
            total += len(payload)
    if total != BYTES or digest.hexdigest() != SHA256:
        args.output.unlink(missing_ok=True)
        raise ValueError("Reconstructed ZIP SHA-256 or size mismatch")
    with zipfile.ZipFile(args.output) as archive:
        bad = archive.testzip()
        if bad is not None or len(archive.infolist()) != EXPECTED_ENTRIES:
            raise ValueError(f"ZIP integrity error: {bad}")
        names = set(archive.namelist())
        assert all(f"sources/{p}" in names for p in (
            "head-turn-8view.gif",
            "face-semantic-0-45-90.gif",
            "hair-semantic-0-45-90.gif",
            "identity-semantic-0-45-90.gif",
            "generated-master.png",
        ))
        frames = [p for p in names if p.startswith("frames/") and p.endswith(".png")]
        if len(frames) != 38:
            raise ValueError(f"Expected 38 frame images; found {len(frames)}")
    print(json.dumps({"status":"PASS", "file":str(args.output),
        "bytes":total, "sha256":digest.hexdigest(),
        "gifCount":4, "pngFrames":38, "zipEntries":EXPECTED_ENTRIES}))

if __name__ == "__main__":
    main()
