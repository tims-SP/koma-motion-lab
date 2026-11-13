#!/usr/bin/env python3
"""Rear-arc source-part VDD candidate: mask-based part ownership and per-part anchors."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
import cv2
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from p15_120_back_semantic_candidates import segment as existing_segment
from p15_121_rear_arc_render import ANGLES,KEYS,load,sha
from flow_render import get_flow,warp_float
P=ROOT/'private-assets'; OUT=P/'exports/p15-123-part-vdd'; E=ROOT/'evidence/p15-123-part-vdd-qa.json'
PARTS=('garment.visible','skin.visible','hair.visible')

def layers(angle):
    src=load()[angle]
    if angle in (135,180):
        root=P/f'exports/p15-120-back-semantic-candidates/yaw{angle:03}'
        return {part:np.array(Image.open(root/(part+'.png')).convert('RGBA')) for part in PARTS}
    # Separate 90° keyframe for the same three visibility roles; preserves original pixels.
    r,g,b=[src[...,i].astype(np.int16) for i in (0,1,2)]
    visible=src[...,3]>0
    y,x=np.indices(visible.shape)
    skin=(r>g+15)&(g>b+4)&(r>125)&(g>90)&(x>200)&(y>110)&(y<345)&visible
    seed=(r>g+12)&(b>g+4)&(r>85)&(b>75)&visible&(y<360)
    closed=cv2.morphologyEx(seed.astype('uint8'),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(17,17)))
    n,labels,stats,_=cv2.connectedComponentsWithStats(closed,8)
    silhouette=np.zeros_like(closed)
    contours=[]
    for i in range(1,n):
        px,py,w,h,area=stats[i]
        if area>100 and py<230: contours.extend(cv2.findContours((labels==i).astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0])
    cv2.drawContours(silhouette,contours,-1,255,-1)
    hair=(silhouette>0)&visible&~skin
    masks={'hair.visible':hair,'skin.visible':skin,'garment.visible':visible&~(hair|skin)}
    out={}
    for k,m in masks.items():
        out[k]=src.copy();out[k][~m]=0
    # Opaque visible partition is exact even if semantic classification is imperfect.
    rebuild=src.copy();rebuild[visible]=0
    for layer in out.values():rebuild+=layer
    assert np.array_equal(rebuild,src)
    return out

def centroid(a):
    pix=a[...,3].astype('float32');total=pix.sum()
    if total<1:return [0.,0.]
    yy,xx=np.indices(pix.shape)
    return [round(float((xx*pix).sum()/total),3),round(float((yy*pix).sum()/total),3)]

def warp_owned(src,flow,dist,grid):
    af=src.astype(np.float32)/255
    prem=np.concatenate((af[...,:3]*af[...,3:4],af[...,3:4]),axis=2)
    warped=warp_float(prem,flow,dist,grid)
    alpha=np.clip(warped[...,3:4],0,1)
    rgb=np.clip(warped[...,:3]/np.maximum(alpha,1e-6),0,1)
    result=np.uint8(np.clip(np.concatenate((rgb,alpha),axis=2)*255,0,255))
    result[result[...,3]==0]=0
    return result

def composite(parts,shape):
    # Native visible material has no true hidden underpaint: alpha-composite by
    # a deterministic rear depth order, do not synthesize unseen cloth or scalp.
    out=Image.new('RGBA',(shape[1],shape[0]),(0,0,0,0))
    for key in PARTS:out.alpha_composite(Image.fromarray(parts[key],'RGBA'))
    return np.asarray(out).copy()

def render(save=True):
    native=load();layers_by_angle={a:layers(a) for a in KEYS}
    h,w=native[90].shape[:2]; yy,xx=np.indices((h,w),dtype=np.float32);grid=np.stack([xx,yy],axis=-1)
    flow={}
    for a,b in ((90,135),(135,180)):
        for key in PARTS:
            flow[a,b,key]=get_flow(layers_by_angle[a][key],layers_by_angle[b][key],'dis')
    rows=[];frames=[]
    for angle in ANGLES:
        if angle in native:
            result=native[angle].copy()
            by_part=layers_by_angle[angle]
            owner={k:angle for k in PARTS}
        else:
            a,b=(90,135) if angle<135 else (135,180)
            t=(angle-a)/(b-a)
            by_part={};owner={}
            for part in PARTS:
                source=a if t<.5 else b
                distance=t if source==a else 1-t
                direction=0 if source==a else 1
                by_part[part]=warp_owned(layers_by_angle[source][part],flow[a,b,part][direction],distance,grid)
                # Fade out side-face as it disappears behind hair approaching back view.
                # Per-part visibility is limited by source art, not newly inferred anatomy.
                if part=='skin.visible' and a==135 and source==135:
                    alpha_weight=min(1.,max(0.,(180-angle)/45))
                    by_part[part][...,3]=np.uint8(by_part[part][...,3].astype('float32')*alpha_weight)
                owner[part]=source
            result=composite(by_part,(h,w))
        frames.append(result)
        rows.append({'yaw':angle,'sourceOwner':owner,'layerAnchors':{k:centroid(by_part[k]) for k in PARTS}})
    def bg(x):
        al=x[...,3:4].astype('float32')/255
        return x[...,:3]*al+(1-al)*np.array([49,61,78])
    jumps=[round(float(np.abs(bg(a)-bg(b)).mean()),4) for a,b in zip(frames,frames[1:])]
    exact=all(np.array_equal(native[a],frames[ANGLES.index(a)]) for a in KEYS)
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        for angle,frame in zip(ANGLES,frames):Image.fromarray(frame,'RGBA').save(OUT/(f'yaw{angle:06.2f}'.replace('.','p')+'.png'))
        contact=Image.new('RGB',(320*5,354*2),(35,41,49));draw=ImageDraw.Draw(contact)
        targets=[90,112.5,135,157.5,180]
        for j,mode in enumerate(('p15_122_source_owned','p15_123_part_vdd')):
            for i,angle in enumerate(targets):
                if j==0:
                    p=P/'exports/p15-122-source-owned'/(f'yaw{angle:06.2f}'.replace('.','p')+'.png')
                    im=np.array(Image.open(p).convert('RGBA'))
                else: im=frames[ANGLES.index(angle)]
                tile=Image.new('RGBA',(w,h),(49,61,78,255));tile.alpha_composite(Image.fromarray(im,'RGBA'))
                contact.paste(tile.convert('RGB').resize((315,315),Image.Resampling.LANCZOS),(i*320,j*354+28))
                draw.text((i*320+8,j*354+6),f'{mode} | {angle:g}',fill='white')
        contact.save(OUT/'comparison.jpg',quality=93)
        previews=[]
        for f in frames+frames[-2:0:-1]:
            tile=Image.new('RGBA',(w,h),(49,61,78,255));tile.alpha_composite(Image.fromarray(f,'RGBA'))
            previews.append(tile.convert('RGB'))
        previews[0].save(OUT/'part-vdd-loop.gif',save_all=True,append_images=previews[1:],duration=180,loop=0,optimize=False)
        (OUT/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>P0 rear arc part VDD</title><style>body{background:#202832;color:#eee;font:16px system-ui}img{max-width:100%}</style><h2>90°–180° source-part correspondence</h2><p>Separate hair, face and garment candidate material with per-part flow and source ownership. Keyviews are pixel-exact; visible geometry is provisional and hidden surfaces require art.</p><img src="comparison.jpg"><h3>Animated diagnostic</h3><img src="part-vdd-loop.gif">''')
        qa={'schema':'KOMA_P15_123_PART_VDD_V1','characterId':'p0_character_001','sourceKeyAngles':list(KEYS),'yawSamples':ANGLES,
            'partRoles':list(PARTS),'candidateGeometry':'per-part DIS inverse flow, candidate anchors and native visibility ownership',
            'sourceViewAnchors':{str(a):{k:centroid(layers_by_angle[a][k]) for k in PARTS} for a in KEYS},
            'frames':rows,'adjacentCompositeRGBMAE':jumps,'maxAdjacentCompositeRGBMAE':max(jumps),
            'nativeKeyframesPixelExact':exact,'hiddenUnderpaintVerified':False,'physicalAnchorCorrespondenceValidated':False,
            'visualAccepted':False,'review':'private-assets/exports/p15-123-part-vdd/index.html',
            'next':'Inspect per-part distortion and owner switches, then replace heuristic boundaries with painted correspondence/underpaint.'}
        E.write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
    return {'nativeKeyframesPixelExact':exact,'maxAdjacentCompositeRGBMAE':max(jumps),'anchors':rows[0]['layerAnchors']}
if __name__=='__main__':print(json.dumps(render(),indent=2))
