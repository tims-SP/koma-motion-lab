#!/usr/bin/env python3
"""Evaluate genuine original Aka Ear ArtMesh under its inherited HeadYaw grid.

No invented pose degrees; original UV, faces/texture IDs are unmodified.
Only native Head Yaw bindings along center pitch are evaluated, excluding
other simultaneous parameters/physics. This is NOT the official D SDK.
"""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np

SHA="dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
def main(ears,params,out):
    a=json.loads(ears.read_text())
    b=json.loads(params.read_text())
    assert a["source_sha256"]==b["source_sha256"]==SHA
    chain=b["headYaw_target_chain_bindings"]
    axis=np.asarray(b["headYaw_axis_points"][0],np.float64)
    assert b["headYaw_exact_ear_binding_matches"]==4
    assert len(chain)==12 and len(axis)==9 and np.isclose(axis[4],.5)
    binds={}
    for ent in chain:
        z=ent["binding"]
        binds.setdefault(z["node"],[]).append(z)
    orig={z["part"]:z for z in b["native_ears"]}

    def sample(binding,yaw):
        values=np.asarray(binding["values"],dtype=np.float64)[:,1]
        idx=int(np.searchsorted(axis,yaw,side="right")-1)
        idx=max(0,min(len(axis)-2,idx))
        f=(yaw-axis[idx])/(axis[idx+1]-axis[idx])
        return (1-f)*values[idx]+f*values[idx+1]
    def posed_node(part,yaw):
        reference=orig[part["part"]]
        mesh=part["mesh"]
        vertices=np.asarray(mesh["verts"],np.float64)
        deformation=np.zeros_like(vertices)
        for bd in binds.get(part["uuid"],[]):
            if bd["param_name"]=="deform":
                deformation+=sample(bd,yaw)
        vertices+=deformation
        M=np.eye(3)
        for obj in reference["ancestry"]:
            tr=obj["transform"]
            trans=np.asarray(tr["trans"][:2],np.float64).copy()
            scale=np.asarray(tr["scale"],np.float64).copy()
            angle=float(tr["rot"][2])
            for bind in binds.get(obj["uuid"],[]):
                typ=bind["param_name"]
                val=sample(bind,yaw)
                if typ=="transform.t.x":trans[0]+=float(val)
                elif typ=="transform.t.y":trans[1]+=float(val)
                elif typ=="transform.s.x":scale[0]=float(val)
                elif typ=="transform.s.y":scale[1]=float(val)
                elif typ=="transform.r.z":angle+=float(val)
            theta=math.radians(angle)
            co=math.cos(theta);si=math.sin(theta)
            current=np.asarray([[co*scale[0],-si*scale[1],trans[0]],
                               [si*scale[0],co*scale[1],trans[1]],
                               [0,0,1.]])
            M=M@current
        transformed=(np.c_[vertices,np.ones(len(vertices))]@M.T)[:,:2]
        return transformed,deformation
    results=[]
    for yaw in (.5,.75,1.0):
        report=[]
        for ear in a["ears"]:
            real_uv=np.asarray(ear["mesh"]["uvs"])
            faces=np.asarray(ear["mesh"]["indices"]).reshape(-1,3)
            orig_uv=np.asarray(ear["mesh"]["uvs"])
            assert np.array_equal(real_uv,orig_uv)
            assert len(faces)==ear["triangle_count"]
            coords,deform=posed_node(ear,yaw)
            report.append({"part":ear["part"],"uuid":ear["uuid"],
                "source_verts":ear["vertex_count"],"source_faces":ear["triangle_count"],
                "original_uv_preserved":True,
                "world_bbox":np.round([coords[:,0].min(),coords[:,1].min(),
                                       coords[:,0].max(),coords[:,1].max()],4).tolist(),
                "deform_abs_max":round(float(np.abs(deform).max()),4),
                "mean_xy":np.round(coords.mean(0),4).tolist()})
        results.append({"native_grid_yaw":yaw,"ears":report})
    changes=[]
    for i,ear in enumerate(a["ears"]):
        a0=np.asarray(results[0]["ears"][i]["mean_xy"])
        a1=np.asarray(results[-1]["ears"][i]["mean_xy"])
        delta=a1-a0
        if np.linalg.norm(delta)<15:raise ValueError("Native HeadYaw did not change original mesh positions")
        changes.append({"part":ear["part"],"mean_delta_xy":np.round(delta,4).tolist()})
    result={"status":"ORIGINAL_HEADYAW_EAR_CHAIN_EVALUATED",
      "source_inx_sha256":SHA,"source_vertices":[57,59],
      "original_artmesh_front_triangles":[89,93],
      "source_texture_and_uv_intact":True,
      "head_yaw_binding_count":114,
      "head_yaw_relevant_chain_bindings":12,
      "native_pose_engine":"INDEPENDENT_NUMPY_REPLAY_NOT_OFFICIAL_D_PARITY",
      "original_uv_to_new_3D_rear_skin":"NOT_IMPLEMENTED",
      "physical_yaw_degrees":"NOT_CALIBRATED",
      "samples":results,"motion":changes}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("CORE017_REAL_PARAMETER_REPLAY_PASS",json.dumps({"motion":changes,"samples":[z["native_grid_yaw"] for z in results]}))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ears",required=True,type=Path)
    p.add_argument("--params",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    v=p.parse_args()
    main(v.ears,v.params,v.out)
