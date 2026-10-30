#!/usr/bin/env python3
"""CORE-011 explicit real Aka original-image EDIT, not prompt-only generation.

The genuine official source PNG hash is required and is passed as an *actual*
input image file. --dry-run never invokes paid OpenAI services.
Even a successful image edit is PENDING_VISUAL_IDENTITY_REVIEW, not rigged.
"""
from pathlib import Path
import argparse,base64,hashlib,json,os
from PIL import Image
SHA="c22f2af3f426d4e79745e28a1244750d1c46b41d82f46570be63b9543aedb4e4"
MODEL="gpt-image-2.5-sunburst"
PROMPTS={
90:("Edit the ATTACHED ORIGINAL official Aka art into ONE 90-degree orthographic true RIGHT SIDE head profile. "
    "Nose pointing IMAGE RIGHT. Preserve precisely the amber-orange tall fox ears with white inner fur, short golden bob "
    "without braids or tie-backs, vivid red-magenta ONE visible near eye, tiny dark red leaf resting on original frontal bangs, "
    "and simple dark choker. Fixed head size, ear-tip height, original cel outlines and neutral expression. Only near eye shows; "
    "far eye must be occluded. Real side nose/cheek/jaw silhouette, appropriate back hair and ear overlaps. "
    "Produce ONE FULL-SIZE standalone 1024x1024 portrait on plain pale background. "
    "Absolutely NO contact sheet, grid, collage, labels, subtitles, technical diagram, UV render, extra outfits, "
    "bows, tassels, bells, hair braids, new ornaments, text, or secondary faces."),
180:("Edit the ATTACHED ORIGINAL official Aka art into ONE strict 180-degree orthographic BACK OF HEAD view, same head scale "
    "and ear-tip height. Real short orange-gold bob's crown, rear hair masses, backs of both huge amber fox ears, rear nape and "
    "simple dark choker/neck. NO eyes, mouth, nose, frontal facial skin or the burgundy leaf on the front bangs showing on rear. "
    "No braids, bows, bells, jewelry changes or extra hair ties. Keep original Japanese 2D ink/cel shading and character asymmetry. "
    "Produce ONE FULL-SIZE standalone 1024x1024 image on pale background. "
    "NO collage, multi-angle board, panels, diagrams, UV text, annotations, or decorative studio asset sheets.")
}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(a):
    src=Path(a.original)
    if not src.is_file():raise FileNotFoundError("Missing authoritative source original: "+str(src))
    actual=digest(src)
    if actual!=SHA:raise RuntimeError("CORE011_REF_SHA_REJECTED: expected genuine original "+SHA+" but got "+actual)
    with Image.open(src) as im:
        size=list(im.size)
        if min(size)<768:raise ValueError("Insufficient original source resolution")
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    doc={"schema":"koma011-explicit-source-edit/1","source_sha256":actual,
      "source_name":src.name,"source_dimensions":size,"source_author":"seagetch",
      "source_license":"CC BY 4.0","model":MODEL,"endpoint":"images.edit",
      "prompt":PROMPTS[a.yaw],"nominal_target_yaw":a.yaw,"size":"1024x1024",
      "quality":"high","explicit_attached_original_png":True,
      "newview_uv":False,"animation":False,"accepted_visual":False,
      "status":"DRY_RUN_REAL_ORIGINAL_REF_VERIFIED" if a.dry_run else "REQUEST_PENDING"}
    (out/"edit_request_manifest.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n")
    if a.dry_run:
        print("CORE011_GENUINE_SOURCE_IMAGE_INTEGRITY_PASS",actual,size)
        return
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not provided. No image edit request executed.")
    from openai import OpenAI
    with src.open("rb") as infile:
        rsp=OpenAI().images.edit(model=MODEL,image=infile,prompt=PROMPTS[a.yaw],
                                 size="1024x1024",quality="high",output_format="png")
    if not rsp.data or not rsp.data[0].b64_json:raise ValueError("Image edit response empty")
    target=out/("aka_yaw_%03d_generated_candidate.png"%a.yaw)
    target.write_bytes(base64.b64decode(rsp.data[0].b64_json))
    with Image.open(target) as im:
        dims=list(im.size)
        supported=min(dims)>=768 and .72<=dims[0]/dims[1]<=1.28
    doc.update({"status":"PENDING_DIRECT_IMAGE_VISUAL_REVIEW" if supported else "REJECTED_LAYOUT_OR_RESOLUTION",
                "output_sha256":digest(target),"output_dimensions":dims})
    (out/"edit_request_manifest.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n")
    if not supported:raise RuntimeError("Generated output format rejected, not production art")
    print("CORE011_GPT_EDIT_RETURNED_UNVERIFIED_ILLUSTRATION",target)
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",required=True)
    parser.add_argument("--yaw",type=int,required=True,choices=(90,180))
    parser.add_argument("--out",required=True)
    parser.add_argument("--dry-run",action="store_true")
    main(parser.parse_args())
