#!/usr/bin/env python3
"""Assemble a standalone P0 3-view RGBA ArtMesh / HTML / QA review bundle."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def sha(file):
    h=hashlib.sha256()
    with Path(file).open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def package(experiment,output):
    experiment=Path(experiment).resolve()
    source=experiment/"private-assets"
    output=Path(output).resolve()
    files={}
    allowed=[
      "review/index.html","review/review.js","review/p1-front.html","review/p1-front.js",
      "private-assets/parts.json","private-assets/qa.json",
      "private-assets/p1-front/parts.json",
      "private-assets/p1-front/engineering-qa.json",
      "private-assets/p1-front/browser/browser-qa.json",
      "private-assets/p2-views/parts.json",
      "private-assets/p2-views/reconstruction-qa.json",
      "private-assets/p2-views/assembled-view-registry-qa.json",
      "private-assets/p2-views/browser/browser-qa.json",
      "private-assets/p2-views/vdd-canvases/canvas-qa.json",
      "private-assets/p2-views/vdd-canvases/holdout-qa.json",
      "private-assets/p2-views/vdd-canvases/texture-qa.json",
      "private-assets/p2-views/turn-sequence/turn-gif-qa.json",
      "private-assets/p2-views/turn-sequence/p0-yaw000-yaw090-artmesh-review.gif",
      "private-assets/p2-audit/semantic-audit.json",
      "private-assets/p2-audit/p2-view-semantic-contact.jpg",
      "private-assets/p1-front/diagnostics/front-pair.png",
      "private-assets/p1-front/diagnostics/semantic-contact.jpg",
      "private-assets/p1-front/diagnostics/front-reference.png"
    ]
    for name in allowed:
        file=experiment/name
        if not file.is_file():raise FileNotFoundError(name)
        files[name]=file
    partmanifest=json.loads((source/"parts.json").read_text())
    if len(partmanifest["parts"])!=39:raise ValueError("Expected 39 independently hashed ArtMesh records")
    for part in partmanifest["parts"]:
        target=source/part["path"]
        if sha(target)!=part["frameSha256"]:
            raise ValueError("bad layer SHA "+part["path"])
        files["private-assets/"+part["path"]]=target
    for angle in partmanifest["wholeViews"]:
        target=source/angle["path"]
        if sha(target)!=angle["sha256"]:
            raise ValueError("bad source whole sha")
        files["private-assets/"+angle["path"]]=target
    for root in (
       source/"p2-views/browser",
       source/"p2-views/vdd-canvases",
       source/"p1-front/browser",
       source/"p2-views/diagnostics"):
        for f in root.glob("*.png"):
            files[str(f.relative_to(experiment))]=f
    for source_asset in (source/"whole/head-turn-8view.gif",
                         source/"gifs/face.gif",source/"gifs/hair.gif",
                         source/"gifs/identity.gif"):
        files[str(source_asset.relative_to(experiment))]=source_asset
    # Include source archive with full GIF and decoded reference evidence.
    original_archive=source/"transport"
    for file in (original_archive/"asset-transport-manifest.json",):
        if file.is_file():files[str(file.relative_to(experiment))]=file
    qa=json.loads((source/"p2-views/vdd-canvases/holdout-qa.json").read_text())
    texture=json.loads((source/"p2-views/vdd-canvases/texture-qa.json").read_text())
    if texture["status"] not in ("REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE",
                                 "PASS_TEXTURE_EDGE_DIAGNOSTIC"):
        raise ValueError("Texture art QA source missing")
    sequence=json.loads((source/"p2-views/turn-sequence/turn-gif-qa.json").read_text())
    if sequence["sourceFrameCount"]!=37 or sequence["GIFFrames"]!=72:
        raise ValueError("Real 37-frame motion GIF missing")
    if sha(source/"p2-views/turn-sequence/p0-yaw000-yaw090-artmesh-review.gif")!=sequence["GIFSHA256"]:
        raise ValueError("Review GIF digest differs from source QA")
    engineering=json.loads((source/"p1-front/engineering-qa.json").read_text())
    if qa["status"] not in ("PASS_HOLDOUT_COVERAGE","REQUIRES_VDD_BOUNDARY_REFINEMENT"):
        raise ValueError("Current review requires explicit recorded holdout status")
    if engineering["status"]!="PASS_STRUCTURAL_ENGINEERING":
        raise ValueError("Front engineering source QA missing")
    manifest={
      "schema":"KOMA-P0-MULTIVIEW-ARTMESH-REVIEW-PACKAGE-V3",
      "characterId":"p0_character_001",
      "source":"recovered_original_GIF_art_workflow",
      "angles":[0,45,90],"holdoutAngles":[22.5,67.5],
      "registeredSemanticParts":39,
      "staticArtMeshStatus":"ENGINEERING_PASS_THREE_KEYS",
      "underpaintStatus":"P0_source_palette_anatomical_contour_candidate",
      "holdoutVisualStatus":qa["status"],
      "intermediateArtisticReview":"PENDING_TEXTURE_CORRESPONDENCE_REFINEMENT",
      "textureEdgeStatus":texture["status"],
      "textureHoldouts":[{"angle":p["angle"],"relativeEdgeDensity":p["edgeDensityRelativeToAdjacentMax"]}
                         for p in texture["holdouts"]],
      "sourceFrameCount":sequence["sourceFrameCount"],
      "reviewGIFSHA256":sequence["GIFSHA256"],
      "approvedHeroOriginalSHAverified":False,
      "files":[{"path":name,"bytes":f.stat().st_size,"sha256":sha(f)}
               for name,f in sorted(files.items())]
    }
    readme="""# P0 Multiview ArtMesh Review

