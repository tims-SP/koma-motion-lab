#!/usr/bin/env python3
"""Reproduce CORE-008E's *image-space* UV interpolation control.

Source files: user-supplied generated frontal and 3/4 RGB images.
UV controls: view_correspondence.json from the audited CORE-008E pair.
This intentionally does NOT pretend to preserve official Aka INX UV/rig,
infer depth, generate side paintings or execute genuine 3D skinning.

Usage:
python register_gpt_pair8.py \
  --front front.png --three-quarter view.png \
  --correspondence view_correspondence.json --out output
Requires numpy, Pillow, scipy, opencv-python-headless, ffmpeg.
"""
import argparse,json,math,subprocess
from pathlib import Path
import cv2,numpy as np
from PIL import Image
from scipy.interpolate import RBFInterpolator

N=720
BG=np.array([241,242,246],np.float32)
def image(path):
    i=Image.open(path).convert("RGB")
    return cv2.resize(np.asarray(i),(N,N),interpolation=cv2.INTER_AREA)
def alpha(rgb):
    # Diagnostic foreground only; not an original art-part matte.
    v=(255-rgb.astype(np.int16)).max(axis=2)
    m=(v>24).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    exterior=1-m
    cv2.floodFill(exterior,np.zeros((N+2,N+2),np.uint8),(0,0),2)
    mask=(exterior!=2).astype(np.float32)
    return cv2.GaussianBlur(mask,(0,0),0.85)
def mapfield(data):
    assert data["actual_original_inx_uv_used"] is False
    links=data["landmarks"]
    assert len(links)>=20
    p=np.array([x["generated_front_uv"] for x in links],np.float32)*N
    q=np.array([x["generated_view_uv"] for x in links],np.float32)*N
    f=np.array([(0,0),(N/2,0),(N-1,0),(N-1,N/2),
                (N-1,N-1),(N/2,N-1),(0,N-1),(0,N/2)],np.float32)
    p=np.concatenate([p,f]);q=np.concatenate([q,f])
    interp=RBFInterpolator((p+q)/2,q-p,
                           kernel="thin_plate_spline",smoothing=2.)
    grid=np.linspace(0,N-1,91,dtype=np.float32)
    xx,yy=np.meshgrid(grid,grid)
    field=interp(np.column_stack([xx.ravel(),yy.ravel()])).reshape(91,91,2)
    return cv2.resize(np.float32(field),(N,N),interpolation=cv2.INTER_CUBIC)
def composed(a,aa,b,ab,fx,fy,disp,t,registered):
    if registered:
        axy=(fx-t*disp[...,0],fy-t*disp[...,1])
        bxy=(fx+(1-t)*disp[...,0],fy+(1-t)*disp[...,1])
    else:
        axy=(fx,fy);bxy=(fx,fy)
    ia=cv2.remap(a,*axy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,
                 borderValue=(255,255,255))
    ib=cv2.remap(b,*bxy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,
                 borderValue=(255,255,255))
    wa=cv2.remap(aa,*axy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*(1-t)
    wb=cv2.remap(ab,*bxy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*t
    val=ia.astype(np.float32)*wa[...,None]+ib.astype(np.float32)*wb[...,None]
    val+=(1-wa-wb)[...,None]*BG
    return np.uint8(np.clip(val,0,255))
def main(args):
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    data=json.loads(Path(args.correspondence).read_text())
    a=image(args.front);b=image(args.three_quarter)
    aa=alpha(a);ab=alpha(b)
    disp=mapfield(data)
    fy,fx=np.indices((N,N),dtype=np.float32)
    target=out/"registered_vs_crossfade.mp4"
    proc=subprocess.Popen([
       "ffmpeg","-hide_banner","-loglevel","error","-y",
       "-f","rawvideo","-pix_fmt","rgb24",
       "-s",f"{2*N}x{N}","-r","24","-i","-",
       "-c:v","libx264","-pix_fmt","yuv420p",
       "-preset","veryfast","-crf","19",str(target)
    ],stdin=subprocess.PIPE)
    for i in range(96):
        t=(1-math.cos(2*math.pi*i/95))/2
        result=composed(a,aa,b,ab,fx,fy,disp,t,True)
        control=composed(a,aa,b,ab,fx,fy,disp,t,False)
        proc.stdin.write(np.concatenate([result,control],axis=1).tobytes())
    proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError("ffmpeg encode failed")
    # Inspect actual encoded output, not source PNG only.
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
      "-i",str(target),"-vf",
      "select=eq(n\\,0)+eq(n\\,24)+eq(n\\,48)+eq(n\\,71)+eq(n\\,95)",
      "-vsync","0",str(out/"decoded_%02d.png")],check=True)
    frames=sorted(out.glob("decoded_*.png"))
    if len(frames)!=5:raise RuntimeError("encoded-video audit failed")
    report={"status":"IMAGE_SPACE_UV_COMPARISON_ONLY",
       "frames":96,"fps":24,"registered_2d_landmarks":len(data["landmarks"]),
       "decoded_samples":len(frames),
       "original_inx_uv":"NOT_REUSED",
       "part_separation":"NOT_IMPLEMENTED",
       "shallow_3d":"NOT_IMPLEMENTED",
       "final_art_quality":"REQUIRES_MANUAL_REVIEW"}
    (out/"qa.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--front",required=True)
    p.add_argument("--three-quarter",required=True)
    p.add_argument("--correspondence",required=True)
    p.add_argument("--out",required=True)
    main(p.parse_args())
