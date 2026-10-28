#!/usr/bin/env python3
"""Spine binary -> Spine JSON: real upstream source, metadata-only report.

All original / converted copyrighted data stays in the ephemeral GitHub runner.
Do not publish source textures, skeletons, converted JSON, images or game-derived
video in public repo Actions artifacts.
"""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,urllib.request,urllib.parse
from pathlib import Path

UPSTREAM="myssal/Reverse-1999-CN-Asset"
COMMIT="45e75248ba3b25053fd32e63ab13c2f9f54dd9df"
CHAR="300401_hongnujian"
ROOT=Path(os.environ.get("PROD_PRIVATE","/tmp/koma-spine-rive-private"))
PUBLIC=Path(os.environ.get("PROD_REPORT","out/spine-rive"))
ROOT.mkdir(parents=True,exist_ok=True)
PUBLIC.mkdir(parents=True,exist_ok=True)
report={"source":UPSTREAM,"commit":COMMIT,"character":CHAR,
        "format":"Spine binary","conversion_status":"NOT_STARTED","features":{},
        "conversion_tools":[],"warning":"Upstream asset has no observed redistribution license; all copyrighted media remain runner-local."}

def persist():
    (PUBLIC/"conversion.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    lines=["# Spine to Rive conversion, real-game source","",
           f"Source: {UPSTREAM}@{COMMIT}; character {CHAR}","",
           f"**Conversion:** {report['conversion_status']}","",
           "| Feature | Count |","|---|---:|"]
    for k,v in report["features"].items():
        lines.append(f"| {k} | {v} |")
    lines+=["","## Conversion attempts",""]
    for x in report["conversion_tools"]:
        lines.append(f"- {x['name']}: exit {x['returncode']}; output {x['output_exists']}; detail {x['detail'][:120]}")
    lines+=["","Do not infer complete bone, mesh, weighting and animation fidelity from a parse alone."]
    (PUBLIC/"summary.md").write_text("\n".join(lines)+"\n")
    print((PUBLIC/"summary.md").read_text(),flush=True)

def download(path):
    url=f"https://raw.githubusercontent.com/{UPSTREAM}/{COMMIT}/{urllib.parse.quote(path,safe='/')}"
    data=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"koma-motion-lab-rig-converter"}),timeout=90).read(8_000_001)
    if len(data)>8_000_000:raise RuntimeError("Source too large")
    local=ROOT/Path(path).name
    local.write_bytes(data)
    return local

def feature_report(doc):
    bones=doc.get("bones",[])
    slots=doc.get("slots",[])
    skins=doc.get("skins",{})
    anims=doc.get("animations",{})
    if isinstance(skins,list):
        attachments=[a for skin in skins for slot in skin.get("attachments",{}).values() for a in slot.values() if isinstance(a,dict)]
    else:
        attachments=[a for skin in skins.values() for slot in skin.values() for a in slot.values() if isinstance(a,dict)]
    weighted=[a for a in attachments if isinstance(a.get("vertices"),list) and len(a["vertices"])>2*len(a.get("uvs",[]))//2]
    mesh=[a for a in attachments if a.get("type") in ("mesh","linkedmesh") or "uvs" in a]
    timelines=sum(len(v) for anim in anims.values() for v in (anim.get("bones",{}) or {}).values() if isinstance(v,dict))
    return {
      "source_version":doc.get("skeleton",{}).get("spine","unknown"),
      "bones":len(bones),"slots":len(slots),"skins":len(skins),
      "attachments":len(attachments),"mesh_attachments":len(mesh),
      "weighted_attachments_candidate":len(weighted),
      "ik_constraints":len(doc.get("ik",[])),
      "transform_constraints":len(doc.get("transform",[])),
      "path_constraints":len(doc.get("path",[])),
      "animations":len(anims),
      "bone_timeline_groups":timelines,
      "animation_names_sample":list(anims)[:16],
      "largest_bones_sample":[b["name"] for b in sorted(bones,key=lambda b:b.get("length",0),reverse=True)[:16]],
    }

def main():
    try:
        src=download(f"roles/{CHAR}/{CHAR}_room.skel")
        report["binary_size"]=src.stat().st_size
        report["binary_header_hex"]=src.read_bytes()[:32].hex()
        report["binary_sha256"]=hashlib.sha256(src.read_bytes()).hexdigest()
        print("Binary sample size",src.stat().st_size,"header",report["binary_header_hex"],flush=True)
        out=ROOT/"source_spine.json"
        converter=["skel_to_json",str(src),"-o",str(out),"--format","3.8"]
        r=subprocess.run(converter,capture_output=True,text=True,timeout=90)
        report["conversion_tools"].append({"name":"AyalaKaguya/skel_to_json",
          "returncode":r.returncode,"output_exists":out.exists(),
          "detail":(r.stdout+r.stderr)[-2200:]})
        if r.returncode!=0 or not out.exists() or out.stat().st_size<100:
            report["conversion_status"]="FAIL"
            persist()
            return 2
        doc=json.loads(out.read_text())
        report["features"]=feature_report(doc)
        report["conversion_status"]="PASS"
        report["json_sha256"]=hashlib.sha256(out.read_bytes()).hexdigest()
        persist()
        return 0
    except Exception as exc:
        report["conversion_status"]="FAIL_EXCEPTION"
        report["error"]=repr(exc)
        persist()
        return 3

if __name__=="__main__":sys.exit(main())
