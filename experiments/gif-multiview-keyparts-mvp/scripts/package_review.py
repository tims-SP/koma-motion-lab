#!/usr/bin/env python3
"""Build a reproducible private P0 review bundle from source GIFs."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fd:
        for chunk in iter(lambda:fd.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def run(repo,origin,browser,out):
    repo=Path(repo).resolve()
    origin=Path(origin).resolve()
    browser=Path(browser).resolve()
    out=Path(out).resolve()
    lab=repo/"experiments/gif-multiview-keyparts-mvp"
    private=lab/"private-assets"
    assert digest(origin)=="8ce3596f60a01b82df49926304c47041d8a8734689ae2a3126acada583666547"
    qa=json.loads((private/"candidate-v2/reconstruction-qa.json").read_text())
    assert qa["registeredSlots"]==39 and all(v["pixelsDifferent"]==0 for v in qa["pixelParity"].values())
    browser_report=json.loads((browser/"browser-qa.json").read_text())
    assert browser_report["status"]=="CANDIDATE_RENDER_ENGINEERING_PASS"
    pairs=[]
    for relative in ["review/index.html","review/review.js","README.md","contract.json",
                     "scripts/build_semantic_partition.py","scripts/flow_render.py",
                     "scripts/qa_temporal.py","scripts/capture_review.cjs"]:
        pairs.append((lab/relative,Path("experiments/gif-multiview-keyparts-mvp")/relative))
    for source in sorted((private/"candidate-v2").rglob("*")):
        if source.is_file():
            pairs.append((source,Path("experiments/gif-multiview-keyparts-mvp/private-assets/candidate-v2")/
                          source.relative_to(private/"candidate-v2")))
    for relative in ["parts.json","qa.json","whole/head-turn-8view.gif",
                     "gifs/face.gif","gifs/hair.gif","gifs/identity.gif"]:
        pairs.append((private/relative,Path("experiments/gif-multiview-keyparts-mvp/private-assets")/relative))
    for source in sorted(browser.glob("*.png")):
        pairs.append((source,Path("screenshots")/source.name))
    pairs.append((browser/"browser-qa.json",Path("screenshots/browser-qa.json")))
    pairs.append((private/"flow-smooth/yaw000-yaw090-flow-review.gif",
                  Path("diagnostics/flow-review.gif")))
    pairs.append((private/"flow-smooth/flow-qa.json",Path("diagnostics/flow-qa.json")))
    pairs.append((private/"flow-smooth/temporal-qa.json",Path("diagnostics/temporal-qa.json")))
    pairs.append((origin,Path("original-38-frames/gif_multiview_asset_review_2026-11-05.zip")))
    members=[]
    for source,rel in pairs:
        if not source.is_file():raise FileNotFoundError(source)
        members.append({"path":rel.as_posix(),"sha256":digest(source),
                        "bytes":source.stat().st_size})
    package={"schema":"KOMA-P0-MULTIVIEW-REVIEW-PACKAGE-V1",
             "characterId":"p0_character_001",
             "sourceOriginalGIFSha256":digest(origin),
             "framesRecovered":38,"registeredRGBAReviewLayers":39,
             "referenceYaw":[0,45,90],"holdouts":[22.5,67.5],
             "visualStatus":"CANDIDATE_ART_REVIEW",
             "approvedHeroSHAverified":False,
             "directPartGenerationAccepted":False,
             "members":members}
    out.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(out,"w",ZIP_DEFLATED,compresslevel=6) as z:
        for src,rel in pairs:z.write(src,rel.as_posix())
        z.writestr("package-manifest.json",json.dumps(package,indent=2,ensure_ascii=False)+"\n")
    with ZipFile(out) as z:
        assert z.testzip() is None
    return {"archive":str(out),"sha256":digest(out),"sizeBytes":out.stat().st_size,
            "members":len(members)+1,"status":package["visualStatus"]}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True)
    p.add_argument("--source-zip",required=True)
    p.add_argument("--browser-dir",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    print(json.dumps(run(a.repo,a.source_zip,a.browser_dir,a.output),indent=2))
