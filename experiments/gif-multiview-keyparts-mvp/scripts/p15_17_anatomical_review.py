#!/usr/bin/env python3
import json,hashlib,shutil,zipfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent.parent
P=R/'private-assets'
SRC=P/'p15-17-anatomical-5frame'
QA=json.loads((SRC/'qa.json').read_text())
names=['yaw55','yaw57p5','yaw60','yaw62p5','yaw65']
frames=[];masks=[]
for name in names:
 path=SRC/(name+'.png')
 im=Image.open(path).convert('RGBA')
 a=np.asarray(im)[:,:,3]>16;masks.append(a)
 frames.append({'angle':float(name[3:].replace('p','.')),'path':name+'.png',
  'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':list(im.size),
  'visiblePixels':int(a.sum())})
pairs=[]
for i in range(4):
 a,b=masks[i],masks[i+1]
 pairs.append({'from':frames[i]['angle'],'to':frames[i+1]['angle'],
  'alphaIoU':round(float(np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b))),5)})
OUT=P/'exports/p15-17-anatomical-review';OUT.mkdir(parents=True,exist_ok=True)
cards=[]
for f in frames:
 shutil.copy2(SRC/f['path'],OUT/f['path'])
 cards.append(f)
contact=Image.new('RGB',(5*256,300),(30,35,45))
for i,f in enumerate(frames):
 im=Image.open(OUT/f['path']).convert('RGBA').resize((256,256))
 bg=Image.new('RGBA',(256,256),(55,60,68,255));bg.alpha_composite(im)
 contact.paste(bg.convert('RGB'),(i*256,0))
 ImageDraw.Draw(contact).text((i*256+8,266),f"{f['angle']:g} deg / {pairs[i]['alphaIoU'] if i<4 else ''}",fill='white')
contact.save(OUT/'contact.png')
report={'schema':'KOMA-P15-17-ANATOMICAL-REVIEW-V1','characterId':'p0_character_001',
 'sourceQA':str((SRC/'qa.json').relative_to(P)),
 'sourceQASHA256':hashlib.sha256((SRC/'qa.json').read_bytes()).hexdigest(),
 'renderer':'P12 original P0 RGBA ArtMesh + P5 anatomical anchors + P11 real profile PSD',
 'mode':'anatomy','frames':cards,'adjacentAlphaIoU':pairs,
 'registeredValidPairs':QA.get('registeredValidPairs'),
 'profilePSDVerified':True,'approvedIndependentPaintings':0,
 'approvedHiddenUnderpainting':0,'visualAcceptance':'PENDING',
 'interpretation':'Engineering diagnostic only; no new source paintings or hidden underpaint authored'}
(OUT/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-17 原始 ArtMesh 解剖对照</title>
<style>body{background:#151a23;color:#eaf0f7;font:16px system-ui;margin:0;padding:20px}main{max-width:1200px;margin:auto}.grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}.card{background:#222b38;border:1px solid #445164;border-radius:10px;padding:10px;min-width:0}img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4b5664 0 25%,#242c37 0 50%) 50%/20px 20px}small{color:#bac4d2}@media(max-width:800px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}</style>
<main><h1>P15-17 · 原始 ArtMesh 解剖约束对照</h1><p>来源为批准的 P0 原始部件，不是新的 AI 代理绘画。用于比较部件定位和遮挡。没有通过隐藏补绘或艺术质量验收。</p><section class="grid" id="frames"></section><h2>相邻轮廓 Alpha IoU</h2><pre id="metrics"></pre></main>
<script>const frames=__FRAMES__,pairs=__PAIRS__;const root=document.querySelector('#frames');for(const f of frames){const c=document.createElement('article');c.className='card';const h=document.createElement('h3');h.textContent=f.angle+'°';const im=document.createElement('img');im.src=f.path;im.alt=f.angle+' degree';const s=document.createElement('small');s.textContent='Alpha pixels: '+f.visiblePixels;c.append(h,im,s);root.append(c)}document.querySelector('#metrics').textContent=pairs.map(p=>p.from+'° → '+p.to+'° : '+p.alphaIoU).join('\n');</script></main></html>'''
(OUT/'index.html').write_text(html.replace('__FRAMES__',json.dumps(cards)).replace('__PAIRS__',json.dumps(pairs)))
bundle=P/'exports/p15-17-anatomical-review.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(OUT.iterdir()):
  if f.is_file():z.write(f,f.name)
with zipfile.ZipFile(bundle) as z:assert z.testzip() is None;entries=len(z.namelist())
print(json.dumps({'frames':len(frames),'pairs':pairs,'zipBytes':bundle.stat().st_size,'entries':entries,'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest()},ensure_ascii=False))
