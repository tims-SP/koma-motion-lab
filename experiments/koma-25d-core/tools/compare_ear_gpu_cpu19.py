#!/usr/bin/env python3
"""Real Inox2D ONLY EARS OpenGL PNG vs independent source INX ArtMesh raster.

Both renderers draw same two original ears, not full puppet vs ear.
Fits exactly one XY offset using only neutral, applies unchanged at max.
This comparison is at SCREEN PIXEL / raster level, not 3D skin/animation QA.

python compare_ear_gpu_cpu19.py --native DIR --independent DIR --out DIR
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np,cv2
from PIL import Image

def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def masks(gpu,source,dx=0,dy=0):
    h,w=source.shape[:2]
    alpha=(source[:,:,3]>64).astype(np.uint8)
    aligned=cv2.warpAffine(alpha,np.float32([[1,0,dx],[0,1,dy]]),
        (w,h),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
    gp=((gpu.max(2)>56)&(gpu[:,:,0].astype(np.int16)>gpu[:,:,2].astype(np.int16)+10)).astype(np.uint8)
    roi=np.zeros((h,w),np.uint8);roi[:260,120:555]=1
    return gp*roi,aligned*roi
def stats(native,cpu,dx,dy):
    a,b=masks(native,cpu,dx,dy)
    i=(a>0)&(b>0);u=(a>0)|(b>0)
    transformed=cv2.warpAffine(cpu,np.float32([[1,0,dx],[0,1,dy]]),(720,880),
      flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    premult=transformed[:,:,:3].astype(np.float32)*transformed[:,:,3:4]/255.
    mae=float(np.abs(native.astype(np.float32)-premult)[i].mean()) if i.any() else None
    return {"iou":round(float(i.sum()/max(1,u.sum())),4),
      "overlap_px":int(i.sum()),"native_px":int(a.sum()),"cpu_px":int(b.sum()),
      "overlap_rgb_mae":round(mae,2) if mae is not None else None}
def run(native,independent,out):
    out.mkdir(parents=True,exist_ok=True)
    g={};s={};metrics={}
    for label in ("neutral","maximum"):
        f=native/f"gpu_ears_{label}.png"
        c=independent/f"custom_INX_ears_{label}_transparent.png"
        g[label]=np.asarray(Image.open(f).convert("RGB"))
        s[label]=np.asarray(Image.open(c).convert("RGBA"))
        assert g[label].shape[:2]==s[label].shape[:2]==(880,720)
        metrics[label]={"real_native_openGL_sha256":sha(f),"independent_original_INX_sha256":sha(c)}
    # Search neutral ONLY on narrow ear ROI; no 3D pose-angle fitting or per-ear adjustments.
    arr=g["neutral"]
    gmask=((arr.max(2)>56)&(arr[:,:,0].astype(np.int16)>arr[:,:,2].astype(np.int16)+10)).astype(np.uint8)[:260,120:555]
    cmask=(s["neutral"][:,:,3]>64).astype(np.uint8)[:260,120:555]
    trials=[]
    for dx in range(-25,26):
      for dy in range(-20,21):
        shifted=cv2.warpAffine(cmask,np.float32([[1,0,dx],[0,1,dy]]),(435,260),flags=cv2.INTER_NEAREST)
        n=int((gmask&shifted).sum());u=int((gmask|shifted).sum())
        trials.append((n/max(1,u),dx,dy))
    _,dx,dy=max(trials)
    for key in metrics:
        metrics[key]["raw"]=stats(g[key],s[key],0,0)
        metrics[key]["neutral_offset_no_refit"]=stats(g[key],s[key],dx,dy)
    result={"schema":"core019-real-native-GPU-ears-only-vs-original-CPU/1",
      "actual_native_gpu_only_original_ear_artmeshes":True,
      "head_yaw_normalized_values":{"neutral":.5,"maximum":1.},
      "common_offset_fitted_only_neutral":[dx,dy],
      "original_uv_unchanged":True,
      "full_character_3D_skin":False,
      "quality_pass_exact_pixel_parity":False,
      "poses":metrics}
    (out/"parity19.json").write_text(json.dumps(result,indent=2)+"\n")
    print("CORE019_GPU_CPU_TRUE_SAME_PART_COMPARE",json.dumps(result))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--native",type=Path,required=True)
    p.add_argument("--independent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();run(a.native,a.independent,a.out)
