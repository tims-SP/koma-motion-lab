#!/usr/bin/env python3
"""CORE017: read source Aka transform ancestry + authentic HeadYaw binding structure.

No inferred transforms, pose degrees or new UV. Full native source SHA locked.
"""
import argparse,json,struct,hashlib
from pathlib import Path
SHA="dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
EAR_NAMES=("Ear:: Left","Ear:: Right")
def shape(x,depth=0):
    if depth>3:return "..."
    if isinstance(x,dict):
        return {str(k):shape(v,depth+1) for k,v in list(x.items())[:18]}
    if isinstance(x,list):
        if len(x)>16:return {"length":len(x),"first":shape(x[0],depth+1),"last":shape(x[-1],depth+1)}
        return [shape(y,depth+1) for y in x]
    return x
def main(inp,out):
    b=inp.read_bytes()
    assert hashlib.sha256(b).hexdigest()==SHA
    assert b[:8]==b"TRNSRTS\x00"
    n=struct.unpack(">I",b[8:12])[0];data=json.loads(b[12:12+n])
    ordered=[];ear_records=[]
    def walk(node,parents):
        tr=node.get("transform",{})
        rec={"name":node.get("name"),"uuid":node.get("uuid"),
             "node_type":node.get("type"),
             "transform":tr,"lock_to_root":node.get("lockToRoot"),
             "zsort":node.get("zsort"),"ancestors":[x["name"] for x in parents],
             "mesh_origin":(node.get("mesh") or {}).get("origin")}
        ordered.append(rec)
        if node.get("name") in EAR_NAMES:
            ear_records.append({"part":node["name"],"uuid":node["uuid"],
               "ancestry":[{k:r[k] for k in ("name","uuid","transform","node_type","zsort","lock_to_root")} for r in parents]+[
                   {k:rec[k] for k in ("name","uuid","transform","node_type","zsort","lock_to_root")}],
               "mesh_origin":rec["mesh_origin"],
               "mesh_vertex_sample":(node.get("mesh") or {}).get("verts",[])[:8]})
        for x in node.get("children",[]) or []:walk(x,parents+[rec])
    walk(data["nodes"],[])
    assert len(ear_records)==2
    params=data.get("param",[])
    param=next(x for x in params if x.get("name")=="Head:: Yaw-Pitch")
    bindings=param["bindings"]
    wanted={a["uuid"] for r in ear_records for a in r["ancestry"]}
    native_bindings=[]
    for i,bind in enumerate(bindings):
        nodeid=bind.get("node")
        if isinstance(nodeid,dict):nodeid=nodeid.get("uuid")
        if bind.get("node") in wanted or bind.get("target") in wanted or bind.get("uuid") in wanted or bind.get("id") in wanted or bind.get("nodeId") in wanted:
            native_bindings.append({"index":i,"binding":bind})
    result={"schema":"core017-native-ear-ancestry-bindings/1","source_sha256":SHA,
      "real_INX_node_data":True,"source_parameters":len(params),"headYaw_name":param["name"],
      "headYaw_axis_points":param.get("axis_points"),"headYaw_keys":list(param),
      "headYaw_binding_count":len(bindings),"headYaw_binding_samples":[shape(x) for x in bindings[:5]],
      "headYaw_target_chain_binding_count":len(native_bindings),
      "headYaw_exact_ear_binding_matches":sum(b["binding"].get("node") in {r["uuid"] for r in ear_records} for b in native_bindings),
      "headYaw_target_chain_bindings":native_bindings,"native_ears":ear_records,
      "node_samples":[{k:x[k] for k in ("name","uuid","node_type","transform")} for x in ordered[:10]],
      "all_parts_node_count":len(ordered),
      "validated_original_INX_pose_engine":"NO_PIXEL_PARITY_YET"}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    compact={k:v for k,v in result.items() if k not in ("headYaw_target_chain_bindings","headYaw_binding_samples","node_samples")}
    compact["headYaw_binding_samples"]=result["headYaw_binding_samples"][:2]
    print("CORE017_NATIVE_POSE_ANCESTRY",json.dumps(compact,ensure_ascii=False)[:28000])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();main(a.input,a.out)
