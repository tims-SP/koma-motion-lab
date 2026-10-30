#!/usr/bin/env python3
"""Inventory actual full Aka model, fail closed for invalid LFS pointer.

This audits only parameters/keyframe shapes, does NOT execute the INX runtime.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
EXPECTED="dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
def main(path,out):
    info={"source":"Inochi2D/example-models/Aka.inx",
      "source_commit":"cd95dd00ddff63b1f7d2b84a19914c3c70d05945",
      "expected_lfs_sha256":EXPECTED,
      "verified_full_model":False,"parameters":[],"native_runtime_replay":"NOT_EXECUTED"}
    if not path.is_file():
        info["status"]="NOT_FETCHED"
    else:
        data=path.read_bytes()
        info["actual_bytes"]=len(data)
        info["actual_sha256"]=hashlib.sha256(data).hexdigest()
        if data.startswith(b"version https://git-lfs.github.com/spec"):
            info["status"]="LFS_POINTER_NOT_ACTUAL_MODEL"
        elif info["actual_sha256"]!=EXPECTED:
            info["status"]="HASH_MISMATCH_UNTRUSTED"
        elif data[:8]!=b"TRNSRTS\x00":
            info["status"]="FORMAT_UNSUPPORTED"
        else:
            n=struct.unpack(">I",data[8:12])[0]
            if n<100 or n>len(data)-12:raise ValueError("Malformed INX JSON header")
            model=json.loads(data[12:12+n])
            params=model.get("param",[])
            if isinstance(params,dict): params=list(params.values())
            def summary(p,i):
                return {"index":i,
                  "name":p.get("name"),"uuid":p.get("uuid"),
                  "axis":p.get("axisPoints"),
                  "keys":sorted(p.keys()),
                  "shape":{"is_vec2":p.get("is_vec2"),"min":p.get("min"),"max":p.get("max")},
                  "bindings":len(p.get("bindings",[])) if isinstance(p.get("bindings"),list) else None}
            info["parameters"]=[summary(p,i) for i,p in enumerate(params) if isinstance(p,dict)]
            info["parameter_count"]=len(info["parameters"])
            info["root_keys"]=list(model.keys())
            info["verified_full_model"]=True
            info["status"]="FULL_INX_BINARY_HASH_VERIFIED_PARAMETERS_PARSED"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n")
    print("CORE008_AKA_NATIVE_PARAMETER_INVENTORY",json.dumps(info,ensure_ascii=False)[:13000])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    x=p.parse_args()
    main(x.input,x.output)
