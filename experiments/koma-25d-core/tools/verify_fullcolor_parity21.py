#!/usr/bin/env python3
"""CORE021 actual full-color source ear parity from two REAL renderer results.

Run with --native PATH --cpu PATH --out PATH. Only original native ear parts;
exact same source input raw yaw/pitch. No per-pose fitting; screen offset 0,0.
CPU input assets and native frames are supplied in conversation bundle;
binary art is NOT stored in the text-only Git repo.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
P=[-1.,-.5,0.,.25,.5,.75,1.]
def run(native,cpu,out):
    rows=[]
    for i,yaw in enumerate(P):
        a=native/f"native_{i:03d}.png"
        b=cpu/f"cpu_{i:03d}.png"
        gpu=np.asarray(Image.open(a).convert("RGB"),dtype=np.float32)
        rgba=np.asarray(Image.open(b).convert("RGBA"),dtype=np.float32)
        assert gpu.shape==(880,720,3) and rgba.shape==(880,720,4)
        roi=np.zeros((880,720),dtype=bool);roi[:290,95:590]=True
        g=(gpu.max(2)>16)&roi
        c=(rgba[:,:,3]>16)&roi
        valid=g&c
        iou=float(valid.sum()/max(1,(g|c).sum()))
        rgb=rgba[:,:,:3]*(rgba[:,:,3:4]/255.)
        mae=float(np.abs(gpu-rgb)[valid].mean())
        rows.append({"raw_yaw":yaw,"raw_pitch":0.,
          "iou":round(iou,6),"rgb_mae":round(mae,4),
          "native_gpu_sha256":hashlib.sha256(a.read_bytes()).hexdigest(),
          "independent_cpu_sha256":hashlib.sha256(b.read_bytes()).hexdigest()})
        assert iou>=.99,(i,rows[-1])
        assert mae<=1.0,(i,rows[-1])
    doc={"schema":"koma-core021-real-native-ear-parity/1",
         "original_author":"seagetch","original_license":"CC BY 4.0",
         "original_Aka_INX_sha256":"dbf82ffb86d1c761bca883ad37ec1c47487a447f8104290b459ce60aaee81e0f",
         "upstream_inox2d_commit":"d4dd9dd7f16b775042cbda44370570abf9a8cf81",
         "raw_actual_default":[0,0],"input_range":[-1,1],
         "mesh_vertex_counts":[57,59],"original_source_UV_kept":True,
         "one_shared_pixel_translation":[0,0],
         "mask":"All source-colored native pixels in x95:590,y0:290 vs original rgba alpha, threshold 16; NO warm-only restriction",
         "exact_byte_for_byte_pixel_parity":False,
         "source_original_D_SDK_parity":False,
         "new_3D_head_skin":False,"production_360_character":False,
         "acceptance":"SOURCE_INOX_NATIVE_EAR_COMPONENT_HIGH_FIDELITY_WITH_LIMITED_TOLERANCE",
         "rows":rows}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,indent=2)+"\n")
    print("CORE021_SEVEN_SAME_INPUT_ORIGINAL_EAR_GPU_CPU_PARITY_PASS",json.dumps(rows))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--cpu",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args();run(x.native,x.cpu,x.out)
