#!/usr/bin/env python3
"""Audit existing See-through PSDs and export unmodified native layers.

Not an acceptance of identity, underpainting quality, or a 13-role ArtMesh mapping.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from psd_tools import PSDImage

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "private-assets"
QA = ROOT / "evidence/p15-14-existing-psd-mapping-qa.json"
SOURCES = {
    "yaw000": "p4-see-through/front/p0-character-001-see-through.psd",
    "yaw045": "p5-see-through/yaw045/p0-character-001-see-through.psd",
    "yaw077p5": "p15-independent-candidates/seethrough/yaw077p5-layers.psd",
}
DIRECT = {
    "back hair": ["hair.back"], "neck": ["body.reference"],
    "topwear": ["body.reference"], "face": ["face.skin"],
    "nose": ["nose"], "mouth": ["mouth"],
}
AMBIGUOUS = {
    "ears": ["ear.near", "ear.far"],
    "eyewhite": ["eye.near", "eye.far"],
    "irides": ["eye.near", "eye.far"],
    "eyelash": ["eye.near", "eye.far"],
    "eyebrow": ["eye.near", "eye.far"],
    "front hair": ["hair.front", "hair.side", "hair.ahoge"],
    "headwear": ["hair.clip.cross_gold"],
    "handwear": ["body.reference"],
}

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def audit(name, rel, output):
    src=PRIVATE/rel
    assert src.read_bytes()[:4]==b"8BPS", "Not a PSD"
    psd=PSDImage.open(src)
    assert psd.size==(768,768), psd.size
    layers=list(psd)
    outdir=output/name
    outdir.mkdir(parents=True,exist_ok=True)
    cover=np.zeros((768,768),dtype=np.float32)
    entries=[]
    for i,layer in enumerate(layers):  # PSD order: top to bottom
        native=layer.composite(viewport=(0,0,768,768))
        if native is None:
            entries.append({"index":i,"name":layer.name,"empty":True})
            continue
        rgba=np.asarray(native.convert("RGBA"))
        if rgba.shape[:2]!=(768,768):
            raise AssertionError(("Unexpected layer dimensions",layer.name,rgba.shape))
        alpha=rgba[:,:,3].astype(np.float32)/255.0
        visible=alpha>.05
        occluded=visible & (cover>.95)
        partial=visible & (cover>.05) & (cover<=.95)
        role=DIRECT.get(layer.name) or AMBIGUOUS.get(layer.name)
        status="DIRECT_ROLE_CLASS_ONLY" if layer.name in DIRECT else "SPLIT_OR_IDENTITY_REVIEW_REQUIRED"
        if not role:status="UNMAPPED"
        dest=outdir/f"native-{i:02d}.png"
        Image.fromarray(rgba,"RGBA").save(dest)
        entries.append({"index":i,"name":layer.name,"status":status,
                        "candidateRoles":role or [],
                        "pixelCount":int(visible.sum()),
                        "fullyCoveredPixels":int(occluded.sum()),
                        "partiallyCoveredPixels":int(partial.sum()),
                        "sha256":sha(dest),"path":str(dest.relative_to(PRIVATE))})
        cover=1-(1-cover)*(1-alpha)
    composed=psd.composite()
    dest=outdir/"psd-composite.png"
    composed.save(dest)
    return {"angle":name,"source":rel,"sourceSHA256":sha(src),
            "size":list(psd.size),"nativeLayerCount":len(layers),
            "nativeLayerEntries":entries,
            "underpaintCandidateCoveredPixelInstances":sum(e.get("fullyCoveredPixels",0) for e in entries),
            "verifiedUnderpaintCorrectness":False,
            "compositePath":str(dest.relative_to(PRIVATE)),"compositeSHA256":sha(dest),
            "status":"PSD_LAYER_EXTRACTION_VERIFIED_MAPPING_INCOMPLETE"}

def run():
    roles=json.loads((ROOT/"evidence/p15-10-semantic-arc-qa.json").read_text())["roles"]
    assert len(roles)==13
    out=PRIVATE/"p15-14-existing-psd-audit"
    files=[audit(k,v,out) for k,v in SOURCES.items()]
    report={"schema":"KOMA-P15-14-EXISTING-PSD-AUDIT-V1",
      "characterId":"p0_character_001","roles":roles,
      "sources":files,"sourceP0IdentityAudit":"Existing PSDs, not newly inferred PSD; verify identity externally",
      "directRoleAcceptance":False,
      "layerSplitAccepted":False,
      "hiddenRegionArtAcceptance":False,
      "artmeshIndependentLayersAccepted":0,
      "next":"Split eye and ear by geometry; separate front hair, ahoge and clip with transparency and inspect hidden paint"}
    QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":"AUDIT_OK_MAPPING_INCOMPLETE",
      "psds":len(files),"layers":sum(f["nativeLayerCount"] for f in files),
      "coveredPixelInstances":[f["underpaintCandidateCoveredPixelInstances"] for f in files],
      "mapped13RolesAccepted":0,
      "qa":str(QA)},ensure_ascii=False))
if __name__=="__main__":
    run()