This is an executable visual-review package containing the recovered
p0_character_001 source artwork and the actual independently registered
0, 45 and 90-degree RGBA semantic layers.

Start an HTTP server from the extracted package root:

    python3 -m http.server 5181

Then open:

    http://localhost:5181/review/index.html?mode=candidate
    http://localhost:5181/review/p1-front.html

Review both original authored keyframes and independent parts in the 2D
canvas. The 22.5 and 67.5 holdouts are rendered coverage diagnostics. The\nface color underpaint is derived from genuine P0 cheek pigment and geometry.

Quality evidence:
    private-assets/p1-front/engineering-qa.json
    private-assets/p2-views/reconstruction-qa.json
    private-assets/p2-views/vdd-canvases/holdout-qa.json
    private-assets/p2-views/vdd-canvases/texture-qa.json
    private-assets/p2-views/turn-sequence/p0-yaw000-yaw090-artmesh-review.gif
    private-assets/p2-views/turn-sequence/turn-gif-qa.json
    private-assets/p2-views/browser/
    private-assets/p2-views/vdd-canvases/

P0 identity and source SHA metadata are persisted as written, but the
separate approved hero-master source file is still awaiting direct matching.
The edge-density texture gate quantifies the remaining interpolation seams.\nFace texture continuity in intermediate turns requires further VDD refinement and
artistic review before this is a production animation asset.
"""
    output.parent.mkdir(exist_ok=True,parents=True)
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,file in sorted(files.items()):z.write(file,arcname=name)
        z.writestr("package-manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
        z.writestr("README.md",readme)
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None:raise ValueError("Bad ZIP member")
        saved=json.loads(z.read("package-manifest.json"))
        for item in saved["files"]:
            if hashlib.sha256(z.read(item["path"])).hexdigest()!=item["sha256"]:
                raise ValueError("mismatched zip content "+item["path"])
    qa_record={
       "schema":"KOMA-P0-REVIEW-PACKAGE-QA-V3","characterId":"p0_character_001",
       "path":str(output),"sha256":sha(output),"bytes":output.stat().st_size,
       "files":len(files)+2,"angles":[0,45,90],"parts":39,
       "internalHashesVerified":True,"staticEngineering":"PASS",
       "holdoutArtQuality":qa["status"],
       "textureEdgeStatus":texture["status"],
       "GIFSHA256":sequence["GIFSHA256"],
       "sourceApprovedHeroOriginalSHAverified":False}
    (source/"p2-views/review-package-qa.json").write_text(
        json.dumps(qa_record,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(qa_record,ensure_ascii=False,indent=2))
    return qa_record

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--experiment",default=str(ROOT))
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    package(args.experiment,args.output)
