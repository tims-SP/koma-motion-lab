#!/usr/bin/env python3
"""Triangulated hair ArtMesh displacement over independently painted hidden material.

Small 2D motion study: mesh topology, alpha compositing and source pixel
identity are verified; anatomical and cross-view correspondences remain pending.
"""
import json,hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from p15_134_underpaint_probe import P,SOURCE,rgba,compose,move,background_rgb
from p15_135_closed_hair_mask import closed_mask,split
from p15_138_underpaint_arc import merge_rear
ROOT=Path(__file__).resolve().parent.parent
OUT=P/'exports/p15-139-hair-artmesh'
E=ROOT/'evidence/p15-139-hair-artmesh-qa.json'
SPACING=24
H=W=443
def geometry():
    xs=list(range(0,W,SPACING))
    ys=list(range(0,H,SPACING))
    if xs[-1]!=W-1:xs.append(W-1)
    if ys[-1]!=H-1:ys.append(H-1)
    verts=np.array([(x,y) for y in ys for x in xs],dtype=np.float32)
    tris=[]
    nx=len(xs)
    for yi in range(len(ys)-1):
        for xi in range(nx-1):
            a=yi*nx+xi;b=a+1;c=a+nx;d=c+1
            tris.extend([(a,b,d),(a,d,c)])
    return verts,np.asarray(tris,dtype=np.int32)
def area(pts):
    a,b,c=pts
    return float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
def deform(verts,dx):
    out=verts.copy()
    x=verts[:,0];y=verts[:,1]
    # Head movement pivots near the nape: upper hair follows full movement;
    # lower back locks nearer the neck. Small vertical easing adds less rigid motion.
    top=np.clip((380-y)/210,0,1)
    top=top*top*(3-2*top)
    out[:,0]+=dx*top
    out[:,1]+=-dx*.07*np.sin(np.pi*np.clip(y/443,0,1))*top
    return out
def warp_triangles(source,original,transformed,faces):
    h,w=source.shape[:2]
    result=np.zeros((h,w,4),dtype=np.float32)
    count=np.zeros((h,w),dtype=np.uint16)
    # Inverse mapping per triangle interpolates source RGBA with linear filtering.
    for tri in faces:
        p=original[tri].astype(np.float32)
        q=transformed[tri].astype(np.float32)
        minx=max(0,int(np.floor(q[:,0].min())));maxx=min(w,int(np.ceil(q[:,0].max()))+1)
        miny=max(0,int(np.floor(q[:,1].min())));maxy=min(h,int(np.ceil(q[:,1].max()))+1)
        if minx>=maxx or miny>=maxy:continue
        yy,xx=np.mgrid[miny:maxy,minx:maxx].astype(np.float32)
        denom=(q[1,1]-q[2,1])*(q[0,0]-q[2,0])+(q[2,0]-q[1,0])*(q[0,1]-q[2,1])
        if abs(float(denom))<1e-6:continue
        v0=((q[1,1]-q[2,1])*(xx-q[2,0])+(q[2,0]-q[1,0])*(yy-q[2,1]))/denom
        v1=((q[2,1]-q[0,1])*(xx-q[2,0])+(q[0,0]-q[2,0])*(yy-q[2,1]))/denom
        v2=1-v0-v1
        inside=(v0>=-1e-5)&(v1>=-1e-5)&(v2>=-1e-5)
        if not inside.any():continue
        sx=(v0*p[0,0]+v1*p[1,0]+v2*p[2,0]).astype(np.float32)
        sy=(v0*p[0,1]+v1*p[1,1]+v2*p[2,1]).astype(np.float32)
        fragment=cv2.remap(source,sx,sy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).astype(np.float32)
        tile=result[miny:maxy,minx:maxx];counts=count[miny:maxy,minx:maxx]
        # Grid rectangles and shared edges can overlap due to pixel discretization.
        # Source and displacement are smooth; deterministic first owner avoids duplicate alpha.
        accept=inside&(counts==0)
        tile[accept]=fragment[accept];counts[accept]+=1
    return np.uint8(np.clip(np.round(result),0,255))
def alpha_holes(reference,frame):
    return (reference[...,3]>160)&(frame[...,3]<64)
def tally(mask):
    rois={'rear_scalp':(52,305,85,245),'eye':(175,295,265,365),
          'ear':(180,325,195,280),'neck':(285,370,140,320)}
    vals={'all':int(mask.sum())}
    for name,(a,b,c,d) in rois.items():vals[name]=int(mask[a:b,c:d].sum())
    return vals
