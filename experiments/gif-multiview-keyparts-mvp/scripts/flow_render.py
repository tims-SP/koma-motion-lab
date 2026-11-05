#!/usr/bin/env python3
"""Flow-based view-conditioned deformation study on recovered real P0 reference artwork.

The result is a visual interpolation candidate. Original 0/45/90 authored
view frames remain authoritative; flow is an estimated correspondence field,
not a proven semantic ArtMesh or generated missing concealed anatomy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return np.asarray(Image.open(path).convert("RGBA")).copy()


def whole_gray(a):
    alpha=a[:,:,3:4].astype(np.float32)/255
    rgb=a[:,:,:3].astype(np.float32)*alpha+(1-alpha)*np.array([50,62,78],dtype=np.float32)
    return cv2.cvtColor(rgb.astype(np.uint8),cv2.COLOR_RGB2GRAY)


def get_flow(a,b,mode="dis"):
    gray_a,gray_b=whole_gray(a),whole_gray(b)
    if mode.startswith("dis"):
        optical=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        optical.setFinestScale(0)
        optical.setVariationalRefinementIterations(8)
        return optical.calc(gray_a,gray_b,None),optical.calc(gray_b,gray_a,None)
    options=dict(pyr_scale=0.5,levels=5,winsize=33,iterations=5,poly_n=7,poly_sigma=1.5,flags=0)
    return (cv2.calcOpticalFlowFarneback(gray_a,gray_b,None,**options),
            cv2.calcOpticalFlowFarneback(gray_b,gray_a,None,**options))


def warp_float(src,flow,amount,grid):
    maps=(grid-amount*flow).astype(np.float32)
    return cv2.remap(src,maps[:,:,0],maps[:,:,1],interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT,borderValue=0)


def morph(a,b,flow_ab,flow_ba,t,grid,single_source=False):
    if t<=0:return a.copy()
    if t>=1:return b.copy()
    af=a.astype(np.float32)/255
    bf=b.astype(np.float32)/255
    fa=np.concatenate([af[:,:,:3]*af[:,:,3:4],af[:,:,3:4]],axis=2)
    fb=np.concatenate([bf[:,:,:3]*bf[:,:,3:4],bf[:,:,3:4]],axis=2)
    pa=warp_float(fa,flow_ab,t,grid)
    pb=warp_float(fb,flow_ba,1-t,grid)
    pix=(pa if t<0.5 else pb) if single_source else pa*(1-t)+pb*t
    alpha=np.clip(pix[:,:,3:4],0,1)
    rgb=np.divide(pix[:,:,:3],np.maximum(alpha,1e-5))
    return (np.concatenate([np.clip(rgb,0,1),alpha],axis=2)*255).astype(np.uint8)


def paint_background(img,rgba):
    fg=Image.fromarray(rgba,"RGBA")
    bg=Image.new("RGBA",fg.size,(49,61,78,255))
    bg.alpha_composite(fg)
    return bg.convert("RGB")


def create_contact(directory,frames):
    dim=320
    margin=14
    names=[0,22.5,45,67.5,90]
    board=Image.new("RGB",(dim*len(names),dim+42),(22,31,44))
    d=ImageDraw.Draw(board)
    for i,key in enumerate(names):
        thumb=paint_background(None,frames[key]).resize((dim-16,dim-16),Image.Resampling.LANCZOS)
        board.paste(thumb,(i*dim+8,8))
        d.text((i*dim+12,dim+1),f"Yaw {key:05.1f} deg",fill="white")
    outfile=directory/"contact.png"
    board.save(outfile)
    return outfile


def run(root,out,mode):
    root=Path(root).resolve()
    out=Path(out).resolve()
    out.mkdir(exist_ok=True,parents=True)
    refs={}
    for yaw in [0,45,90]:
        refs[yaw]=read(root/f"recovered-review/frames/head_8/yaw{yaw:03d}_whole.png")
        assert refs[yaw].shape==(443,443,4)
    yy,xx=np.indices((443,443),dtype=np.float32)
    grid=np.stack((xx,yy),axis=2)
    flow={}
    flow_metrics={}
    for a,b in [(0,45),(45,90)]:
        ab,ba=get_flow(refs[a],refs[b],mode)
        flow[(a,b)]=(ab,ba)
        flow_metrics[str(a)+"-"+str(b)]={
            "fwdMeanPx":float(np.linalg.norm(ab,axis=2).mean()),
            "fwdMaxPx":float(np.linalg.norm(ab,axis=2).max()),
            "revMeanPx":float(np.linalg.norm(ba,axis=2).mean()),
        }
    frames={}
    hashes={}
    for yaw in np.arange(0,90.01,2.5):
        yaw=round(float(yaw),1)
        if yaw in refs:
            frame=refs[yaw].copy()
        else:
            a,b=(0,45) if yaw<45 else (45,90)
            t=(yaw-a)/(b-a)
            frame=morph(refs[a],refs[b],*flow[(a,b)],t,grid,single_source=(mode=="dis_sharp"))
        frames[yaw]=frame
        outfile=out/("yaw%05.1f.png"%yaw).replace(".","p")
        # Restore a meaningful PNG extension.
        outfile=out/("yaw%03d_%d.png"%(int(yaw),int(round((yaw%1)*10))))
        Image.fromarray(frame,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS).save(outfile)
        hashes[str(yaw)]={"sha256":sha(outfile),"path":str(outfile),"alphaPixels":int((frame[:,:,3]>0).sum())}
    contact=create_contact(out,frames)
    # GIF for visual review (palette, diagnostic only), then reverse for seamless return.
    seq=[Image.fromarray(frames[round(float(y),1)],"RGBA").resize((512,512),Image.Resampling.LANCZOS)
         for y in np.arange(0,90.01,2.5)]
    animated=seq+seq[-2:0:-1]
    gif=out/"yaw000-yaw090-flow-review.gif"
    animated[0].save(gif,save_all=True,append_images=animated[1:],duration=90,
                     disposal=2,loop=0,optimize=False,transparency=0)
    qa={"schema":"KOMA-P0-OPTICAL-FLOW-VIEW-STUDY-V1",
        "characterId":"p0_character_001","renderMethod":mode,
        "sourceRole":"verified_recovered_whole_view_GIF_pixels",
        "viewSourceSHA256":{str(yaw):sha(root/f"recovered-review/frames/head_8/yaw{yaw:03d}_whole.png") for yaw in refs},
        "flowMetrics":flow_metrics,
        "referenceKeyframeCount":3,"candidateFrames":len(frames),
        "contact":str(contact),"gif":str(gif),"gifSHA256":sha(gif),
        "frames":hashes,"semanticArtMeshesProven":False,
        "holdoutHumanVisualReviewed":False,
        "status":"REVIEW_CANDIDATE"}
    (out/"flow-qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:qa[k] for k in ["renderMethod","referenceKeyframeCount",
                                     "candidateFrames","flowMetrics","gif","gifSHA256","status"]},indent=2))
    return qa


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--mode",choices=["dis","farneback","dis_sharp"],default="dis")
    args=p.parse_args()
    run(args.root,args.out,args.mode)
