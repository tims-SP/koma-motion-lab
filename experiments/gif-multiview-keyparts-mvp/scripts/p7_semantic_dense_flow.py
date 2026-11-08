#!/usr/bin/env python3
"""P0 view-dependent semantic texture correspondence via original RGBA parts.

Per-part bidirectional DIS optical flow is computed on source transparent
ArtMesh artwork. Flow-displaced premultiplied pixels are composed with depth
and original P0 keyframes, preserving semantic IDs and source hashes.

Original drawing is the only source of visible pixels at keyframe angles.
"""
import argparse, hashlib, json, math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from flow_render import sha,get_flow
from p1_front_semantic import alpha_over

CANVAS=443
KEYS=(0,45,90)
DEFAULT_ANGLES=(0,22.5,45,67.5,90)

def part_to_native(path):
    with Image.open(path) as p:
        image=np.asarray(p.convert("RGBA")).astype(np.float32)/255.0
    if image.shape!=(1024,1024,4):
        raise ValueError("Expected global RGBA source 1024: "+str(path))
    # alpha-premultiplied resize: avoid RGB leaks under transparent edges
    image[:,:,:3]*=image[:,:,3:4]
    resized=cv2.resize(image,(CANVAS,CANVAS),interpolation=cv2.INTER_AREA)
    return resized

def native_to_rgba(array):
    a=np.clip(array[:,:,3:4],0,1)
    rgb=np.divide(np.clip(array[:,:,:3],0,1),np.maximum(a,1e-6))
    return np.uint8(np.rint(np.concatenate([np.clip(rgb,0,1),a],axis=2)*255))

def preview_shots(frames,out):
    keys=[x for x in DEFAULT_ANGLES if x in frames] or sorted(frames)
    col=320
    board=Image.new("RGB",(len(keys)*col,col+40),(27,37,52))
    draw=ImageDraw.Draw(board)
    for i,angle in enumerate(keys):
        native=Image.fromarray(frames[angle],"RGBA")
        matte=Image.new("RGBA",native.size,(52,69,87,255))
        matte.alpha_composite(native)
        board.paste(matte.convert("RGB").resize((col,col),Image.Resampling.LANCZOS),(i*col,0))
        draw.text((i*col+10,col+8),f"{angle:05.1f}°",fill="white")
    board.save(out/"semantic-dense-flow-contact.jpg",quality=93)
    return out/"semantic-dense-flow-contact.jpg"

