#!/usr/bin/env python3
import json,hashlib,shutil,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
names=['yaw55','yaw57p5','yaw60','yaw62p5','yaw65']
modes={'anatomy':P/'p15-17-anatomical-5frame','anatomy-strokes':P/'p15-18-anatomy-strokes-5frame','stroke-wide':P/'p15-18-stroke-wide-5frame'}
OUT=P/'exports/p15-18-mode-comparison';OUT.mkdir(parents=True,exist_ok=True)
data={}
for mode,folder in modes.items():
 frames=[];masks=[]
 for name in names:
  src=folder/(name+'.png');im=Image.open(src).convert('RGBA')
  a=np.asarray(im)[:,:,3]>16;masks.append(a)
  dst=OUT/(mode+'-'+name+'.png');shutil.copy2(src,dst)
  frames.append({'angle':float(name[3:].replace('p','.')),'path':dst.name,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'visiblePixels':int(a.sum())})
 pairs=[]
 for i in range(4):
  a,b=masks[i],masks[i+1]
  pairs.append(round(float(np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b))),5))
 qa=json.loads((folder/'qa.json').read_text())
 data[mode]={'frames':frames,'pairs':pairs,'registeredPairs':len(qa['pairDiagnostics']),
  'strokeAnchorsUsed':sum(qa.get('localStrokeCandidatesUsed',{}).values())}
report={'schema':'KOMA-P15-18-MODE-COMPARISON-V1','characterId':'p0_character_001',
 'modes':data,'interpretation':'Alpha IoU is only silhouette continuity. P10 stroke anchors are hypotheses and need texture/art QA.',
 'artisticAcceptance':False,'approvedIndependentPaintings':0,'approvedHiddenUnderpainting':0}
(OUT/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>P15-18 VDD 模式对照</title>
<style>body{margin:0;padding:18px;background:#151b25;color:#eaf0f7;font:15px system-ui}main{max-width:1300px;margin:auto}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.card{border:1px solid #435064;background:#222c3a;border-radius:9px;padding:10px;min-width:0}.frames{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:5px}img{width:100%;aspect-ratio:1;object-fit:contain;background:#3a4350}small{color:#bbc5d2}@media(max-width:800px){.grid{grid-template-columns:1fr}.frames{grid-template-columns:repeat(3,minmax(0,1fr))}}</style>
<main><h1>P15-18 · anatomy vs anatomy-strokes</h1><p>同一组原始 P0 ArtMesh、同一 P5 锚点、P11 profile PSD。第二组额外加入 P10 高置信度笔画假设；不是新增原画。</p><div class="grid" id="modes"></div><p>Alpha IoU 只代表轮廓覆盖连续性，不代表纹理和艺术质量。隐藏补绘与独立原画仍未签收。</p></main>
<script>const D=__DATA__,root=document.querySelector('#modes');for(const [name,m] of Object.entries(D.modes)){const c=document.createElement('section');c.className='card';const h=document.createElement('h2');h.textContent=name+' · stroke anchors '+m.strokeAnchorsUsed;const g=document.createElement('div');g.className='frames';m.frames.forEach(f=>{const d=document.createElement('div'),im=document.createElement('img'),s=document.createElement('small');im.src=f.path;im.alt=name+' '+f.angle;s.textContent=f.angle+'°';d.append(im,s);g.append(d)});const p=document.createElement('p');p.textContent='相邻 Alpha IoU: '+m.pairs.join(' / ');c.append(h,g,p);root.append(c)}</script></main></html>'''
(OUT/'index.html').write_text(html.replace('__DATA__',json.dumps(report)))
bundle=P/'exports/p15-18-mode-comparison.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(OUT.iterdir()):
  if f.is_file():z.write(f,f.name)
with zipfile.ZipFile(bundle) as z:assert z.testzip() is None;entries=len(z.namelist())
print(json.dumps({'modes':{k:v['pairs'] for k,v in data.items()},'anchors':data['anatomy-strokes']['strokeAnchorsUsed'],'zipBytes':bundle.stat().st_size,'entries':entries,'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest()},ensure_ascii=False))