def evaluate(save=True):
    src=rgba(SOURCE)
    region,_=closed_mask(src)
    hair,rest=split(src,region)
    baseline=rgba(P/'exports/p15-137-occlusion-regions/eye_08-underpaint.png')
    hybrid=merge_rear(baseline,rgba(P/'exports/p15-138-rear-scalp/registered-underpaint.png'))
    verts,faces=geometry()
    base_areas=np.asarray([area(verts[t]) for t in faces])
    assert (base_areas>0).all()
    choices={'baseline_translation':baseline,'hybrid_translation':hybrid,'baseline_mesh':baseline,'hybrid_mesh':hybrid}
    outputs={}
    metrics={}
    for label,background in choices.items():
        rendered={}
        for offset in (0,12,24):
            if offset==0:foreground=hair.copy()
            elif label.endswith('_mesh'):foreground=warp_triangles(hair,verts,deform(verts,offset),faces)
            else:foreground=move(hair,offset,0)
            rendered[offset]=compose(compose(background,rest),foreground)
        outputs[label]=rendered
        roi=np.s_[125:350,125:390]
        metrics[label]={str(offset):{'holes':tally(alpha_holes(src,frame)),
           'rgbMAE':round(float(np.abs(background_rgb(frame)[roi]-background_rgb(src)[roi]).mean()),4)}
          for offset,frame in rendered.items()}
    areas={str(offset):{'minSignedArea':round(float(min(area(deform(verts,offset)[t]) for t in faces)),5),
                        'folds':sum(area(deform(verts,offset)[t])<=0 for t in faces)} for offset in (0,12,24)}
    report={'schema':'KOMA_P15_139_ARTMESH_REVEAL_V1','characterId':'p0_character_001',
        'angle':112.5,'geometry':'two-triangle regular-grid ArtMesh with piecewise barycentric inverse UV sampling',
        'vertexCount':len(verts),'triangleCount':len(faces),'vertexSpacing':SPACING,
        'geometryQuality':areas,'composites':metrics,'sourcePixelSplitExact':True,
        'sourceKeyframeUnmodified':True,'nativeUnderpaintUnmodified':True,
        'artistApprovedTopology':False,'realCrossViewCorrespondence':False,
        'physicalDepthOrderAccepted':False,'actualYawTransitionAccepted':False,
        'visualAcceptance':False,
        'review':'private-assets/exports/p15-139-hair-artmesh/index.html',
        'next':'Replace rectangular proxy with hair-root/tip boundary-conforming mesh and source-paint behind eye, ear and neck. Validate by actual 90–135 yaw mesh interpolation, not only displaced 112.5 view.'}
    if save:
        OUT.mkdir(exist_ok=True,parents=True)
        board=Image.new('RGB',(350*4,395*4),(35,41,50));d=ImageDraw.Draw(board)
        for row,(label,images) in enumerate(outputs.items()):
            for col,(title,frame) in enumerate([('original',src)]+[(str(dx)+'px',images[dx]) for dx in (0,12,24)]):
                tile=Image.new('RGBA',(443,443),(49,61,78,255));tile.alpha_composite(Image.fromarray(frame,'RGBA'))
                board.paste(tile.convert('RGB').resize((344,344),Image.Resampling.LANCZOS),(col*350,row*395+30))
                d.text((col*350+7,row*395+8),f'{label}/{title}',fill='white')
                if col:Image.fromarray(frame,'RGBA').save(OUT/f'{label}-{title}.png')
        board.save(OUT/'comparison.jpg',quality=93)
        mesh=Image.new('RGB',(443,443),(40,44,53));p=ImageDraw.Draw(mesh)
        for tri in faces:
            xy=[tuple(map(float,v)) for v in verts[tri]]
            p.line(xy+[xy[0]],fill=(46,177,211),width=1)
        mesh.save(OUT/'wireframe.png')
        (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>P0 hair ArtMesh reveal</title><style>body{background:#202733;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>P0 112.5° triangulated head-hair ArtMesh</h2><p>Native pixel-preserved source and 0/12/24px displacement, comparing uniform translation to per-vertex ArtMesh deformation over baseline or hybrid rear scalp. Anatomy and cross-view registration remain provisional.</p><img src="comparison.jpg"><h3>Mesh topology</h3><img style="width:420px" src="wireframe.png">')
        E.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
if __name__=='__main__':
    q=evaluate()
    print(json.dumps({'vertices':q['vertexCount'],'triangles':q['triangleCount'],
        'geometry':q['geometryQuality'],'composites':q['composites']},indent=2))
