#!/usr/bin/env python3
"""CORE-013 deterministic LOCAL rear ear-fur / invented-curl repair.

Exact input geometry is for the currently QA'd 1254x1254 generated back image,
not a reusable semantic image editor. Output is still GENERATED_UNRIGGED.
Requires numpy, Pillow, OpenCV. No OpenAI API.
"""
import argparse,hashlib,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run(source,out):
    src=np.asarray(Image.open(source).convert("RGB"))
    if src.shape[:2]!=(1254,1254):raise ValueError("Only exact 1254-square generated rear candidate supported")
    if sha(source)!="5f016f460c5632366e5c1dfbfc74d33de79d93faa1d4b71a027ef5fc0ba0d965":
        raise ValueError("Generated back source SHA256 mismatch; refusing to apply hardcoded masks to other images")
    h,w=src.shape[:2];arr=src.astype(np.float32)
    # Only the known ear-back interior tufts in the generated image may be recolored.
    left=np.array([[328,244],[373,255],[410,300],[455,414],[413,505],[333,523],[288,444],[299,315]],np.int32)
    right=np.array([[910,244],[948,281],[976,347],[985,427],[965,505],[876,519],[836,435],[862,323]],np.int32)
    region=np.zeros((h,w),np.uint8)
    cv2.fillPoly(region,[left,right],255)
    cream=((arr[...,0]-arr[...,2]>12)&(arr[...,0]>194)&(arr[...,2]>120)).astype(np.float32)
    a=cv2.GaussianBlur((region.astype(np.float32)/255*cream),(0,0),1.8)
    d=(arr.mean(axis=-1)-205.)/65.
    orange=np.stack([np.clip(224+24*d,155,255),np.clip(148+23*d,76,202),np.clip(76+16*d,32,142)],axis=-1)
    tinted=arr*(1-0.93*a[...,None])+orange*0.93*a[...,None]
    # Remove only non-background pixels in the curl's local region above the head.
    y0,y1,x0,x1=222,347,542,709
    curl=(np.max(np.abs(tinted[y0:y1,x0:x1]-255),axis=2)>19).astype(np.uint8)
    mask=np.zeros((h,w),np.uint8);mask[y0:y1,x0:x1]=curl*255
    mask=cv2.dilate(mask,np.ones((5,5),np.uint8),iterations=1)
    mask[352:,:]=0
    fixed=cv2.inpaint(np.uint8(np.clip(tinted,0,255)),mask,8,cv2.INPAINT_TELEA)
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    Image.fromarray(fixed).save(out)
    changed=np.max(np.abs(fixed.astype(np.int16)-src.astype(np.int16)),axis=2)>10
    report={'status':'DETERMINISTIC_LOCAL_CANDIDATE_REPAIR_NOT_INX_UV',
      'source_sha256':sha(source),'output_sha256':sha(out),
      'changed_pixels_gt10':int(changed.sum()),'changed_frac_gt10':round(float(changed.mean()),4),
      'native_uv_bound':False,'author_art_consistency_passed':False}
    print('CORE013_LOCAL_PATCH',json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();run(a.source,a.out)
