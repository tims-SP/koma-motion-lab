#!/usr/bin/env python3
"""Freeze the P0 55° view authoring contract from SHA-verified neighbouring art."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/"private-assets"
TARGET=ROOT/"metadata/p15-08-yaw055-generation-contract.json"


def digest(file):
    h=hashlib.sha256()
    with Path(file).open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def create():
    p0=load(PRIVATE/"p5-see-through/mv-candidate/parts.json")
    painted=load(PRIVATE/"p15-independent-candidates/yaw065-artmesh/ingest-qa.json")
    if p0["characterId"]!="p0_character_001" or painted["characterId"]!="p0_character_001":
        raise ValueError("P0 canonical source identity not aligned")
    src45=next(x for x in p0["wholeViews"] if x["yawDeg"]==45)
    src90=next(x for x in p0["wholeViews"] if x["yawDeg"]==90)
    refs=[
       {"yawDeg":45.,"path":src45["path"],"sha256":src45["sha256"],
        "role":"original P0 yaw45 portrait and anatomical anchor source"},
       {"yawDeg":65.,"path":painted["referencePainting"]["path"],
        "sha256":painted["referencePainting"]["sha256"],
        "role":"generated yaw65 view geometry and pose reference"},
       {"yawDeg":90.,"path":src90["path"],"sha256":src90["sha256"],
        "role":"original P0 full side profile and physical handedness control"},
    ]
    for item in refs:
        if digest(PRIVATE/item["path"])!=item["sha256"]:
            raise ValueError("Source artwork SHA mismatch at "+str(item["yawDeg"]))
    entries=sorted((x for x in p0["parts"] if x["yawDeg"]==45),
                   key=lambda x:x["depthOrder"])
    parts=[{"semanticId":e["semanticId"],"depthOrder":e["depthOrder"],
             "output":f"private-assets/p15-08-yaw055/parts/{e['semanticId']}.png",
             "nativeRGBA":True,"canvas":[1024,1024],
             "anatomicalSide":"character-physical-side"} for e in entries]
    if len(parts)!=13 or [x["depthOrder"] for x in parts]!=list(range(13)):
        raise AssertionError("Canonical semantic and depth coverage changed")
    contract={
      "schema":"KOMA-P0-P15-08-55DEG-INDEPENDENT-ARTWORK-CONTRACT-V1",
      "characterId":"p0_character_001",
      "yawDeg":55.0,
      "bodyFrame":"unchanged head-center, shoulder-center and camera size",
      "originalHeroExpectedSHA256":"e95a4b694777f4dcd2e085b25b10d76058d65cd1f8c6ef46971caa8005cb7e54",
      "originalHeroSourceSHA256Verified":False,
      "references":refs,
      "portrait":{
         "path":"private-assets/p15-08-yaw055/yaw055-source-rgba.png",
         "canvas":[1024,1024],
         "mode":"RGBA",
         "alpha":"fine edge alpha with transparent background",
         "sourceMethod":"independently authored Japanese 2D cel-style key painting",
         "referenceBlendAngle":"45 to 65 interpolation midpoint at yaw55",
      },
      "physicalIdentity":{
         "hair":"neck-length mauve-pink bob, side fringe, one ahoge",
         "eyes":"violet-pink, near eye in front, far eye partially turning away",
         "clip":"single gold cross on character physical left",
         "clothing":"navy jacket with gold trim, white collar, burgundy bow",
         "yawConvention":"0 front,90 right-facing profile; preserve physical left/right",
      },
      "keyAnatomicalAnchors":[
         "face.chin","face.jaw.near","eye.near.iris","eye.far.iris",
         "nose","mouth","ear.near","ear.far","hair.front",
         "hair.back","hair.ahoge.root","hair.clip.center","shoulder.center"
      ],
      "semanticLayers":parts,
      "hiddenSourceRoles":["hair.back","hair.side","face.skin","eye.far","ear.far"],
      "sourceRoleRule":"each semantic PNG independently painted and registered, no composite-only role mask",
      "fullKeyviewContract":"all 13 rendered parts reconstruct the yaw55 portrait by real depth order and maintain physical source identity",
      "paintPrompt":"Using only the supplied identical-character P0 45-degree, 65-degree, and 90-degree source artworks, independently draw a high-fidelity Japanese TV anime cel-style yaw55 (camera-right) head-and-shoulders view on a 1024x1024 transparent registered canvas. The face angle is geometrically halfway between the 45-degree near-frontal two-eye reference and the 65-degree near-profile single-eye reference. Retain a narrow partially occluded far eye, one near eye with violet-pink iris, coherent nose bridge, chin and ear-root anatomy; one mauve-pink ahoge, neck-length bob, and exactly one physically left gold crossed hair clip as visibility permits. Preserve the navy-and-gold school uniform and burgundy bow. Stable hairstyle topology, fine strokes, no text, no opaque backdrop.",
      "partPrompt":"For the same yaw55 independent key portrait, render exactly one semanticId item as a separate 1024x1024 native RGBA8 image with its full-canvas position unchanged and other parts fully transparent. Preserve source strokes, correct role identity and physical handedness; include hidden underpaint when occluded by foreground geometry. The 13 outputs must remain individually editable and recombine to the key portrait.",
      "acceptance":{
         "requiredIndependentPartImages":13,
         "requiredIndependentPortraits":1,
         "sourcePNGPixelRecompositionMaximumDifference":0,
         "sourceReferenceSHA256":True,
         "originalHeroSourceApprovalRequired":True,
         "heldoutAnglesToAuthor":[52.5,57.5],
         "silhouetteIoUMin":0.90,
         "maxRelativeSilhouetteAreaError":0.08,
         "visualChecks":["angle geometry", "near/far eye silhouette",
                         "nose and jaw shape","ear location",
                         "front,side,back hair stroke", "hairpin physical side",
                         "collar and bow geometry","continuous occlusion"],
      },
      "status":"P15_08_AUTHORING_INPUT_REGISTERED"
    }
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":contract["status"],
                      "sourceAngles":[x["yawDeg"] for x in refs],
                      "registeredPartRoles":len(parts),
                      "contract":str(TARGET.relative_to(ROOT))},ensure_ascii=False))
    return contract

if __name__=="__main__":
    create()
