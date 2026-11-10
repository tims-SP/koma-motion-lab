#!/usr/bin/env python3
"""Reproducible private P0 55-degree art calibration review package."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/"private-assets"
ARCHIVE=PRIVATE/"exports/p15-08-pose-source-review.zip"
REC=ROOT/"evidence/p15-08-delivery.json"
FIXED=(2026,11,10,0,0,0)


def sha(f):
    h=hashlib.sha256()
    with Path(f).open("rb") as file:
        for block in iter(lambda:file.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def run():
    qa=json.loads((ROOT/"evidence/p15-08-source-candidate-qa.json").read_text())
    if qa["characterId"]!="p0_character_001" or len(qa["candidateRecords"])!=2:
        raise AssertionError("P0 source candidate registry required")
    browser=PRIVATE/"p15-08-yaw055/browser/qa.json"
    report=json.loads(browser.read_text())
    if report["status"]!="SOURCE_IMAGES_AND_ALPHA_GALLERY_PASS":
        raise AssertionError("P0 original preview browser QA required")
    paths={
        "review/p15-08-mid-angle.html",
        "review/p15-08-mid-angle.js",
        "evidence/p15-08-source-candidate-qa.json",
        "private-assets/p15-08-yaw055/browser/qa.json",
        "private-assets/p2-views/whole/yaw045.png",
        "private-assets/p2-views/whole/yaw090.png",
        "private-assets/p15-independent-candidates/yaw065-source-rgba.png",
    }
    for k in ("v1","v2"):
        paths.add(f"private-assets/p15-08-yaw055/yaw055-qwen2511-{k}.png")
        paths.add(f"private-assets/p15-08-yaw055/yaw055-rgba-{k}.png")
        paths.add(f"private-assets/p15-08-yaw055/yaw055-rgba-{k}.qa.json")
    for capture in report["captures"]:
        paths.add(capture["capturedPath"])
    checked=[]
    for rel in sorted(paths):
        source=ROOT/rel
        if not source.is_file():raise FileNotFoundError(source)
        checked.append({"path":rel,"bytes":source.stat().st_size,"sha256":sha(source)})
    manifest={"schema":"KOMA-P15-08-55DEG-PRIVATE-POSE-REVIEW-V1",
              "characterId":"p0_character_001",
              "entryHtml":"review/p15-08-mid-angle.html",
              "sourceFiles":checked,
              "artSourceAdmission":"PENDING_INDEPENDENT_POSE_REVIEW"}
    ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(ARCHIVE,"w",compression=ZIP_DEFLATED,compresslevel=3) as archive:
        for item in checked:
            info=ZipInfo(item["path"],FIXED)
            info.compress_type=ZIP_DEFLATED
            info.external_attr=0o100644<<16
            archive.writestr(info,(ROOT/item["path"]).read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=3)
        info=ZipInfo("manifest.json",FIXED)
        info.compress_type=ZIP_DEFLATED
        info.external_attr=0o100644<<16
        archive.writestr(info,json.dumps(manifest,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    with ZipFile(ARCHIVE) as archive:
        if archive.testzip() is not None:raise AssertionError("ZIP CRC check failed")
        for item in checked:
            if hashlib.sha256(archive.read(item["path"])).hexdigest()!=item["sha256"]:
                raise AssertionError("ZIP member SHA differs")
        count=len(archive.namelist())
    data={
      "schema":"KOMA-P15-08-55DEG-POSE-REVIEW-PACKAGE-V1",
      "characterId":"p0_character_001",
      "archivePath":str(ARCHIVE.relative_to(ROOT)),
      "sha256":sha(ARCHIVE),
      "bytes":ARCHIVE.stat().st_size,
      "entries":count,
      "htmlEntry":"review/p15-08-mid-angle.html",
      "artisticAdmission":"PENDING_POSE_AND_HAIRPIN_CORRESPONDENCE",
    }
    REC.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(data,ensure_ascii=False))


if __name__=="__main__":
    run()
