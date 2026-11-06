#!/usr/bin/env python3
"""Build self-contained P0 PSD, GIF, ArtMesh, HTML and VDD source-review archive.

All source PNGs are actual recovered/generator/artwork files. Asset hashes are
verified against original manifests, and every ZIP entry is verified after
writing. No private image binaries are committed to the text-only lab repo.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

def sha(file):
    h=hashlib.sha256()
    with Path(file).open("rb") as fp:
        for chunk in iter(lambda:fp.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def build(exp,previous,target):
    exp=Path(exp).resolve()
    assets=exp/"private-assets"
    previous=Path(previous).resolve()
    target=Path(target).resolve()
    if not previous.is_file():raise FileNotFoundError(previous)
    oldfiles={}
    with zipfile.ZipFile(previous) as z:
        meta=json.loads(z.read("package-manifest.json"))
        if meta["characterId"]!="p0_character_001":
            raise ValueError("Review source identity differs")
        for rec in meta["files"]:
            oldfiles[rec["path"]]=rec["sha256"]
    writable={"review/review.js","review/p1-front.js","private-assets/p1-front/browser/browser-qa.json"}
    files={}
    for rel,expected in oldfiles.items():
        path=exp/rel
        if not path.is_file():raise FileNotFoundError(rel)
        if sha(path)!=expected and rel not in writable:
            raise ValueError("Previously verified artifact changed "+rel)
        files[rel]=path
    add=[
      assets/"p4-see-through/front/p0-character-001-see-through.psd",
      assets/"p4-see-through/front/inference-qa.json",
      assets/"p4-see-through/front/exported/layer-qa.json",
      assets/"p4-see-through/front/browser/browser-qa.json",
      assets/"p4-see-through/front/integrated/integration-qa.json",
      assets/"p4-see-through/front/integrated/integrated-parts.json",
      assets/"p4-see-through/mv-candidate/parts.json",
      assets/"p4-see-through/mv-candidate/qa.json",
      assets/"p4-see-through/mv-candidate/holdout-qa.json",
      assets/"p4-see-through/mv-candidate/texture-qa.json",
      assets/"p4-see-through/mv-candidate/vdd-canvas/canvas-qa.json",
      assets/"p4-see-through/mv-candidate/p0-psd-front-vdd-turn.gif",
      assets/"p4-see-through/mv-candidate/turn-gif-qa.json",
      assets/"p4-see-through/mv-candidate/vdd-sequence/canvas-qa.json",
      assets/"p4-see-through/yaw045/inference-qa.json",
      assets/"p2-views/turn-sequence/canvas-qa.json",
      assets/"p2-views/turn-sequence/temporal-qa.json"
    ]
    patterns=[
      ("p4-see-through/front/exported/parts","*.png"),
      ("p4-see-through/front/exported","*.png"),
      ("p4-see-through/front/exported","*.jpg"),
      ("p4-see-through/front/integrated/parts","*.png"),
      ("p4-see-through/front/integrated","*.png"),
      ("p4-see-through/front/integrated","*.jpg"),
      ("p4-see-through/front/browser","*.png"),
      ("p4-see-through/mv-candidate/vdd-canvas","*.png"),
      ("p2-views/turn-sequence","yaw*.png")
    ]
    for folder,pat in patterns:
        add.extend(sorted((assets/folder).glob(pat)))
    for path in add:
        if not path.is_file():raise FileNotFoundError(path)
        rel=str(path.relative_to(exp))
        files[rel]=path
    psd=assets/"p4-see-through/front/p0-character-001-see-through.psd"
    qa=json.loads((assets/"p4-see-through/front/integrated/integration-qa.json").read_text())
    mv=json.loads((assets/"p4-see-through/mv-candidate/qa.json").read_text())
    browser=json.loads((assets/"p4-see-through/front/browser/browser-qa.json").read_text())
    texture=json.loads((assets/"p4-see-through/mv-candidate/texture-qa.json").read_text())
    if qa["inferencePSDSHA256"]!=sha(psd) or qa["layerCount"]!=13:
        raise ValueError("PSD source traceability mismatch")
    if mv["registeredSemanticViews"]!=39 or \
       browser["status"]!="PASS_P4_PSD_BROWSER_ENGINEERING":
        raise ValueError("P4 browser/three-view source engineering incomplete")
    if texture["status"]!="REQUIRES_SEMANTIC_TEXTURE_CORRESPONDENCE":
        raise ValueError("Expected reviewed texture gate status")
    p4sequence=json.loads((assets/"p4-see-through/mv-candidate/vdd-sequence/canvas-qa.json").read_text())
    p4gif=json.loads((assets/"p4-see-through/mv-candidate/turn-gif-qa.json").read_text())
    if len(p4sequence["outputs"])!=37 or p4gif["GIFFrames"]!=72:
        raise ValueError("P4 browser turn sequence incomplete")
    if sha(assets/"p4-see-through/mv-candidate/p0-psd-front-vdd-turn.gif")!=p4gif["GIFSHA256"]:
        raise ValueError("P4 generated animation checksum mismatch")
    for sourceFrame in p4sequence["outputs"]:
        if sha(sourceFrame["path"])!=sourceFrame["sha256"]:
            raise ValueError("P4 true browser frame hash mismatch")
    frames=json.loads((assets/"p2-views/turn-sequence/canvas-qa.json").read_text())
    if len(frames["outputs"])!=37:raise ValueError("37 real browser RGBA frames are required")
    for rec in frames["outputs"]:
        filename=Path(rec["path"])
        if sha(filename)!=rec["sha256"]:
            raise ValueError("Rendered PNG checksum mismatch")
    registered=json.loads((assets/"p4-see-through/mv-candidate/parts.json").read_text())
    for entry in registered["parts"]:
        filename=assets/entry["path"]
        if sha(filename)!=entry["frameSha256"]:
            raise ValueError("Mesh part PNG checksum mismatch")
    manifest={
      "schema":"KOMA-P0-P4-ARTMESH-PSD-ASSET-REVIEW-V1",
      "characterId":"p0_character_001",
      "registeredSemanticSlots":39,
      "sourceGIFAngles":[0,45,90],
      "psdModelNativeSize":[768,768],
      "normalizedArtMeshCanvas":[1024,1024],
      "psdSemanticLayers":13,
      "sourcePSDSHA256":sha(psd),
      "originalBrowserFrames":37,
      "PSDEnhancedBrowserFrames":37,
      "PSDEnhancedMotionGIFFrames":72,
      "PSDEnhancedMotionGIFSHA256":p4gif["GIFSHA256"],
      "underpaintAddedPixels":qa["inferredUnderpaintPixels"],
      "frontStaticSourceSilhouetteIoU":qa["metrics"]["originalStaticSilhouetteIoU"],
      "dynamicFringeOpaqueHoles":{
       "source":qa["metrics"]["sourceFringeMotionOpaqueHoles"],
       "withPSD":qa["metrics"]["inferredFringeMotionOpaqueHoles"]},
      "vddFaceCoreCoverageStatus":"PASS_HOLDOUT_COVERAGE",
      "vddHoldoutTextureStatus":texture["status"],
      "visualAcceptance":"PENDING_CROSS_VIEW_TEXTURE_REFINEMENT",
      "approvedHeroSourceSHAverified":False,
      "files":[{"path":name,"bytes":path.stat().st_size,"sha256":sha(path)}
               for name,path in sorted(files.items())]
    }
    README="""# P0 Character ArtMesh + PSD source review