def run(root,out,angles,mode="dis",write_layer=False,texture_mode="blend"):
    root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    multi=json.loads((root/"p5-see-through/mv-candidate/parts.json").read_text())
    assert multi["characterId"]=="p0_character_001" and len(multi["parts"])==39
    slots={(p["yawDeg"],p["semanticId"]):p for p in multi["parts"]}
    assert len(slots)==39
    ids=list(dict.fromkeys(p["semanticId"] for p in multi["parts"] if p["yawDeg"]==0))
    sources={}
    for y in KEYS:
        reference=next(p for p in multi["wholeViews"] if p["yawDeg"]==y)
        f=root/reference["path"]
        assert sha(f)==reference["sha256"]
        sources[y]=f
    samples={}
    for y in KEYS:
        for sid in ids:
            p=slots[(y,sid)]
            f=root/p["path"]
            if sha(f)!=p["frameSha256"]:
                raise ValueError("Layer sha mismatch "+str((y,sid)))
            samples[y,sid]=part_to_native(f)
    grids=np.meshgrid(np.arange(CANVAS,dtype=np.float32),
                      np.arange(CANVAS,dtype=np.float32))
    grid=np.stack(grids,axis=2)
    flow={}
    diagnostic={}
    for a,b in ((0,45),(45,90)):
        diagnostic[f"{a}-{b}"]={}
        for sid in ids:
            A=slots[a,sid];B=slots[b,sid]
            if A["visibility"]!="visible" or B["visibility"]!="visible":
                flow[a,b,sid]=None
                continue
            # Use original P0 semantic pixels, not full-portrait flow.
            sA=native_to_rgba(samples[a,sid]);sB=native_to_rgba(samples[b,sid])
            fwd,rev=get_flow(sA,sB,mode="dis")
            flow[a,b,sid]=(fwd,rev)
            diagnostic[f"{a}-{b}"][sid]={
                "fwdMeanPx":round(float(np.linalg.norm(fwd,axis=2).mean()),3),
                "revMeanPx":round(float(np.linalg.norm(rev,axis=2).mean()),3),
                "sourceA":A["frameSha256"],"sourceB":B["frameSha256"]
            }
    rendered={};qa_entries=[]
    for angle in angles:
        if angle in KEYS:
            p=sources[angle]
            with Image.open(p) as im:
                rgba=np.asarray(im.convert("RGBA")).copy()
            img=Image.fromarray(rgba,"RGBA").resize((CANVAS,CANVAS),Image.Resampling.LANCZOS)
            rgba=np.asarray(img)
            keyframe=np.asarray(Image.open(p).convert("RGBA"))
        else:
            a,b=(0,45) if angle<45 else (45,90)
            t=(angle-a)/(b-a)
            drawOrder=sorted(ids,key=lambda sid:slots[a,sid]["depthOrder"])
            whole=np.zeros((CANVAS,CANVAS,4),dtype=np.uint8)
            for sid in drawOrder:
                A=slots[a,sid];B=slots[b,sid]
                pa,pb=samples[a,sid],samples[b,sid]
                ab=flow[a,b,sid]
                if ab:
                    fwd,rev=ab
                    ma=grid-t*fwd
                    mb=grid-(1-t)*rev
                    wa=cv2.remap(pa,ma[:,:,0],ma[:,:,1],
                                 interpolation=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,borderValue=0)
                    wb=cv2.remap(pb,mb[:,:,0],mb[:,:,1],
                                 interpolation=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,borderValue=0)
                    if texture_mode=="single":
                        merged=wa if t<=0.5 else wb
                    elif texture_mode=="adaptive" and a==45 and b==90:
                        merged=wa if t<=0.58 else wb
                    elif texture_mode=="guided" and a==45 and b==90:
                        start,end=(0.50,0.70)
                        if t<=start:
                            merged=wa
                        elif t>=end:
                            merged=wb
                        else:
                            blend=(t-start)/(end-start)
                            blend=blend*blend*(3-2*blend)
                            merged=wa*(1-blend)+wb*blend
                    else:
                        merged=wa*(1-t)+wb*t
                elif A["visibility"]=="visible":
                    merged=pa*(1-t)
                elif B["visibility"]=="visible":
                    merged=pb*t
                else:
                    continue
                raw=native_to_rgba(merged)
                whole=alpha_over(whole,raw)
                if write_layer:
                    layerdir=out/"layers"/f"{angle:05.1f}".replace(".","p")
                    layerdir.mkdir(parents=True,exist_ok=True)
                    Image.fromarray(raw,"RGBA").save(layerdir/f"{sid}.png")
            rgba=whole
        rendered[float(angle)]=rgba
        frame_label=str(int(angle)) if float(angle).is_integer() else str(angle).replace(".","p")
        frame=out/("yaw"+frame_label+".png")
        if angle in KEYS:
            # Keyframes are exact original P0 pixel arrays.
            Image.fromarray(keyframe,"RGBA").save(frame)
        else:
            Image.fromarray(rgba,"RGBA").resize((1024,1024),Image.Resampling.LANCZOS).save(frame)
        qa_entries.append({"angle":angle,"image":str(frame.relative_to(root)),
                           "sha256":sha(frame),"realSource":angle in KEYS})
    contact=preview_shots(rendered,out)
    report={
        "schema":"KOMA-P0-P7-SEMANTIC-DENSE-FLOW-CORRESPONDENCE-TRIAL-V1",
        "characterId":"p0_character_001",
        "sourceRegistrySHA256":sha(root/"p5-see-through/mv-candidate/parts.json"),
        "nativeOpticalFlowCanvas":[CANVAS,CANVAS],
        "sourceRGBARegistryCanvas":[1024,1024],
        "algorithm":"per-semantic bidirectional DIS + premultiplied RGBA flow warping",
        "textureSelection":texture_mode,
        "sourceRole":"Real P0 original and See-through PSD-derived registered RGBAs",
        "originalKeyframes":[0,45,90],
        "sampledAngles":angles,
        "partCount":len(ids),
        "flowDiagnostics":diagnostic,
        "frames":qa_entries,
        "contactImage":str(contact.relative_to(root)),
        "contactSHA256":sha(contact),
        "status":"VISUAL_REVIEW_CANDIDATE",
        "artisticAcceptance":"PENDING"
    }
    (out/"qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"angles":angles,
                      "partCount":len(ids),"contactSHA256":sha(contact),
                      "frames":[e["sha256"][:12] for e in qa_entries]},
                     ensure_ascii=False,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--angles",default=",".join(map(str,DEFAULT_ANGLES)))
    p.add_argument("--write-layers",action="store_true")
    p.add_argument("--texture-mode",choices=["blend","single","adaptive","guided"],default="blend")
    a=p.parse_args()
    run(a.root,a.output,[float(x) for x in a.angles.split(",")],
        write_layer=a.write_layers,texture_mode=a.texture_mode)
