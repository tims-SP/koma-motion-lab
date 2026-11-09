#!/usr/bin/env python3
"""Source-hash and actual-browser acceptance of P15-05 hair part occlusion."""
import hashlib
import json
from pathlib import Path
from p15_hair_occlusion import registry, sha, ROLE_SET, OCCLUSION, KEYS

EXP=Path(__file__).resolve().parents[1]
PRIVATE=(EXP/"private-assets").resolve()


def load(path):
    return json.loads(path.read_text(encoding="utf8"))


def verify():
    hairfile=EXP/"evidence/p15-hair-correspondence-qa.json"
    browserfile=PRIVATE/"p15-hair-occlusion/browser/qa.json"
    hair=load(hairfile);browser=load(browserfile)
    if hair["characterId"]!="p0_character_001" or browser["characterId"]!="p0_character_001":
        raise AssertionError("original P0 identity mismatch")
    source,anchors,regions=registry(PRIVATE)
    if len(source)!=28 or hair["sourceViewSlotsVerified"]!=28:
        raise AssertionError("hair and context slots incomplete")
    if len({x["sha256"] for x in source.values()})!=28:
        raise AssertionError("source PNG ID completeness")
    if hair["semanticStrokeViewPairs"]!=12 or len(hair["strandPairCorrespondence"])!=12:
        raise AssertionError("cross-view hair stroke pairs incomplete")
    if hair["occlusionPairCount"]!=16:
        raise AssertionError("depth occlusion coverage incomplete")
    if set(hair["depthOcclusion"])!={str(x) for x in KEYS}:
        raise AssertionError("hair yaw keys incomplete")
    if any(set(x)!={front+">"+back for front,back in OCCLUSION}
           for x in hair["depthOcclusion"].values()):
        raise AssertionError("hair depth mask pairs incomplete")
    matches=sum(len(x["accepted"]) for x in hair["strandPairCorrespondence"].values())
    if matches!=hair["candidateStrokeMatches"] or matches!=browser["acceptedStrokeMatches"]:
        raise AssertionError("cross-view hair matches differ from browser")
    for role in ROLE_SET:
        for name,pair in hair["strandPairCorrespondence"].items():
            if not name.endswith("/"+role):
                continue
            seen=set()
            for part in pair["accepted"]:
                if part["targetId"] in seen:raise AssertionError("duplicate stroke target")
                seen.add(part["targetId"])
    if browser["status"]!="PASS_SOURCE_HASH_CHROMIUM" or browser["screenshotCount"]!=4:
        raise AssertionError("browser review incomplete")
    if browser["javascriptErrors"] or browser["failedRequests"]:
        raise AssertionError("chromium error")
    if browser["verifiedSourceImages"]!=16:
        raise AssertionError("browser input hash coverage incomplete")
    for frame in browser["reviews"]:
        path=(EXP/frame["path"]).resolve()
        if not path.is_relative_to(PRIVATE) or sha(path)!=frame["sha256"]:
            raise AssertionError("browser screenshot hash changed")
    original=hair["sourceMetadataSHA256"]
    expected={
        "P5ArtMesh":"p5-see-through/mv-candidate/parts.json",
        "P5Landmarks":"p5-see-through/mv-candidate/landmark-qa.json",
        "P9Palette":"p9-region-correspondence/qa.json",
        "P10StrokeBaseline":"p10-stroke-identity/qa.json",
    }
    for name,p in expected.items():
        if sha(PRIVATE/p)!=original[name]:raise AssertionError("original P0 provenance changed")
    public={
        "schema":"KOMA-P0-P15-05-HAIR-OCCLUSION-ACCEPTANCE-V1",
        "characterId":"p0_character_001",
        "status":"PASS_HAIR_SOURCE_STRAND_AND_DEPTH_ENGINEERING",
        "sourceRegisteredLayers":len(source),
        "sourceSHA256UniqueCount":hair["sourceSHA256UniqueCount"],
        "hairSemanticRoles":list(ROLE_SET),
        "viewAngles":list(KEYS),
        "strandViewPairs":hair["semanticStrokeViewPairs"],
        "candidateStrokeMatches":matches,
        "occlusionPairChecks":hair["occlusionPairCount"],
        "generatedKeyviewOcclusion":[hair["depthOcclusion"][str(y)] for y in (67.5,72.5)],
        "browserScreenshots":browser["screenshotCount"],
        "browserSourceImagesHashVerified":browser["verifiedSourceImages"],
        "sourceQA_SHA256":sha(hairfile),
        "sourceBrowserSHA256":sha(browserfile),
        "sourcePhysicalAnchor":"P5_ORIGINAL_45_90_PROJECTED_REFERENCE",
        "nativeRGBA":[1024,1024],
        "adoptedRenderer":"P8_SEMANTIC_OCCLUSION_ARTMESH",
        "artisticAcceptance":"PENDING_INDEPENDENT_STRAND_AND_MASK_REVIEW",
        "nextVisualPriority":["hair.back","hair.front","hair.side","hair.ahoge"],
    }
    output=EXP/"evidence/p15-05-acceptance.json"
    output.write_text(json.dumps(public,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"status":public["status"],
        "layers":public["sourceRegisteredLayers"],
        "matchedStrokes":public["candidateStrokeMatches"],
        "occlusionQA":public["occlusionPairChecks"],
        "browserCaptures":public["browserScreenshots"]},ensure_ascii=False))
    return public


if __name__=="__main__":
    verify()
