#!/usr/bin/env python3
"""Generate source-linked P0 55-degree pose candidates with Qwen Image Edit 2511.

Each generated image is an independent artwork candidate; no identity or
anatomical acceptance is inferred from successful inference.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from io import BytesIO
from pathlib import Path
from PIL import Image
from gradio_client import Client

BASE=Path(__file__).resolve().parent.parent
ASSETS=BASE/"private-assets"
SPACE="akhaliq/Qwen-Image-Edit-2511-LoRAs-Fast"
SOURCE=ASSETS/"p15-08-yaw055/input-yaw045.jpg"
VARS={
  "v3":("Fal-Multiple-Angles",55103),
  "v4":("Multiple-Angles",55104),
}
PROMPT=(
 "Use the provided image as the ONLY character identity reference. "
 "Make a SUBTLE head turn toward the RIGHT EDGE of the image, about 8-12 "
 "degrees more rotated than the supplied image, NOT a 90 degree profile. "
 "This is a gentle anime 3/4 angle between the input pose and a profile. "
 "Both purple-pink eyes MUST still be visible, with the far eye noticeably "
 "narrower and partly occluded by the nasal bridge and bangs; the near eye "
 "must be fully visible. Preserve the nose, lips, cheek and chin anatomy. "
 "Retain the SAME side-parted neck-length mauve pink bob hairstyle and "
 "EXACTLY ONE upward ahoge. Preserve the gold crossed X hairclip on the "
 "RIGHT SIDE of the canvas in the bangs near the upper right forehead; "
 "NEVER mirror this ornament to the left of the picture. Preserve the "
 "same school uniform, white collar, gold-trim navy jacket and burgundy "
 "bow with unchanged shoulder pose, same torso proportions and camera scale. "
 "Maintain the 2D Japanese TV anime painted style, fine clean linework, "
 "natural uninterrupted face and hair topology. Plain WHITE background; "
 "no text, no additional ornaments, no alternate character. "
 "Keep the far eye visible, do not turn the subject fully sideways."
)

def sha(data: bytes)->str:return hashlib.sha256(data).hexdigest()

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--version",choices=VARS,required=True)
 a=p.parse_args()
 adapter,seed=VARS[a.version]
 input_bytes=SOURCE.read_bytes()
 body=json.dumps(["data:image/jpeg;base64,"+base64.b64encode(input_bytes).decode()])
 print(json.dumps({"event":"start","version":a.version,"adapter":adapter,
                    "seed":seed,"inputSha256":sha(input_bytes)}),flush=True)
 client=Client(SPACE,verbose=False)
 result=client.predict(body,PROMPT,adapter,seed,False,1.0,4,api_name="/edit_image")
 if isinstance(result,(tuple,list)):result=result[0]
 if not isinstance(result,dict) or "image" not in result:
  raise ValueError("Space returned an unexpected image payload")
 content=result["image"]
 if "base64," not in content:raise ValueError("Expected base64 image payload")
 data=base64.b64decode(content.split("base64,",1)[1],validate=True)
 with Image.open(BytesIO(data)) as image:
  if image.size!=(1024,1024):raise ValueError("Generated image dimensions differ")
  image=image.convert("RGB")
  dest=ASSETS/f"p15-08-yaw055/yaw055-qwen2511-{a.version}.png"
  image.save(dest)
 raw=dest.read_bytes()
 provenance={"schema":"KOMA-P0-P15-09-ARTWORK-SOURCE-V1",
  "characterId":"p0_character_001","angleNominal":55,"source":"P0 original45",
  "sourceInputPath":str(SOURCE.relative_to(ASSETS)),
  "sourceInputSha256":sha(input_bytes),"model":"Qwen-Image-Edit-2511",
  "space":SPACE,"adapter":adapter,"seed":seed,"steps":4,"guidanceScale":1.0,
  "prompt":PROMPT,"outputPath":str(dest.relative_to(ASSETS)),
  "outputSha256":sha(raw),"bytes":len(raw),"mode":"RGB","canvas":[1024,1024],
  "status":"GENERATED_CANDIDATE_REQUIRES_POSE_REVIEW"}
 dest.with_suffix(".provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
 print(json.dumps({"event":"complete","version":a.version,"sha256":sha(raw),
                   "output":str(dest),"bytes":len(raw)}),flush=True)

if __name__=="__main__":main()
