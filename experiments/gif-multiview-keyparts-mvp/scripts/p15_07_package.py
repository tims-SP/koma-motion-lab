#!/usr/bin/env python3
"""Package the locally reproducible P15-07 HTML and full source-backed images."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/"private-assets"
TARGET=PRIVATE/"exports/p15-07-view-correspondence-review.zip"
REPORT=ROOT/"evidence/p15-07-delivery.json"
LOCKED_DATE=(2026,11,10,0,0,0)


def sha(file):
    h=hashlib.sha256()
    with Path(file).open("rb") as fp:
        for chunk in iter(lambda:fp.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    qa=json.loads((ROOT/"evidence/p15-07-renderer-qa.json").read_text())
    if qa["technicalGate"]!="SOURCE_INTEGRITY_AND_BROWSER_PASS":
        raise AssertionError("P15-07 source/browser engineering gate required")
    files={
        "review/p15-07-view.html",
        "review/p15-07-view.js",
        "evidence/p15-07-renderer-qa.json",
        "private-assets/p15-07-browser/qa.json",
    }
    for subdir in ("p15-07-semantic-preview","p15-07-wholekey-preview",
                   "p8-semantic-occlusion/selective-sequence"):
        for step in range(37):
            yaw=2.5*step
            k=str(int(yaw)) if float(yaw).is_integer() else str(yaw).replace(".","p")
            files.add(f"private-assets/{subdir}/yaw{k}.png")
    for x in qa["browser"]["qaPath"],:
        files.add(x)
    browser=json.loads((PRIVATE/"p15-07-browser/qa.json").read_text())
    for entry in browser["screenshots"]:
        files.add(entry["screenPath"])
    files.update((
        "private-assets/p15-independent-candidates/yaw065-source-rgba.png",
        "private-assets/p15-independent-candidates/yaw077p5-source-rgba.png",
        "private-assets/p14-authored-candidates/yaw067p5-artmesh/yaw067p5-painted-semantic-composite.png",
        "private-assets/p14-authored-candidates/yaw072p5-artmesh/yaw072p5-p0-source-mapped-artmesh.png",
    ))
    paths=[]
    for rel in sorted(files):
        file=ROOT/rel
        if not file.is_file():
            raise FileNotFoundError(file)
        paths.append((rel,file))
    checks=[{"path":p,"bytes":f.stat().st_size,"sha256":sha(f)} for p,f in paths]
    manifest={
      "schema":"KOMA-P15-07-OFFLINE-REVIEW-PACKAGE-V1",
      "characterId":"p0_character_001",
      "entryHtml":"review/p15-07-view.html",
      "registeredFiles":checks,
      "sourceQA":"evidence/p15-07-renderer-qa.json",
      "fullTurnFramesPerRenderer":37,
      "visualGate":"REVIEW_REQUIRED",
    }
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(TARGET,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
        for rel,file in paths:
            info=zipfile.ZipInfo(rel,LOCKED_DATE)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            archive.writestr(info,file.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=3)
        info=zipfile.ZipInfo("manifest.json",LOCKED_DATE)
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        archive.writestr(info,json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    with zipfile.ZipFile(TARGET) as archive:
        if archive.testzip() is not None:
            raise AssertionError("Archive CRC test failed")
        for x in checks:
            if hashlib.sha256(archive.read(x["path"])).hexdigest()!=x["sha256"]:
                raise AssertionError("Archive content hash differs: "+x["path"])
        count=len(archive.namelist())
    result={
      "schema":"KOMA-P15-07-LOCAL-HTML-ARTIFACT-V1",
      "characterId":"p0_character_001",
      "relativeArchivePath":str(TARGET.relative_to(ROOT)),
      "size":TARGET.stat().st_size,
      "sha256":sha(TARGET),
      "verifiedEntries":count,
      "includedImageFrames":111,
      "htmlEntry":"review/p15-07-view.html",
      "deliveryRole":"private source-linked engineering and artistic review",
      "artisticAcceptance":"PENDING_VISUAL_REVIEW",
    }
    REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"archive":result["relativeArchivePath"],"size":result["size"],
                      "sha256":result["sha256"],"entries":count}))


if __name__=="__main__":
    main()
