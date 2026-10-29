#!/usr/bin/env python3
"""Stage a minimal real upstream MOC3 bundle in ephemeral workspace, never in Git."""
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.request import urlopen

work = Path(os.environ["GODOT002_PROJECT"])
dest = work / "assets" / "301003_x"
report = Path(os.environ["GODOT002_OUT"])
report.mkdir(parents=True, exist_ok=True)
base = "https://raw.githubusercontent.com/myssal/Reverse-1999-CN-Asset/master/live2d/roles/301003_x/"

def download(path):
    if path.startswith("/") or ".." in Path(path).parts:
        raise ValueError("unsafe path: " + path)
    for attempt in range(4):
        try:
            with urlopen(base + path, timeout=60) as response:
                binary = response.read()
            if not binary:
                raise ValueError("empty upstream file: " + path)
            target = dest / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(binary)
            return binary
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt + 1)

manifest = json.loads(download("301003_x.model3.json"))
refs = manifest["FileReferences"]
files = [refs["Moc"]] + list(refs["Textures"])
source_motions = [entry["File"] for group in refs.get("Motions", {}).values() for entry in group]
nod = "motions/b_diantou.motion3.json"
idle = "motions/t_idle.motion3.json"
if nod not in source_motions or idle not in source_motions:
    raise RuntimeError("original model lacks chosen nod or idle motion")
files += [nod, idle]
for f in files:
    download(f)
# Original motion3 Meta point counters underreport real curve point counts.
# Normalize transient copies only; original curve data, times, Beziers untouched.
from godot_002_normalize_motion import repair
motion_repairs = [repair(dest / f) for f in (nod, idle)]
for entry in motion_repairs:
    print("GODOT002_MOTION_META_REPAIRED", json.dumps({
        "path": entry["path"], "original": entry["original_meta"],
        "corrected": entry["verified_meta"]}))
refs["Motions"] = {"nod": [{"File": nod}], "idle": [{"File": idle}]}
(dest / "301003_x.model3.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
moc = (dest / refs["Moc"]).read_bytes()
if moc[:4] != b"MOC3":
    raise RuntimeError("expected real MOC3 header")
integrity = {"model": "301003_x", "origin": "myssal/Reverse-1999-CN-Asset",
             "moc_magic": "MOC3", "status": "STAGED_NOT_RENDERED",
             "files": [{"name": p, "bytes": (dest/p).stat().st_size,
                        "sha256": hashlib.sha256((dest/p).read_bytes()).hexdigest()}
                       for p in sorted(set(files))],
             "preview_policy": "No third-party artwork in git or public release",
             "motion_metadata_repairs": motion_repairs}
(report / "asset-integrity.json").write_text(json.dumps(integrity, indent=2) + "\n")
print("GODOT002_STAGED_REAL_MODEL", len(integrity["files"]), "files")
