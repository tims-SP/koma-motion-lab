#!/usr/bin/env python3
"""Read a *real* Reverse1999 .skel, recover its Spine JSON, summarize importability.
Copyrighted source/JSON never leaves the ephemeral GitHub runner.
"""
from __future__ import annotations
import hashlib,json,os,re,subprocess,sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from production_reverse1999 import download, PRIVATE

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"out"/"spine-rive-production"
EVIDENCE.mkdir(parents=True,exist_ok=True)
SOURCE="roles/300401_hongnujian"
MODELS=["300401_hongnujian_room.skel","300401_hongnujian_fight.skel","300401_hongnujian_ui.skel"]
exe=Path(os.environ.get("SPINE_CONVERTER","")).resolve()
report={"source":"myssal/Reverse-1999-CN-Asset",
        "source_commit":"45e75248ba3b25053fd32e63ab13c2f9f54dd9df",
        "format_probe":{},"conversion":{},"errors":[]}

for name in MODELS:
    try:
        skel=download(SOURCE+"/"+name)
        binary=skel.read_bytes()
        snippet=binary[:180]
        versions=[m.group().decode("ascii","replace") for m in re.finditer(rb"(?:3\.[5678]|4\.[0123])\.\d{1,3}",snippet)]
        report["format_probe"][name]={"file_bytes":len(binary),"version_strings":versions,
               "sha256":hashlib.sha256(binary).hexdigest(),
               "git_lfs_pointer":binary.startswith(b"version https://git-lfs.github.com/spec")}
        dest=PRIVATE/"conversion"/(name+".json")
        dest.parent.mkdir(parents=True,exist_ok=True)
        r=subprocess.run([str(exe),str(skel),str(dest)],capture_output=True,text=True,timeout=120)
        details={"converter_exit_code":r.returncode,
                 "converter_tail":(r.stdout+"\n"+r.stderr)[-1200:]}
        if r.returncode==0 and dest.exists():
            data=json.loads(dest.read_text("utf-8"))
            details["json_bytes"]=dest.stat().st_size
            for key in ("bones","slots","skins","animations","ik","transform","path","events"):
                v=data.get(key,{})
                details[key+"_count"]=len(v) if isinstance(v,(list,dict)) else None
            details["version"]=data.get("skeleton",{}).get("spine")
            details["animation_names"]=list(data.get("animations",{}))[:30]
            details["bone_sample"]=[{k:b.get(k) for k in ("name","parent","x","y","rotation","length") if k in b}
                                    for b in data.get("bones",[])[:12]]
            details["skin_top_type"]=type(data.get("skins")).__name__
        report["conversion"][name]=details
    except Exception as e:
        report["errors"].append(name+": "+repr(e))
(EVIDENCE/"conversion-scout.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(report,indent=2,ensure_ascii=False))
# A reader failing for one format should not block investigation of others.
sys.exit(0 if any(x.get("json_bytes") for x in report["conversion"].values()) else 1)