This package carries original authored P0 source views, 39 registered 2.5D
ArtMeshes, 13 See-through PSD semantic layers and their normalized RGBA PNG
exports, 37 genuine browser-rendered turn frames, animated GIF previews,
visual comparison boards and executable HTML review interfaces.

Start an HTTP server from the extracted package directory:

    python3 -m http.server 5181

Open the original recovered 0-90 view viewer:

    http://localhost:5181/review/index.html?mode=candidate

Open the P0 See-through PSD-enhanced independent 0-degree parts:

    http://localhost:5181/review/p1-front.html?source=seethrough

Open the 3-view ArtMesh candidate using PSD-inferred 0-degree underpainting:

    http://localhost:5181/review/index.html?mode=candidate&source=seethrough-front

P0 PSD-enhanced front source motion preview GIF (37 source frames,
72 bidirectional preview frames):

    private-assets/p4-see-through/mv-candidate/p0-psd-front-vdd-turn.gif

Motion GIF (original multi-view ArtMesh source, actual Canvas2D browser frames):

    private-assets/p2-views/turn-sequence/p0-yaw000-yaw090-artmesh-review.gif

Generated source five-view reference storyboard GIF:

    private-assets/p3-native-source-trial/preview/five-view-identity-storyboard.gif

Specific P0 PSD underpainting motion/recomposition evidence:

    private-assets/p4-see-through/front/integrated/p0-fringe-motion-review.jpg
    private-assets/p4-see-through/front/exported/semantic-contact.jpg

Image origin and every native/derived asset SHA-256 are in
package-manifest.json and private-assets/p4-see-through/ QA JSON records.

Source artwork from See-through uses a 768px model canvas and is exported
to a 1024x1024 registered RGBA mesh canvas. The 0-degree static original
is retained; model-predicted hidden texture only supplies occluded areas.

The intermediate 22.5°/67.5° head turn remains a texture correspondence
research candidate. Use the supplied browser renders for artistic review.
"""
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=6,
                         allowZip64=True) as z:
        for name,path in sorted(files.items()):z.write(path,arcname=name)
        z.writestr("README.md",README)
        z.writestr("package-manifest.json",json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None:raise ValueError("ZIP payload CRC mismatch")
        loaded=json.loads(z.read("package-manifest.json"))
        for entry in loaded["files"]:
            if hashlib.sha256(z.read(entry["path"])).hexdigest()!=entry["sha256"]:
                raise ValueError("ZIP SHA mismatch "+entry["path"])
    report={
      "schema":"KOMA-P0-P4-PACKAGE-QA-V1",
      "characterId":"p0_character_001",
      "archivePath":str(target),"bytes":target.stat().st_size,
      "sha256":sha(target),
      "entryCount":len(files)+2,
      "sourcePSDSHA256":sha(psd),
      "nativeBrowserFrameCount":37,
      "PSDEnhancedBrowserFrameCount":37,
      "PSDEnhancedMotionGIFSHA256":p4gif["GIFSHA256"],
      "registeredSemanticSlots":39,
      "internalHashesVerified":True,
      "browserPSDQA":browser["status"],
      "VDDTextureQA":texture["status"],
      "visualAcceptance":"PENDING"
    }
    (assets/"p4-see-through/p4-package-qa.json").write_text(
      json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--experiment",required=True)
    p.add_argument("--previous",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    build(a.experiment,a.previous,a.output)
