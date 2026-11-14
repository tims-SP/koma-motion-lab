#!/usr/bin/env python3
"""Generate a traceable P0 yaw55 original-painting candidate via a HF Space."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from io import BytesIO
from pathlib import Path

from gradio_client import Client
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/"private-assets"
SPACE="akhaliq/Qwen-Image-Edit-2511-LoRAs-Fast"
ADAPTER="Multiple-Angles"
SEED=55022
OUT=PRIVATE/"p15-08-yaw055"
OUT.mkdir(parents=True,exist_ok=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jpeg_data_url(path):
    with Image.open(path) as im:
        if im.size != (1024, 1024) or im.mode != "RGB":
            raise ValueError("Generation reference JPEG must be registered 1024 RGB")
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def main():
    contract=json.loads((ROOT/"metadata/p15-08-yaw055-generation-contract.json").read_text())
    if contract["characterId"]!="p0_character_001" or contract["yawDeg"]!=55.0:
        raise ValueError("Registered contract mismatch")
    src=contract["references"]
    ref45=next(item for item in src if item["yawDeg"]==45.)
    ref65=next(item for item in src if item["yawDeg"]==65.)
    for r in (ref45,ref65):
        if digest(PRIVATE/r["path"])!=r["sha256"]:
            raise ValueError(f"Original P0 view source SHA differs at {r['yawDeg']}")
    jpg45=OUT/"input-yaw045.jpg"
    jpg65=OUT/"input-yaw065.jpg"
    if digest(jpg45)!="1b5953ef9a22eb0e4356b677883143d073e03bd3c980eb8543a640353ad0b941":
        raise ValueError("P0 original 45-degree inference input SHA changed")
    if digest(jpg65)!="390ba6e25d8afff96201c3e881b4c389db78be4423b80ac97b707f082fda9333":
        raise ValueError("P15 generated 65-degree inference input SHA changed")
    image_data=json.dumps([jpeg_data_url(jpg45),jpeg_data_url(jpg65)])
    prompt=(
        "Image 1 is the original Japanese 2D anime girl at registered yaw45. "
        "Image 2 is the same anime girl at registered yaw65. "
        "Create one newly painted in-between keyframe EXACTLY yaw55 toward the right-facing profile: "
        "the HEAD GEOMETRY is halfway between those two registered source poses, "
        "with natural 3D rotation, a near open violet-pink eye and a thin partially occluded far eye, "
        "coherent nose bridge and chin contour, proper near ear root and natural fringe occlusion. "
        "Keep the exact same original character identity: mauve-pink neck-length bob with a single ahoge, "
        "the gold crossed clip on the character physical left when naturally visible, "
        "navy school jacket with gold trim, white collar and burgundy bow. "
        "Single clean TV anime cel-shaded drawing, stable camera, same pixel center and 1024 square framing, "
        "no split panels, no text, no other subjects, no distorted skin or duplicate strokes."
    )
    if (OUT/"yaw055-qwen2511-v1.png").exists():
        raise FileExistsError("A SHA-registered P0 yaw055 source candidate exists; retain it as immutable provenance")
    client=Client(SPACE,token=os.getenv("HF_TOKEN"),verbose=False)
    print(json.dumps({"status":"SPACE_READY","space":SPACE,"seed":SEED,"inputCount":2}),flush=True)
    result=client.predict(
        images_b64_json=image_data,prompt=prompt,lora_adapter=ADAPTER,
        seed=SEED,randomize_seed=False,guidance_scale=1.0,steps=4,
        api_name="/edit_image",
    )
    if not isinstance(result,dict) or not isinstance(result.get("image"),str):
        raise RuntimeError("Space inference response did not contain a source PNG")
    encoded=result["image"].split(",",1)[-1]
    raw=base64.b64decode(encoded)
    pic=Image.open(BytesIO(raw)).convert("RGB")
    if pic.size!=(1024,1024):
        raise ValueError(f"Model output is not registered 1024 square: {pic.size}")
    output=OUT/"yaw055-qwen2511-v1.png"
    pic.save(output,format="PNG")
    evidence={
        "schema":"KOMA-P15-08-YAW055-PAINTING-SOURCE-V1",
        "characterId":"p0_character_001",
        "targetYaw":55.0,
        "model":"Qwen-Image-Edit-2511",
        "space":SPACE,
        "adapter":ADAPTER,
        "seed":result.get("seed",SEED),
        "sourceFrames":[{"yawDeg":r["yawDeg"],"path":r["path"],
                         "sha256":r["sha256"]} for r in (ref45,ref65)],
        "prompt":prompt,
        "originalPainting":{"path":str(output.relative_to(PRIVATE)),
                            "sha256":digest(output),"mode":"RGB",
                            "size":list(pic.size)},
        "status":"P15_08_CANDIDATE_READY_FOR_POSE_AND_IDENTITY_REVIEW",
        "semanticLayerAcceptance":"PENDING_DIRECT_13_PART_PAINTING",
        "heroSourceVerified":False,
    }
    (OUT/"source-qa.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":evidence["status"],
                      "path":evidence["originalPainting"]["path"],
                      "sha256":evidence["originalPainting"]["sha256"],
                      "sourceSeed":evidence["seed"]}),flush=True)
    return evidence


if __name__=="__main__":
    main()
