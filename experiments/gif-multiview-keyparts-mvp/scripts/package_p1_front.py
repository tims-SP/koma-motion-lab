#!/usr/bin/env python3
"""Package P0 real-front ArtMesh preview assets and verified browser review privately."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def create(experiment,output):
    experiment=Path(experiment).resolve()
    p1=experiment/"private-assets/p1-front"
    manifest=json.loads((p1/"parts.json").read_text())
    engineering=json.loads((p1/"engineering-qa.json").read_text())
    browser=json.loads((p1/"browser/browser-qa.json").read_text())
    if engineering["status"]!="PASS_STRUCTURAL_ENGINEERING" or \
       browser["status"]!="PASS_P1_BROWSER_ENGINEERING":
        raise ValueError("Source-driven engineering and browser QA required")
    if len(manifest["parts"])!=13:
        raise ValueError("P1 front source layers incomplete")
    file_list=[
       "review/p1-front.html","review/p1-front.js",
       "private-assets/p1-front/parts.json",
       "private-assets/p1-front/qa.json",
       "private-assets/p1-front/engineering-qa.json",
       "private-assets/p1-front/diagnostics/front-reference.png",
       "private-assets/p1-front/diagnostics/front-composite.png",
       "private-assets/p1-front/diagnostics/front-pair.png",
       "private-assets/p1-front/diagnostics/semantic-contact.jpg",
       "private-assets/p1-front/diagnostics/pixel-difference.png",
       "private-assets/p1-front/diagnostics/eye-near-motion-check.png",
       "private-assets/p1-front/browser/browser-qa.json",
       "private-assets/p1-front/browser/p1-front-default.png",
       "private-assets/p1-front/browser/p1-front-eye-near-10px.png",
       "private-assets/p1-front/browser/p1-front-hair-parts.png",
       "sources/head-turn-8view.gif",
       "sources/face-semantic-0-45-90.gif",
       "sources/hair-semantic-0-45-90.gif",
       "sources/identity-semantic-0-45-90.gif"
    ]
    assets=experiment/"private-assets"
    content={}
    for rel in file_list:
        if rel.startswith("sources/"):
            target=assets/"recovered-review"/rel
            if not target.is_file():raise FileNotFoundError(target)
            content[rel]=target
        else:
            target=experiment/rel
            if not target.is_file():raise FileNotFoundError(target)
            content[rel]=target
    for part in manifest["parts"]:
        rel="private-assets/"+part["path"]
        target=assets/part["path"]
        if sha(target)!=part["frameSha256"]:
            raise ValueError("Source hash mismatch for "+rel)
        content[rel]=target
    for screenshot in browser["shots"]:
        name=screenshot["name"]
        actual=p1/"browser"/(name+".png")
        if sha(actual)!=screenshot["sha256"]:
            raise ValueError("Browser capture mismatch "+name)
    archive_manifest={
       "schema":"KOMA-P0-FRONT-ARTMESH-PRIVATE-EXPORT-V1",
       "characterId":"p0_character_001",
       "yawDeg":0,
       "sourceRole":"recovered_p0_original_GIF_with_semantic_occlusion_completion",
       "engineeringStatus":engineering["status"],
       "visualStatus":"REQUIRES_MOTION_ART_REVIEW",
       "sourceHeroShaVerified":False,
       "totalArtMeshParts":len(manifest["parts"]),
       "sourceGIFs":4,
       "files":[{"path":rel,"bytes":p.stat().st_size,"sha256":sha(p)}
                for rel,p in sorted(content.items())],
       "browserShots":[{"name":x["name"],"sha256":x["sha256"]}
                        for x in browser["shots"]]
    }
    readme="""# p0_character_001 | Front ArtMesh Review

Original authored P0 appearance from the recovered multi-view GIF series.

## Explore

From the extracted ZIP root, start a local HTTP server:

    python3 -m http.server 5181

Then open:

    http://localhost:5181/review/p1-front.html

Use the layer controls to inspect 13 semantic meshes. Horizontal eye sliders
exercise independent eye identity and occluded face skin filling.

## Engineering evidence

    private-assets/p1-front/engineering-qa.json
    private-assets/p1-front/browser/browser-qa.json
    private-assets/p1-front/diagnostics/front-pair.png

Source provenance and per-layer SHA-256 hashes are declared in
private-assets/p1-front/parts.json and archive-manifest.json.

The approved master SHA is still awaiting direct original-file verification.
Dynamic eye motion and hairstyle deformation require visual and structural
review before production animation use.
"""
    output=Path(output).resolve()
    output.parent.mkdir(exist_ok=True,parents=True)
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for rel,filename in sorted(content.items()):
            z.write(filename,arcname=rel)
        z.writestr("archive-manifest.json",json.dumps(archive_manifest,ensure_ascii=False,indent=2)+"\n")
        z.writestr("README.md",readme)
    with zipfile.ZipFile(output) as z:
        failed=z.testzip()
        if failed is not None:
            raise ValueError("Corrupt ZIP member "+failed)
        test=json.loads(z.read("archive-manifest.json"))
        for part in test["files"]:
            if hashlib.sha256(z.read(part["path"])).hexdigest()!=part["sha256"]:
                raise ValueError("Archive content mismatch "+part["path"])
    return {"schema":"KOMA-P0-FRONT-ARTMESH-PACKAGE-QA-V1",
            "characterId":"p0_character_001",
            "output":str(output),"bytes":output.stat().st_size,
            "sha256":sha(output),"zipFiles":len(content)+2,
            "sourceArtMeshes":len(manifest["parts"]),
            "engineeringStatus":engineering["status"],
            "browserStatus":browser["status"],
            "archiveIntegrityVerified":True,
            "visualStatus":"HUMAN_MOTION_ART_REVIEW_REQUIRED"}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--experiment",default=str(Path(__file__).resolve().parents[1]))
    p.add_argument("--output",required=True)
    args=p.parse_args()
    print(json.dumps(create(args.experiment,args.output),indent=2,ensure_ascii=False))
