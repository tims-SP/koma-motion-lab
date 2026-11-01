#!/usr/bin/env python3
"""Audit one pinned Cubism asset without publishing its original binary files."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import struct
import tempfile
import time
import urllib.request

UPSTREAM = "myssal/Reverse-1999-CN-Asset"
COMMIT = "45e75248ba3b25053fd32e63ab13c2f9f54dd9df"
CHARACTER = "302301_shisihangshi"
PREFIX = f"live2d/roles/{CHARACTER}"
ROOT = f"https://raw.githubusercontent.com/{UPSTREAM}/{COMMIT}/{PREFIX}/"
MODEL = f"{CHARACTER}.model3.json"
DISPLAY = f"{CHARACTER}.cdi3.json"
TIMEOUT = 35


def download(relative: str, base: Path) -> dict:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe model relative path: {relative}")
    target = base.joinpath(*path.parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            request = urllib.request.Request(ROOT + str(path), headers={"User-Agent": "KomaMotionLab-SourceAudit/1"})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                if response.status != 200:
                    raise RuntimeError(f"GET {path}: HTTP {response.status}")
                payload = response.read()
            if not payload:
                raise ValueError(f"Empty source file: {path}")
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temp:
                temp.write(payload)
                name = temp.name
            os.replace(name, target)
            entry = {"path": str(path), "sourcePath": f"{PREFIX}/{path}",
                     "sizeBytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                     "downloadVerified": True}
            if path.suffix.lower() == ".png":
                if payload[:8] != b"\x89PNG\r\n\x1a\n":
                    raise ValueError(f"Invalid PNG: {path}")
                entry["imageSize"] = list(struct.unpack(">II", payload[16:24]))
            elif path.suffix.lower() == ".moc3":
                if payload[:4] != b"MOC3":
                    raise ValueError(f"Invalid MOC3 signature: {path}")
                entry["mocSignature"] = "MOC3"
            elif path.suffix.lower() == ".json":
                json.loads(payload)
            return entry
        except Exception:
            if attempt == 3:
                raise
            time.sleep(0.5 * (attempt + 1))
    raise AssertionError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True, help="Private asset cache path")
    parser.add_argument("--report", type=Path, required=True, help="JSON output path")
    args = parser.parse_args()
    base = args.assets.resolve()
    base.mkdir(parents=True, exist_ok=True)
    first = [download(MODEL, base), download(DISPLAY, base)]
    model = json.loads((base / MODEL).read_text(encoding="utf-8"))
    ref = model["FileReferences"]
    paths = [ref["Moc"], *ref["Textures"]]
    for value in ref.get("Motions", {}).values():
        paths.extend(item["File"] for item in value)
    paths.extend(item["File"] for item in ref.get("Expressions", []))
    for key in ["Physics", "Pose", "UserData"]:
        value = ref.get(key)
        if value:
            paths.append(value)
    unique = sorted(set(paths) - {MODEL, DISPLAY})
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        downloaded = list(pool.map(lambda p: download(p, base), unique))
    files = sorted(first + downloaded, key=lambda item: item["path"])
    report = {
        "schema": "R1999-CUBISM-ASSET-AUDIT-V1",
        "status": "PASS",
        "source": {"repo": UPSTREAM, "commit": COMMIT, "prefix": PREFIX},
        "model": MODEL,
        "fileCount": len(files),
        "motionGroups": len(ref.get("Motions", {})),
        "motionFileCount": len(set(item["File"] for group in ref.get("Motions", {}).values() for item in group)),
        "expressionReferences": len(ref.get("Expressions", [])),
        "uniqueExpressions": len(set(item["File"] for item in ref.get("Expressions", []))),
        "textureCount": len(ref["Textures"]),
        "mocFile": ref["Moc"],
        "cubismRuntimeLoad": "NOT_RUN",
        "files": files,
    }
    report_path = args.report.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["status", "fileCount", "motionFileCount", "uniqueExpressions", "textureCount", "cubismRuntimeLoad"]}))


if __name__ == "__main__":
    main()
