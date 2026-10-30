#!/usr/bin/env python3
"""CORE-011 fail-closed single-view input preflight.

Passing automated dimensions never counts as character consistency,
actual source edit provenance, real texture/INX UV, or angle accuracy.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
def evaluate(path,target,min_edge=768):
    if target not in (90,180): raise ValueError("Only +90 and 180 candidate gates")
    path=Path(path)
    im=Image.open(path)
    checks={
      "single_image_aspect_ratio_plausible": .72 <= im.width/im.height <= 1.28,
      "minimum_native_resolution":min(im.size)>=min_edge,
      "valid_rgb_or_rgba":im.mode in ("RGB","RGBA")
    }
    return {
      "candidate":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "width":im.width,"height":im.height,"mode":im.mode,"target_nominal_degrees":target,
      "automatic_checks":checks,
      "status":"PENDING_VISUAL_IDENTITY_REVIEW" if all(checks.values()) else "REJECTED_AUTOMATIC_LAYOUT_OR_SIZE",
      "identity_from_real_Aka_PSD_verified":False,
      "native_INX_uv_registered":False,"reconstructed_hidden_art":False,
      "360_quality_acceptance":False,
      "additional_hard_gates":[
       "actual_original_Aka_reference_edit_input_attached_and_proven",
       "visual_no_extra_braids_bows_bells_costume_changes",
       "physical_profile_and_facial_occlusion",
       "180_view_no_eyes_nose_mouth_or_front_leaf",
       "per_part_visible_and_hidden_alpha_art",
       "per_part_new_view_uv_registered_to_native_INX",
       "decoded_360_video_direct_visual_inspection"
      ]}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",type=Path,required=True)
    p.add_argument("--yaw",type=int,choices=(90,180),required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    d=evaluate(a.candidate,a.yaw)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
    print("CORE011_FAILCLOSED",json.dumps(d))
    if d["status"].startswith("REJECTED"):raise SystemExit(2)
