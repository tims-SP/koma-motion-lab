#!/usr/bin/env python3
"""P15-39 reversible source-pixel face-occlusion candidate and close-up HTML review."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from p15_32_mesh_vdd import read,write,over

R=Path(__file__).resolve().parents[1]
P=R/'private-assets'
BASE=P/'p15-38-p0-registered-arc'
OUT=P/'exports/p15-39-occlusion-review'
QA=R/'evidence/p15-39-depth-review-qa.json'
AUD=json.loads((R/'evidence/p15-39-source-occlusion-audit.json').read_text())
ROLES=['body.reference','hair.back','face.skin','ear.far','ear.near','hair.side','eye.far','eye.near','nose','mouth','hair.front','hair.ahoge','hair.clip.cross_gold']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def hide_far_eye(yaw,eye,skin,nose,hair):
    # Explicit face-surface occluder: face skin covers the leftward slice
    # of the *source* far eye, with yaw-driven boundary. This never fabricates
    # hidden pixels, and does not fade the entire eye layer.
    e=eye[:,:,3].astype(np.float32)/255
    coords=np.where(e>.05)
    if len(coords[0])<5:return eye.copy(),np.zeros_like(eye),0
    left,right=coords[1].min(),coords[1].max()
    t=np.clip((yaw-45.)/20.,0,1)
    t=t*t*(3-2*t)
    edge=left+(right-left)*(.06+.83*t)
    xx=np.arange(eye.shape[1])[None,:]
    # Soft boundary is only 1.4 native pixels wide, not a global opacity fade.
    boundary=1/(1+np.exp(np.clip((xx-edge)/1.4,-60,60)))
    cover=np.clip(boundary*(skin[:,:,3].astype(np.float32)/255),0,1)
    # Nose and bangs remain independent painter-order occluders.
    shown=eye.copy();hidden=eye.copy()
    shown[:,:,3]=np.uint8(np.rint(e*(1-cover)*255))
    hidden[:,:,3]=np.uint8(np.rint(e*cover*255))
    return shown,hidden,float(edge)

def annotate_zoom(source,candidate,angle):
    # Image cutout is a faithful nearest-source RGB crop; zoom is for inspection.
    s=Image.fromarray(source,'RGBA');c=Image.fromarray(candidate,'RGBA')
    crop=(235,75,410,270)
    s=s.crop(crop).resize((525,585),Image.Resampling.NEAREST)
    c=c.crop(crop).resize((525,585),Image.Resampling.NEAREST)
    board=Image.new('RGBA',(1050,620),'#d8e0e8');board.alpha_composite(s,(0,35));board.alpha_composite(c,(525,35))
    draw=ImageDraw.Draw(board);draw.text((12,9),f'{angle} source 3x',fill='#121827');draw.text((535,9),f'{angle} depth candidate 3x',fill='#121827')
    return board

OUT.mkdir(parents=True,exist_ok=True)
rows=[]
for audit in AUD['frames']:
    tag=audit['angle'];yaw=float(tag[3:].replace('p','.'))
    folder=OUT/tag;folder.mkdir(exist_ok=True)
    layers={role:read(BASE/tag/(role+'.png')) for role in ROLES}
    visible,hidden,edge=hide_far_eye(yaw,layers['eye.far'],layers['face.skin'],layers['nose'],layers['hair.front'])
    layers['eye.far']=visible
    result=np.zeros_like(visible)
    for role in ROLES:result=over(result,layers[role])
    src=read(BASE/tag/'composite-native.png')
    rgba=Image.fromarray(result,'RGBA');srcimg=Image.fromarray(src,'RGBA')
    # Outputs deliberately separate from source roles; all P15-38 bytes retained.
    srcimg.save(folder/'source.png');rgba.save(folder/'candidate.png')
    write(folder/'far-eye-visible.png',visible);write(folder/'far-eye-underpaint.png',hidden)
    diff=np.abs(src.astype(np.int16)-result.astype(np.int16));diff=np.uint8(np.clip(diff*4,0,255));diff[:,:,3]=255
    write(folder/'difference-x4.png',diff)
    annotate_zoom(src,result,yaw).save(folder/'face-zoom.png')
    changed=int(np.any(src!=result,axis=2).sum())
    priorAlpha=float(read(BASE/tag/'eye.far.png')[:,:,3].sum())
    retainedAlpha=float(visible[:,:,3].sum())
    rows.append({'tag':tag,'angle':yaw,'sourceSHA256':sha(BASE/tag/'composite-native.png'),
      'candidateSHA256':sha(folder/'candidate.png'),'changedPixels':changed,
      'farEyeSourceAlpha':priorAlpha,'farEyeVisibleAlpha':retainedAlpha,
      'faceEdgeX443':round(edge,3),'sourceLayersPreserved':True,
      'independentHiddenPaint':False,'artisticallyApproved':False})

html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-39 · P0 原画局部深度审查</title><style>
:root{color-scheme:dark;font:15px/1.5 system-ui;background:#14202b;color:#eef4fc}body{max-width:1400px;margin:0 auto;padding:18px}h1{font-size:24px}p{color:#bbcddd}button{background:#30465e;color:white;border:1px solid #7890aa;border-radius:6px;padding:7px 11px;cursor:pointer}button[aria-pressed=true]{background:#5472a4}input[type=range]{width:100%;accent-color:#92b1eb}section{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}article{background:#23364a;border:1px solid #435771;padding:10px;min-width:0}h3{margin:0 0 6px;font-size:16px}img{display:block;max-width:100%;width:100%;height:auto;background:repeating-conic-gradient(#d3dce6 0 25%,#f2f5f9 0 50%) 50%/20px 20px}small{color:#b1c7e0}@media(max-width:700px){section{grid-template-columns:1fr}}</style><h1>P15-39 · 45°–65° 遮挡与原画审查</h1><p>左侧为 P15-38 原始画面，右侧为基于面部皮肤 Alpha 和头部转角的远眼深度遮挡候选。原眼隐藏像素独立保存；发夹目前保留原始笔触与位置供对照。图层可复查，候选不代表正式原画验收。</p><nav><button id="prev">上一角</button> <b id="angle"></b> <button id="next">下一角</button><input id="slider" type="range" min="0" max="12" value="0" step="1"><button data-mode="whole" aria-pressed="true">整体</button> <button data-mode="zoom">脸部放大</button> <button data-mode="layers">眼睛与隐藏笔触</button></nav><p id="metrics"></p><section id="gallery"></section><p id="status" role="status"></p><script>
const data=__ROWS__;let index=0,mode='whole';const $=x=>document.getElementById(x);
const frames={whole:[['source.png','P15-38 原始画面'],['candidate.png','P15-39 局部遮挡候选']],zoom:[['face-zoom.png','来源与候选的同区近邻放大'],['difference-x4.png','像素差异 ×4']],layers:[['far-eye-visible.png','面部遮挡后的远眼'],['far-eye-underpaint.png','保留的隐藏像素（原眼来源）']]};
async function show(i=index,m=mode){index=Math.max(0,Math.min(data.length-1,i));mode=m;let r=data[index];$('angle').textContent=r.angle+'°';$('slider').value=index;$('metrics').textContent='改动像素 '+r.changedPixels+' · 远眼来源 Alpha '+r.farEyeSourceAlpha.toFixed(0)+' · 可见 Alpha '+r.farEyeVisibleAlpha.toFixed(0)+' · 面部遮挡边界 X '+r.faceEdgeX443;document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));let g=$('gallery');g.replaceChildren();let imgs=frames[mode].map(([p,title])=>{let a=document.createElement('article'),h=document.createElement('h3'),im=document.createElement('img');h.textContent=title;im.alt=title;im.src=r.tag+'/'+p;a.append(h,im);g.append(a);return im});let v=await Promise.allSettled(imgs.map(im=>im.decode()));$('status').textContent=v.every(x=>x.status==='fulfilled')?'两张图像均已载入；需逐帧人工评价面部、发丝与发夹物理关系':'图像加载异常';return v.every(x=>x.status==='fulfilled')}
$('prev').onclick=()=>show(index-1);$('next').onclick=()=>show(index+1);$('slider').oninput=e=>show(+e.target.value);document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>show(index,b.dataset.mode));window.__KOMA_P15_39={show,rows:data};show(0);
</script>'''
(OUT/'index.html').write_text(html.replace('__ROWS__',json.dumps(rows)),encoding='utf-8')
report={'schema':'KOMA-P15-39-DEPTH-REVIEW-V1','characterId':'p0_character_001','frames':rows,'sourceAuditSHA256':sha(R/'evidence/p15-39-source-occlusion-audit.json'),'reviewIndex':'private-assets/exports/p15-39-occlusion-review/index.html','browserChecked':False,'heroVerified':False,'formalArtistApproval':False}
QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'frames':len(rows),'changedPixels':[r['changedPixels'] for r in rows],'review':report['reviewIndex']}))
