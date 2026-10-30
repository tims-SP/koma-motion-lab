#!/usr/bin/env python3
"""CORE016: embed REAL original source INX ear UV/texture on experimental thick shell.

Front triangles and UV values are never modified. Original native 2D vertices
are affinely placed against observed front-source ear bounding regions, then
duplicated as a shallow 3D shell. The back/side geometry is MAGENTA precisely
because an original side/rear ear skin has not been supplied.
This does not implement native INX transforms/deformers.
"""
from pathlib import Path
import argparse,json,hashlib
import numpy as np,trimesh
from PIL import Image
from trimesh.visual import TextureVisuals,material

def run(folder,out):
    src=json.loads((folder/"native_ear_parts.json").read_text())
    assert src["source_sha256"]=="dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f"
    scene=trimesh.Scene();stats=[]
    for item in src["ears"]:
        name=item["part"];verts=np.array(item["mesh"]["verts"],np.float64)
        uv=np.array(item["mesh"]["uvs"],np.float64)
        native_faces=np.array(item["mesh"]["indices"],np.int32).reshape((-1,3))
        n=len(verts)
        assert len(uv)==n and n in (57,59) and len(native_faces) in (89,93)
        native_box=np.stack([verts.min(0),verts.max(0)])
        u=(verts-native_box[0])/(native_box[1]-native_box[0])
        # This source-inferred overlay placement is NOT original INX node transform.
        if name=="Ear:: Left":
            xp=437+u[:,0]*102
        elif name=="Ear:: Right":
            xp=174+u[:,0]*128
        else:raise ValueError("Unexpected source node")
        yp=44+u[:,1]*303
        x=(xp-360)/225;y=(423-yp)/215
        depth=.06+.32*np.clip((yp-44)/160,0,1)
        front=np.column_stack([x,y,.085+depth/2])
        back=np.column_stack([x,y,.085-depth/2])
        rgba=Image.open(folder/("original_"+name.replace(":","").replace(" ","_")+".png")).convert("RGBA")
        assert rgba.size==tuple(item["texture_dimensions"])
        front_visual=TextureVisuals(uv=uv,material=material.SimpleMaterial(image=rgba))
        scene.add_geometry(trimesh.Trimesh(vertices=front,faces=native_faces,visual=front_visual,process=False),
            node_name=name+"_ORIGINAL_NATIVE_UV_FRONT")
        # Exactly original triangles on the front. New geometry is a separate shell.
        seen={}
        for tri in native_faces:
            for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                k=tuple(sorted((int(a),int(b))));seen[k]=seen.get(k,0)+1
        perimeter=[key for key,v in seen.items() if v==1]
        assert len(perimeter)>12
        wall=np.array([(a,b,b+n) for a,b in perimeter]+[(a,b+n,a+n) for a,b in perimeter],np.int32)
        side_back_faces=np.vstack([native_faces[:,::-1]+n,wall])
        vol=np.vstack([front,back])
        backing=trimesh.Trimesh(vertices=vol,faces=side_back_faces,process=False,
          visual=trimesh.visual.ColorVisuals(vertex_colors=np.tile(
            np.array([231,62,171,255],np.uint8),(len(vol),1))))
        scene.add_geometry(backing,node_name=name+"_UNPAINTED_SYNTHETIC_VOLUME")
        stats.append({"source_part":name,"uuid":item["uuid"],"original_vertex_count":n,
             "original_front_triangle_count":len(native_faces),"volume_extra_triangles":len(side_back_faces),
             "original_texture_sha256":item["texture_sha256"],
             "native_uv_bounds":item["uv_bounds"],"front_uv_unchanged":True,
             "native_source_node_transform_replayed":False})
    out.parent.mkdir(parents=True,exist_ok=True)
    scene.export(out)
    reloaded=trimesh.load(out,force="scene")
    assert len(reloaded.geometry)==4
    report={"status":"REAL_SOURCE_UV_FRONT_ON_EXTRUDED_3D_EAR",
      "source_sha256":src["source_sha256"],
      "original_inx_uv_used":True,"original_tga_rgba_used":True,
      "front_original_artmesh_triangle_topology_preserved":True,
      "original_native_head_yaw_evaluated":False,
      "actual_new_side_or_back_skin":False,
      "source_global_node_transform_fidelity":"NOT_PROVEN_AFFINE_PLACEHOLDER",
      "art_quality":"NOT_ACCEPTED",
      "glb_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"ears":stats}
    out.with_suffix(".qa.json").write_text(json.dumps(report,indent=2)+"\n")
    print("CORE016_3D_ORIGINAL_SOURCE_UV_SHELL_PASS",json.dumps(report)[:5000])
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--original-ears",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    x=a.parse_args();run(x.original_ears,x.out)
