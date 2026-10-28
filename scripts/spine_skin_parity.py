#!/usr/bin/env python3
"""PROD-007: numerical parity of Rive native Skin and source-weighted bake.

Both frame sets are derived from the same source images and source Spine 4.2.36
rotation timeline. Game art never leaves the private runner; only aggregate
quality metrics are emitted.
"""
from __future__ import annotations
import json,os,statistics,sys
from pathlib import Path
from PIL import Image
ROOT=Path(os.environ.get("PROD_PRIVATE","/tmp/koma-spine-rive-private"))
OUT=Path(os.environ.get("PROD_REPORT","out/spine-rive"))
REPORT={"comparison":"Rive native live Skin/Tendon vs Spine-weight-baked Rive Mesh",
        "source":"Reverse 1999 / 300401_hongnujian room.skel / idle_room",
        "samples":[],
        "caveats":["Neither branch independently matches the Spine runtime",
            "Only sampled rotate tracks are included; IK/path/FFD/attachment switches not yet matched",
            "Rive bone offset bridges and source bone inherit transforms may differ",
            "Game art and actual diff images remain private in Actions runner"],
        "source_art_uploaded":False}
def compare(a,b):
    with Image.open(a) as A, Image.open(b) as B:
        A=A.convert("RGBA"); B=B.convert("RGBA")
        if A.size!=B.size:raise ValueError("frame size mismatch")
        r1=A.tobytes();r2=B.tobytes()
    background1=r1[:4];background2=r2[:4]
    common=union=present1=present2=diff_count=0
    mad=0
    for p in range(0,len(r1),4):
        f1=r1[p:p+4]!=background1
        f2=r2[p:p+4]!=background2
        if f1:present1+=1
        if f2:present2+=1
        if f1 and f2:common+=1
        if f1 or f2:
            union+=1
            if any(abs(x-y)>8 for x,y in zip(r1[p:p+4],r2[p:p+4])):diff_count+=1
            mad+=sum(abs(x-y) for x,y in zip(r1[p:p+4],r2[p:p+4]))
    return {"source_native_visible":present1,"baked_visible":present2,
            "mask_iou":round(common/union,5) if union else 0.,
            "foreground_changed_fraction":round(diff_count/union,5) if union else 0.,
            "rgba_mae_foreground":round(mad/(4*union),3) if union else 0.}
def main():
    a=ROOT/"textured-original-frames"
    b=ROOT/"source-weight-baked-frames"
    if not a.exists() or not b.exists():raise RuntimeError("Both frame sets required")
    for n in (0,3,6,9,12,15,18,21,23):
        p1=a/f"{n:04d}.png";p2=b/f"{n:04d}.png"
        if not p1.exists() or not p2.exists():raise RuntimeError("Missing frame "+str(n))
        REPORT["samples"].append({"frame":n,**compare(p1,p2)})
    REPORT["min_mask_iou"]=min(x["mask_iou"] for x in REPORT["samples"])
    REPORT["median_mask_iou"]=statistics.median(x["mask_iou"] for x in REPORT["samples"])
    REPORT["median_pixel_difference"]=statistics.median(x["foreground_changed_fraction"] for x in REPORT["samples"])
    # A green build is not proof that the animation is production-ready.
    # Conservative internal reference thresholds; true Spine-runtime parity
    # needs a separate independent source-runtime render.
    REPORT["internal_reference_threshold"]={"median_mask_iou_min":0.75,
        "median_changed_foreground_max":0.25}
    REPORT["production_fidelity_gate"]=(
        "PASS_INTERNAL_REFERENCE_ONLY" if
        REPORT["median_mask_iou"]>=0.75 and REPORT["median_pixel_difference"]<=0.25
        else "FAIL_LOW_PARITY")
    REPORT["source_runtime_parity"]="NOT_TESTED"
    REPORT["status"]="MEASURED"
def finish():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"skin-vs-bake-parity.json").write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+"\n")
    lines=["# PROD-007 — Rive native-vs-baked animation comparison","",
        "Status: "+REPORT.get("status","FAIL"),"",
        "| Frame | Native pixels | Baked pixels | Mask IoU | Foreground pixel difference |",
        "|---:|---:|---:|---:|---:|"]
    for x in REPORT["samples"]:
        lines.append(f"| {x['frame']} | {x['source_native_visible']} | {x['baked_visible']} | {x['mask_iou']:.3f} | {x['foreground_changed_fraction']:.3f} |")
    lines+=["",f"Production fidelity gate: **{REPORT.get('production_fidelity_gate','N/A')}**",f"Median mask IoU: {REPORT.get('median_mask_iou','N/A')}",
            f"Median changed foreground fraction: {REPORT.get('median_pixel_difference','N/A')}",
            "","Source-runtime frame parity is still NOT established.",
            "Original source/derived game artwork remains in temporary runner storage only.",
            "","Error: "+str(REPORT.get("error","none"))]
    (OUT/"skin-vs-bake-parity.md").write_text("\n".join(lines)+"\n")
    print((OUT/"skin-vs-bake-parity.md").read_text(),flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:REPORT["status"]="ERROR";REPORT["error"]=repr(exc)
    finish()
    if REPORT.get("status")!="MEASURED":sys.exit(1)
