#!/usr/bin/env python3
"""P15-40: anatomical far-eye silhouette trim and anchored clip placement trial.

Pixel-authentic edits only. Original P15-38 RGBA layers remain unchanged.
"""
from pathlib import Path
import hashlib,json
import cv2
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import read,write,over
ROLES=["body.reference","hair.back","face.skin","ear.far","ear.near","hair.side","eye.far","eye.near","nose","mouth","hair.front","hair.ahoge","hair.clip.cross_gold"]

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'private-assets/p15-38-p0-registered-arc'
OUT=ROOT/'private-assets/exports/p15-40-profile-review'
QA=ROOT/'evidence/p15-40-profile-qa.json'
AUD=json.loads((ROOT/'evidence/p15-39-source-occlusion-audit.json').read_text())
# Progressive anatomical profile limits, not image-wide opacity modulation.
# Existing pixels to the right of a moving nose-facing silhouette survive.
GEOMETRIC_SCALES=[1.0]*9+[.8,.6,.35,0.0]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def limit_eye(a,scale):
    """Keep complete painted eye features, shrink around outer eye corner."""
    original=a[:,:,3]
    ys,xs=np.where(original>13)
    if not len(xs):return a.copy(),a.copy(),0
    anchor_x=float(xs.max());anchor_y=float(np.average(ys,weights=original[ys,xs]))
    out=a.copy()
    if scale==0:
        out[:]=0
    elif scale<1:
        dx=anchor_x*(1-scale)
        dy=anchor_y*(1-scale)
        m=np.float32([[scale,0,dx],[0,scale,dy]])
        out=cv2.warpAffine(a,m,(a.shape[1],a.shape[0]),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
    # Full source underpaint is preserved independently, because geometric
    # contraction changes coordinates and is not a per-pixel alpha partition.
    return out,a.copy(),round(anchor_x,3)

def contact(clip,hair):
    c=clip[:,:,3].astype(float)/255;h=hair[:,:,3].astype(float)/255
    return float((c*h).sum()/max(1,c.sum()))

def move_clip(clip,hair,last_offset):
    # Limited anchored search: retain source stroke, nudge only 0..3px
    # in either dimension, and penalize frame-to-frame motion jitter.
    baseline=contact(clip,hair);choice=clip;offset=(0,0);best=baseline
    for dx in range(-3,4):
      for dy in range(-3,4):
        if dx==0 and dy==0:continue
        cand=cv2.warpAffine(clip,np.float32([[1,0,dx],[0,1,dy]]),(clip.shape[1],clip.shape[0]),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
        c=contact(cand,hair)
        score=c-.003*(abs(dx)+abs(dy))-.002*(abs(dx-last_offset[0])+abs(dy-last_offset[1]))
        if score>best:best=score;choice=cand;offset=(dx,dy)
    return choice,offset,baseline,contact(choice,hair)

def main():
    OUT.mkdir(parents=True,exist_ok=True);records=[];last=(0,0)
    for i,row in enumerate(AUD['frames']):
      tag=row['angle'];angle=float(tag[3:].replace('p','.'))
      layers={role:read(SRC/tag/(role+'.png')) for role in ROLES}
      visible,hidden,edge=limit_eye(layers['eye.far'],GEOMETRIC_SCALES[i]);layers['eye.far']=visible
      clip,offset,before,after=move_clip(layers['hair.clip.cross_gold'],layers['hair.front'],last)
      layers['hair.clip.cross_gold']=clip;last=offset
      composite=np.zeros_like(visible)
      for role in ROLES:composite=over(composite,layers[role])
      original=read(SRC/tag/'composite-native.png')
      d=OUT/tag;d.mkdir(parents=True,exist_ok=True)
      write(d/'source.png',original);write(d/'candidate.png',composite)
      write(d/'far-eye-visible.png',visible);write(d/'far-eye-underpaint.png',hidden)
      delta=np.uint8(np.clip(np.abs(composite.astype(np.int16)-original.astype(np.int16))*4,0,255));delta[:,:,3]=255
      write(d/'difference-x4.png',delta)
      src=Image.fromarray(original,'RGBA').crop((235,75,410,270)).resize((525,585),Image.Resampling.NEAREST)
      dst=Image.fromarray(composite,'RGBA').crop((235,75,410,270)).resize((525,585),Image.Resampling.NEAREST)
      board=Image.new('RGBA',(1050,620),'#d8e0e8');board.alpha_composite(src,(0,35));board.alpha_composite(dst,(525,35));board.save(d/'face-zoom.png')
      eye_original=read(SRC/tag/'eye.far.png')[:,:,3].astype('int16')
      retained=float(visible[:,:,3].sum()/max(1,eye_original.sum()))
      records.append({'tag':tag,'angle':angle,'sourceSHA256':sha(SRC/tag/'composite-native.png'),
       'candidateSHA256':sha(d/'candidate.png'),'sourceEyeSHA256':sha(SRC/tag/'eye.far.png'),
       'changedPixels':int(np.any(composite!=original,axis=2).sum()),
       'farEyeSourceAlpha':float(eye_original.sum()),'farEyeVisibleAlpha':float(visible[:,:,3].sum()),
       'eyeVisibleRatio':round(retained,6),'eyeOuterAnchorX443':edge,
       'clipShiftXY':list(offset),'clipContactBefore':round(before,6),'clipContactAfter':round(after,6),
       'sourceLayersPreserved':True,'independentHiddenPaint':False,'artisticallyApproved':False})
    # reuse the already-validated UI shell, keep separate output and tool identity
    html=(ROOT/'private-assets/exports/p15-39-occlusion-review/index.html').read_text()
    html=html.replace('P15-39','P15-40').replace('window.__KOMA_P15_39','window.__KOMA_P15_40')
    html=html.replace('const data='+json.dumps(json.loads((ROOT/'evidence/p15-39-depth-review-qa.json').read_text())['frames']), 'const data='+json.dumps(records))
    # robust replace independently of original JSON serialization formatting
    start=html.index('const data=');end=html.index(';let index=',start)
    html=html[:start]+'const data='+json.dumps(records)+html[end:]
    html=html.replace('远眼深度遮挡候选','远眼完整形状收缩与发夹微位移候选').replace('发夹目前保留原始笔触与位置供对照','发夹保留原始笔触并采用最大 3 像素的局部接触微调')
    html=html.replace('r.faceEdgeX443','r.eyeOuterAnchorX443')
    (OUT/'index.html').write_text(html)
    ratios=[r['eyeVisibleRatio'] for r in records]
    if any(b>a+.002 for a,b in zip(ratios,ratios[1:])):raise AssertionError('Far-eye silhouette reappears')
    if any(r['clipContactAfter']+1e-7<r['clipContactBefore'] for r in records):raise AssertionError('Clip attachment regressed')
    report={'schema':'KOMA-P15-40-PROFILE-VISIBILITY-V1','characterId':'p0_character_001',
      'frames':records,'geometricScales':GEOMETRIC_SCALES,'browserChecked':False,'artisticApproval':False,
      'sourceP15_39AuditSHA256':sha(ROOT/'evidence/p15-39-source-occlusion-audit.json'),
      'geometryMethod':'complete source eye affine geometry contraction toward outer eye corner; independent hair-contact clip translation'}
    QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'frames':len(records),'eyeRatios':ratios,'clipShift':[r['clipShiftXY'] for r in records],
      'clipContactGain':[round(r['clipContactAfter']-r['clipContactBefore'],4) for r in records]}))
if __name__=='__main__':main()
