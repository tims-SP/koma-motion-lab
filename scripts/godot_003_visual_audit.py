#!/usr/bin/env python3
"""GODOT-003: auditable real Cubism render diagnostics, NOT a parity certificate.

Input: actual Godot-rendered motion frames and a static control with identical
camera transform. Output: numeric metrics and zoomed review sheets, never assets
in the source repository. Official Cubism reference frames are still required
to certify mesh, clipping and blend fidelity.
"""
from collections import deque
from pathlib import Path
import json
import math
from PIL import Image, ImageChops, ImageDraw, ImageStat

OUT = Path("out/godot-002")
MOTION = sorted(OUT.glob("shot*.png"))
STATIC = sorted(OUT.glob("framed-static*.png"))
BACKGROUND = (18, 28, 43)
SAMPLE_INDICES = [0, 22, 45, 67, 89]

def foreground(im, scale=4):
    small = im.convert("RGB").resize((im.width//scale, im.height//scale))
    w, h = small.size
    pix = small.load()
    mask = bytearray(w*h)
    for y in range(h):
        for x in range(w):
            p = pix[x, y]
            if sum(abs(p[c]-BACKGROUND[c]) for c in range(3)) > 90:
                mask[y*w+x] = 1
    return mask, w, h

def metrics(im):
    mask, w, h = foreground(im)
    n = sum(mask)
    if not n:
        return {"pixels":0,"coverage":0.0,"bbox":None,"component_fraction":0.0}
    coords = [i for i,b in enumerate(mask) if b]
    minx = min(i%w for i in coords)
    maxx = max(i%w for i in coords)
    miny = min(i//w for i in coords)
    maxy = max(i//w for i in coords)
    # Connected components on downsampled foreground mask, 8-connectivity.
    seen = bytearray(w*h)
    largest = 0
    components = 0
    for start in coords:
        if seen[start]:
            continue
        components += 1
        stack = [start]
        seen[start] = 1
        count = 0
        while stack:
            k = stack.pop()
            count += 1
            y,x = divmod(k, w)
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    nx,ny=x+dx,y+dy
                    if (dx or dy) and 0<=nx<w and 0<=ny<h:
                        neighbor=ny*w+nx
                        if mask[neighbor] and not seen[neighbor]:
                            seen[neighbor]=1
                            stack.append(neighbor)
        largest=max(largest,count)
    return {
        "pixels":n,
        "coverage":round(n/(w*h),5),
        "bbox":[minx*4,miny*4,(maxx+1)*4,(maxy+1)*4],
        "bbox_width":(maxx-minx+1)*4,
        "bbox_height":(maxy-miny+1)*4,
        "components":components,
        "largest_component_fraction":round(largest/n,5)
    }

def delta(a,b):
    d=ImageChops.difference(a.convert("RGB"),b.convert("RGB"))
    return sum(ImageStat.Stat(d).mean)/3

def motion_roi(a,b,reference_bbox):
    d=ImageChops.difference(a.convert("RGB"),b.convert("RGB"))
    cut=d.crop(reference_bbox)
    return round(sum(ImageStat.Stat(cut).mean)/3,4)

def cropped(im,bbox):
    x0,y0,x1,y1=bbox
    width=max(x1-x0,10);height=max(y1-y0,10)
    margin=max(24,int(max(width,height)*.16))
    box=(max(0,x0-margin),max(0,y0-margin),
         min(im.width,x1+margin),min(im.height,y1+margin))
    return im.crop(box)

def contact_sheet(frames, labels, file, crop_bbox=None):
    thumb_size=(480,300)
    cols=3
    rows=math.ceil(len(frames)/cols)
    board=Image.new("RGB",(cols*thumb_size[0],rows*thumb_size[1]),(28,32,39))
    draw=ImageDraw.Draw(board)
    for i,(img,label) in enumerate(zip(frames,labels)):
        if crop_bbox is not None:
            img=cropped(img,crop_bbox)
        img=img.copy()
        img.thumbnail((thumb_size[0]-16,thumb_size[1]-32),Image.Resampling.LANCZOS)
        left=(i%cols)*thumb_size[0]+(thumb_size[0]-img.width)//2
        top=(i//cols)*thumb_size[1]+22+(thumb_size[1]-32-img.height)//2
        board.paste(img,(left,top))
        draw.text(((i%cols)*thumb_size[0]+12,(i//cols)*thumb_size[1]+4),
                  label, fill="white")
    board.save(file,quality=92,subsampling=0)

def main():
    if len(MOTION)!=90 or len(STATIC)!=8:
        raise SystemExit(f"GODOT003_NEEDS_REAL_FRAMES motion={len(MOTION)} static={len(STATIC)}")
    with Image.open(STATIC[4]) as src:
        still=src.convert("RGB")
    images=[]
    for index in SAMPLE_INDICES:
        with Image.open(MOTION[index]) as src:
            images.append(src.convert("RGB"))
    if still.size!=(960,540) or any(im.size!=still.size for im in images):
        raise SystemExit("GODOT003_INVALID_RESOLUTION")
    image_metrics=[metrics(im) for im in images]
    static_metrics=metrics(still)
    bbox=static_metrics["bbox"]
    if not bbox:
        raise SystemExit("GODOT003_NO_CHARACTER_IN_STATIC_REFERENCE")
    # Use union of all foreground boxes, static and animated, for crop review.
    boxes=[m["bbox"] for m in [static_metrics]+image_metrics if m["bbox"]]
    bbox=[min(b[0] for b in boxes),min(b[1] for b in boxes),
          max(b[2] for b in boxes),max(b[3] for b in boxes)]
    signals=[round(delta(still,im),4) for im in images]
    roi_signals=[motion_roi(still,im,bbox) for im in images]
    motion_pair=[round(delta(a,b),4) for a,b in zip(images,images[1:])]
    with Image.open(STATIC[0]) as f0,Image.open(STATIC[-1]) as f1:
        static_stability=round(delta(f0,f1),6)
    diag={
        "stage":"GODOT-003",
        "status":"PLAYBACK_EVIDENCE_ONLY__REFERENCE_VISUAL_REVIEW_REQUIRED",
        "original_model":"301003_x.moc3",
        "frame_count":90,
        "static_control_frames":8,
        "static_control_difference":static_stability,
        "static_image":static_metrics,
        "dynamic_samples":[{"frame":idx,"geometry":geo,
                            "rgb_difference_from_static":d,
                            "roi_difference_from_static":r}
                           for idx,geo,d,r in zip(SAMPLE_INDICES,image_metrics,signals,roi_signals)],
        "global_motion_pair_differences":motion_pair,
        "combined_foreground_bbox":bbox,
        "review_warnings":[],
        "not_certified":["original Cubism runtime pixel parity",
                         "clipping and inverted masks",
                         "artmesh weighting and mesh deformations",
                         "render order and translucency",
                         "face / clothing / texture fidelity"]
    }
    if static_stability>0.05:
        diag["review_warnings"].append("static control is not stable")
    if max(roi_signals)<0.5:
        diag["review_warnings"].append("motion changes small even inside foreground crop")
    if static_metrics["largest_component_fraction"]<0.4:
        diag["review_warnings"].append("foreground is fragmented; inspect missing meshes or transparency")
    if any((b[0]<=4 or b[1]<=4 or b[2]>=956 or b[3]>=536) for b in boxes):
        diag["review_warnings"].append("foreground touches output boundary: possible clipped character")
    contact_sheet([still]+images,["static / same camera"]+[f"nod frame {i}" for i in SAMPLE_INDICES],
                  OUT/"visual-comparison.jpg")
    contact_sheet([still]+images,["static / zoom"]+[f"nod {i} / zoom" for i in SAMPLE_INDICES],
                  OUT/"visual-crops.jpg",crop_bbox=bbox)
    (OUT/"visual-audit.json").write_text(json.dumps(diag,indent=2,ensure_ascii=False)+"\n")
    print("GODOT003_VISUAL_AUDIT",json.dumps(diag,ensure_ascii=False))
    # Do not pass the final art-fidelity gate without a real official reference.
    if static_stability>0.05 or not bbox:
        raise SystemExit("GODOT003_REFERENCE_CONTROL_INVALID")
    print("GODOT003_DIAGNOSTICS_PASS__ART_PARITY_NOT_CLAIMED")

if __name__=="__main__":
    main()
