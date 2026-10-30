#!/usr/bin/env python3
"""Inspect genuine Aka Head:: Yaw-Pitch parameter binding grids.

Only structural excerpts, not a native renderer nor a claim of 3D yaw=45°.
"""
import argparse,hashlib,json,struct
from pathlib import Path
SHA="dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
def inspect_shape(v,depth=0):
    if depth>4:return {"kind":"omitted_deep"}
    if isinstance(v,list):
        return {"kind":"list","length":len(v),
                "first":inspect_shape(v[0],depth+1) if v else None}
    if isinstance(v,dict):
        return {k:inspect_shape(x,depth+1) for k,x in list(v.items())[:16]}
    return v if isinstance(v,(str,int,float,bool,type(None))) else str(type(v))
def main(p,out):
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError("Actual full Aka INX mismatch")
    if data[:8]!=b"TRNSRTS\x00":raise ValueError("Invalid INX format")
    n=struct.unpack(">I",data[8:12])[0]
    model=json.loads(data[12:12+n])
    params=model.get("param",[])
    yaw=[x for x in params if isinstance(x,dict) and "Yaw-Pitch" in str(x.get("name","")) and "Head" in str(x.get("name",""))]
    if len(yaw)!=1:raise ValueError("Expected ONE native Head:: Yaw-Pitch parameter")
    p0=yaw[0];bindings=p0["bindings"]
    if len(bindings)<40:raise ValueError("Missing native head deformation bindings")
    counts={}
    for b in bindings:
        key=str(b.get("type",b.get("interpolation",b.get("target",b.get("node",None)))))
        counts[key]=counts.get(key,0)+1
    report={
     "status":"REAL_NATIVE_HEAD_YAW_BINDING_GRID_INSPECTED",
     "original_license":"Aka by seagetch CC BY 4.0",
     "source":"Inochi2D/example-models/Aka.inx (full binary, verified SHA256)",
     "param_name":p0.get("name"),"uuid":p0.get("uuid"),
     "axis_points":p0.get("axis_points"),
     "min":p0.get("min"),"max":p0.get("max"),"is_vec2":p0.get("is_vec2"),
     "binding_count":len(bindings),"binding_kinds":counts,
     "sample_binding_shapes":[inspect_shape(x) for x in bindings[:6]],
     "native_pose_evaluation":"NOT_IMPLEMENTED",
     "semantic_yaw_degrees_from_parameter":"UNKNOWN_UNTIL_RENDERER_CALIBRATION",
     "verified_source_3d_surface":"NO_SOURCE_IS_2D_DEFORMABLE_MESH",
     "source_mesh_bindings_are_real":True
    }
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("CORE008_REAL_HEAD_PARAMETER",json.dumps(report,ensure_ascii=False)[:13500])
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args();main(a.input,a.output)
