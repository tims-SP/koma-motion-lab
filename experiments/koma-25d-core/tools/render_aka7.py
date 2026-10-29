#!/usr/bin/env python3
"""CORE-007: animated original Aka 62-layer artwork with shallow surface hypothesis.

NOT an Inochi runtime renderer. Tested candidates:
  FLAT - 2D perspective-like cos(yaw) compression + per-layer translation
  CURVE - same original raster layers, plus cylindrical front-surface depth
Both use the same official layered PSD, not a 3D source or hallucinated art.
Each frame is explicitly labeled as source-derived diagnostic. The INX's
original meshes are audited separately but not yet driven by this renderer.
"""
from __future__ import annotations
import argparse,json,math,time,base64,textwrap,io
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageOps
from psd_tools import PSDImage

SIZE=640
BG=(241,242,246)
def rgba(image):return np.array(image.convert("RGBA"),dtype=np.uint8)
def bbox_square(source:Image.Image):
    alpha=np.array(source.convert("RGBA").getchannel("A"))
    ys,xs=np.where(alpha>8)
    if len(xs)<20000:raise ValueError("Source artwork unexpectedly empty")
    left,right=int(xs.min()),int(xs.max())+1
    top,bottom=int(ys.min()),int(ys.max())+1
    span=int(max(right-left,bottom-top)*1.17)
    cx=(left+right)//2;cy=(top+bottom)//2
    return [cx-span//2,cy-span//2,cx+span//2,cy+span//2]

def on_canvas(img:Image.Image,bounds,source_size):
    l,t,r,b=bounds
    canvas=Image.new("RGBA",source_size,(0,0,0,0))
    if img.width and img.height:
        canvas.paste(img.convert("RGBA"),(l,t))
    return canvas

def depth_role(name):
    n=name.lower()
    if "back side hair" in n:return -0.22,0.45
    if "ear" in n:return -0.07,0.35
    if "neck" in n:return -0.15,0.30
    if n.strip()== "face":return 0.02,0.80
    if "front hair" in n:return 0.28,0.45
    if "side hair" in n:return 0.18,0.45
    if "eye" in n or "eyebrow" in n:return 0.06,0.65
    if "nose" in n:return 0.16,0.65
    if "mouth" in n or "lip" in n:return 0.12,0.60
    return 0.08,0.55

def compose_rgba(background,overlay):
    # Correct Porter-Duff over in float; preserve alpha.
    a=overlay[...,3:4].astype(np.float32)/255.
    b=background[...,3:4].astype(np.float32)/255.
    combined=a+b*(1-a)
    color=(overlay[...,:3].astype(np.float32)*a+
           background[...,:3].astype(np.float32)*b*(1-a))
    background[...,:3]=np.uint8(np.clip(color/np.maximum(combined,1.e-7),0,255))
    background[...,3]=np.uint8(np.clip(combined[...,0]*255,0,255))
    return background

def remap_layer(layer,angle,mode,role):
    # Inverse surface-projection map: reference layer pixels at x0 / y0
    # are placed at x_camera = x0*cos(yaw) + surfaceDepth(x0)*sin(yaw).
    # This is only a front-facing shallow shell; at extreme yaw back art
    # is unknown. Do not make 90°/180° claims from this routine.
    rad=math.radians(angle)
    co=max(0.55,math.cos(rad))
    si=math.sin(rad)
    depth,bulge=role
    yy,xx=np.indices((SIZE,SIZE),dtype=np.float32)
    pivot_x=SIZE*0.5
    pivot_y=SIZE*0.51
    layer_depth=depth*SIZE*0.16
    x0=(xx-pivot_x-layer_depth*si)/co+pivot_x
    if mode=="curved":
        for _ in range(4):
            u=np.clip((x0-pivot_x)/(SIZE*.36),-1.,1.)
            z=(layer_depth + bulge*SIZE*0.085*np.sqrt(np.maximum(0.,1-u*u)))
            x0=(xx-pivot_x-z*si)/co+pivot_x
    y0=yy+(yy-pivot_y)*(-0.016*(1-co))
    return cv2.remap(layer,x0.astype(np.float32),y0.astype(np.float32),
                     cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,
                     borderValue=(0,0,0,0))

def run(psdfile,out):
    out.mkdir(parents=True,exist_ok=True)
    psd=PSDImage.open(psdfile)
    original=psd.composite().convert("RGBA")
    box=bbox_square(original)
    size=(psd.width,psd.height)
    layers=[]
    all_nodes=list(psd.descendants())
    # A PSD's layer order can differ from renderer draw order. Never assume.
    # Determine the correct front-to-back ordering by source pixel parity.
    for layer in all_nodes:
        if layer.is_group() or not layer.is_visible():continue
        if layer.width<=0 or layer.height<=0:continue
        im=layer.composite()
        if im is None:continue
        full=on_canvas(im,(layer.left,layer.top,layer.right,layer.bottom),size)
        patch=full.crop(box).resize((SIZE,SIZE),Image.Resampling.LANCZOS)
        arr=rgba(patch)
        if np.count_nonzero(arr[...,3]>8)<60:continue
        layers.append((str(layer.name),arr,depth_role(str(layer.name))))
    if len(layers)<40:raise ValueError("Expected real layered anime PSD, got "+str(len(layers)))
    canonical=original.crop(box).resize((SIZE,SIZE),Image.Resampling.LANCZOS)
    canonical.save(out/"source_front.png")
    def over_white(image):
        white=Image.new("RGBA",(SIZE,SIZE),(255,255,255,255))
        white.alpha_composite(image if isinstance(image,Image.Image)
                              else Image.fromarray(image,"RGBA"))
        return np.asarray(white.convert("RGB")).astype(np.int16)
    # Native PSD is white-backed and independent parts can be transparent.
    # Compare *visible RGB* on the SAME white background, not unassociated
    # RGB bytes in transparent pixels (which produced a false MAE ~162).
    expected=over_white(canonical)
    candidates=[]
    for order_name,items in (("source_sequence",layers),("reverse_sequence",list(reversed(layers)))):
        preview=np.zeros((SIZE,SIZE,4),np.uint8)
        for _name,arr,_role in items:compose_rgba(preview,arr)
        visible=over_white(preview)
        from_white=np.array([255,255,255],dtype=np.int16)
        mask=(np.max(np.abs(expected-from_white),axis=2)>15)|(
            np.max(np.abs(visible-from_white),axis=2)>15)
        mae=float(np.abs(expected-visible)[mask].mean())
        candidates.append((mae,order_name,items,preview))
    mae,chosen_order,layers,layer_comp=min(candidates,key=lambda x:x[0])
    Image.fromarray(layer_comp,"RGBA").save(out/"layer_composite.png")
    print("CORE007_DRAW_ORDER_CHECK",json.dumps({
        "selected":chosen_order,
        "candidate_maes":{x[1]:x[0] for x in candidates},
        "best_mae":mae
    }))
    # A failure MUST include actual source-vs-layer images for inspection,
    # because numerical MAE alone cannot diagnose PSD clipping/blending.
    view=Image.new("RGB",(SIZE*3,SIZE),(241,242,246))
    for col,img in enumerate((canonical,candidates[0][3],candidates[1][3])):
        layer_img=Image.new("RGBA",(SIZE,SIZE),(241,242,246,255))
        layer_img.alpha_composite(Image.fromarray(img,"RGBA") if isinstance(img,np.ndarray) else img)
        view.paste(layer_img.convert("RGB"),(col*SIZE,0))
    view.thumbnail((1350,490))
    view.save(out/"composition_debug.jpg",quality=79)
    if mae>48.0:
        print("KOMA_CORE007_COMPOSE_DEBUG_BEGIN")
        for line in textwrap.wrap(base64.b64encode((out/"composition_debug.jpg").read_bytes()).decode(),120):
            print(line)
        print("KOMA_CORE007_COMPOSE_DEBUG_END")
        raise ValueError(f"FAIL_SOURCE_LAYER_COMPOSITION_PARITY: {mae:.2f}; cannot animate falsely ordered layers")
    report={
      "status":"SOURCE_PSD_LAYER_ANIMATION_DIAGNOSTIC",
      "actual_source":"Inochi2D official tutorial Aka layered PSD, 62 leaf layers",
      "copyright":"Aka, artist and rigger seagetch, CC BY 4.0",
      "source_psd_size":list(size),"working_crop":box,
      "render_size":[SIZE,SIZE],"active_layers":len(layers),
      "flattened_vs_independent_layer_composite_subject_rgb_mae":mae,
      "source_draw_order":chosen_order,
      "native_inx_parameter_curves_used":False,
      "native_inx_mesh_weights_used":False,
      "original_front_exactness":"SOURCE_FRAME_EXACT_ONLY; off-angle is approximated",
      "real_side_hidden_art":"MISSING",
      "surface_kind":"SHALLOW_2D_FRONT_CYLINDER_WITH_PER_LAYER_DEPTH",
      "anime_quality":"NOT_YET_ACCEPTED"
    }
    (out/"layer_roles.json").write_text(json.dumps({
       "roles":[{"name":n,"baseDepth":r[0],"curvature":r[1]} for n,_,r in layers],
       "rest_artifact_kind":"PSD_LAYERS"}
       ,indent=2,ensure_ascii=False)+"\n")
    # First/last are zero yaw. Two interpolation hypotheses use identical
    # source layers, not a rendered pre-existing 3D character.
    frames=36
    headings={"flat":[],"curved":[]}
    for kind in headings:
        folder=out/kind;folder.mkdir(exist_ok=True)
        for i in range(frames):
            yaw=34*math.sin(math.pi*i/(frames-1))
            if abs(yaw)<0.0001:
                candidate=np.asarray(canonical).copy()
            else:
                candidate=np.zeros((SIZE,SIZE,4),np.uint8)
                for name,arr,role in layers:
                    warped=remap_layer(arr,yaw,kind,role)
                    compose_rgba(candidate,warped)
            base=Image.new("RGBA",(SIZE,SIZE),BG+(255,))
            base.alpha_composite(Image.fromarray(candidate,"RGBA"))
            frame=base.convert("RGB")
            # Not text over the original art. Video labels go in an external
            # top caption in the contact sheet to avoid visual cheating.
            frame.save(folder/f"{i:04d}.png")
            if i in (0,9,18,27,35):
                headings[kind].append(frame)
    sheet=Image.new("RGB",(SIZE*5,SIZE*3),BG)
    src_can=Image.new("RGBA",(SIZE,SIZE),BG+(255,))
    src_can.alpha_composite(canonical)
    for col in range(5):sheet.paste(src_can.convert("RGB"),(col*SIZE,0))
    for row,kind in enumerate(("flat","curved"),1):
        for col,i in enumerate((0,9,18,27,35)):
            sheet.paste(Image.open(out/kind/f"{i:04d}.png").convert("RGB"),
                        (SIZE*col,SIZE*row))
    sheet.save(out/"contact.png")
    view=sheet.copy();view.thumbnail((1880,1130))
    view.save(out/"contact_preview.jpg",quality=85,optimize=True)
    report["frames_per_video"]=frames
    (out/"render.json").write_text(json.dumps(report,indent=2)+"\n")
    print("CORE007_REAL_ANIME_RENDER",json.dumps(report))
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--psd",required=True,type=Path)
    a.add_argument("--out",required=True,type=Path)
    args=a.parse_args()
    run(args.psd,args.out)
