#!/usr/bin/env python3
"""Register original P0 45/90° ArtMeshes with See-through-generated front underpaint.

This is a parallel VDD visual-review candidate. It does not replace the
genuine recovered P0 canonical image or the existing three-view registry.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fp:
        for chunk in iter(lambda:fp.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def run(assets,out):
    assets=Path(assets).resolve();out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    canonical=json.loads((assets/"parts.json").read_text())
    canonicalQA=json.loads((assets/"qa.json").read_text())
    alternate=assets/"p4-see-through/front/integrated"
    model=json.loads((alternate/"integrated-parts.json").read_text())
    modelQA=json.loads((alternate/"integration-qa.json").read_text())
    assert canonical["characterId"]==model["characterId"]=="p0_character_001"
    byId={p["semanticId"]:p for p in model["parts"]}
    assert len(byId)==13 and len(canonical["parts"])==39
    addedPixels=0
    manifest=copy.deepcopy(canonical)
    for rec in manifest["parts"]:
        sid=rec["semanticId"]
        if rec["yawDeg"]!=0: continue
        new=byId[sid]
        assert rec["mesh"]["vertexIds"]==new["mesh"]["vertexIds"]
        assert rec["mesh"]["triangles"]==new["mesh"]["triangles"]
        modelSource=alternate/new["path"]
        assert modelSource.is_file() and sha(modelSource)==new["frameSha256"]
        with Image.open(modelSource) as im:
            assert im.mode=="RGBA" and im.size==(1024,1024)
        rec.update({
          "path":str(modelSource.relative_to(assets)),
          "frameSha256":new["frameSha256"],
          "underpaintSource":"See-through inferred P0 front PSD",
          "underpaintPSDSHA256":modelQA["inferencePSDSHA256"],
          "additionalUnderpaintPixels":new["additionalInferredNativePixels"],
          "visualReviewed":False
        })
        addedPixels+=new["additionalInferredNativePixels"]
    for p in manifest["parts"]:
        assert sha(assets/p["path"])==p["frameSha256"]
    manifest.update({
      "sourceStatus":"P0_0DEG_SEETHROUGH_ARTMESH_REVIEW_CANDIDATE",
      "sourceApprovedHeroSHAverified":False,
      "visualApproval":"VDD_ARTISTIC_REVIEW_PENDING",
      "frontSemanticUnderpaintSource":"P0 original source + See-through PSD",
      "frontAddedUnderpaintPixels":addedPixels,
      "anglesUsingModelUnderpaint":[0],
      "anglesUsingRecoveredGIFLayers":[45,90]
    })
    qa={
      "schema":"KOMA-P0-P4-MULTIVIEW-CANDIDATE-QA-V1",
      "characterId":"p0_character_001",
      "status":"REVIEW_CANDIDATE",
      "role":"P0 real 0/45/90 view semantic-layer VDD with PSD source for front hidden pixels",
      "registeredSemanticViews":len(manifest["parts"]),
      "artMeshTopologyStatus":"CANONICAL_49_VERTICES_72_TRIANGLES",
      "psdSourceSha256":modelQA["inferencePSDSHA256"],
      "frontUnderpaintPixels":addedPixels,
      "frontStaticSourceIoU":modelQA["metrics"]["originalStaticSilhouetteIoU"],
      "sourceApprovedHeroSHAverified":False,
      "artisticAcceptance":"PENDING"
    }
    (out/"parts.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    (out/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(qa,indent=2,ensure_ascii=False))
    return qa

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assets",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.assets,a.out)
