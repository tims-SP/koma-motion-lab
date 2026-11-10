#!/usr/bin/env python3
"""P15-29 offline 5-angle animated-key art and mounted clip review."""
import hashlib,json,shutil,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent.parent;P=R/'private-assets'
E=json.loads((R/'evidence/p15-29-defade-bridge-qa.json').read_text())
C=json.loads((R/'evidence/p15-29-clip-mount-qa.json').read_text())
O=P/'exports/p15-29-defade-geometry-review';O.mkdir(parents=True,exist_ok=True)
for name,src in [('source-p0-eye45.png',P/E['sourceP0_45']),('source-p0-clip45.png',P/'p5-see-through/yaw045/integrated/parts/hair.clip.cross_gold.png')]:
 shutil.copy2(src,O/name)
shutil.copy2(R/'evidence/p15-29-defade-bridge-qa.json',O/'eye-qa.json')
shutil.copy2(R/'evidence/p15-29-clip-mount-qa.json',O/'clip-qa.json')
views=[]
for eye,clip in zip(E['frames'],C['frames']):
 yaw=eye['angle'];assert yaw==clip['angle']
 slug='yaw'+(str(int(yaw)) if yaw%1==0 else str(yaw).replace('.','p'))
 d=O/slug;d.mkdir(exist_ok=True)
 names=['legacy-faded','inverse-fade','bridge-proxy',
        'legacy-composite','recovered-composite','bridge-composite',
        'clip-legacy','clip-recovered','clip-hair-attached','clip-off-hair']
 for name in names:shutil.copy2(P/'p15-29-defade-bridge'/slug/(name+'.png'),d/(name+'.png'))
 views.append({'yaw':yaw,'prefix':slug,'eye':{
  'fade':eye['scheduleFactor'],'old':eye['legacyEyeMass'],'restored':eye['restoredEyeMass'],
  'visible':eye['bridgeVisibleFractionOfRestored'],
  'anchor':eye['anchors'],'changed':eye['wholeFrameChangedFromBaseline']},
  'clip':{'fade':clip['scheduleFactor'],'old':clip['legacyMass'],
  'restored':clip['recoveredMass'],'attached':clip['clipAttachedMassFraction'],
  'anchorDistance':clip['centerToAnchorPixels']}})
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-29 · 远眼恢复 / 鼻梁代理与发夹附着</title><style>
body{margin:0;padding:15px;background:#151b25;color:#e8eff9;font:14px system-ui}main{max-width:1350px;margin:auto}
h1{font-size:24px}.warn{color:#e8b785;line-height:1.5}.note{color:#b9c6d8;line-height:1.6}
select{padding:8px;background:#2c384a;color:#f8f8fa;border:1px solid #63758a;border-radius:6px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.panel{border:1px solid #44546c;border-radius:9px;background:#222b3a;padding:8px;min-width:0}
.panel img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#4b5968 0 25%,#293543 0 50%) 50%/24px 24px}
.panel h3{font-size:14px;margin:4px 0 9px}.reference{max-width:170px}
small{color:#b6c1d2}@media(max-width:800px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:530px){.grid{grid-template-columns:1fr}}
</style><main>
<h1>P15-29 · 从整体淡出恢复远眼与发夹</h1>
<p class="note">角色 p0_character_001。左侧可选角度。远眼和发夹源像素来自 P0 原画，中间层透明度通过 P8 已知平滑淡出函数反算。鼻梁遮挡使用已登记 P15-12 锚点的二维斜边代理，不是经过验证的三维脸面。</p>
<p class="warn">工程恢复通过，但鼻梁遮挡与发夹物理侧仍待视觉签收。逆向透明度不能补出丢失的真实纹理，也不代表新绘制了独立原画。下面这些图都没有替换生产 VDD。</p>
<label>观察角度 <select id="angle"></select></label><p id="metrics"></p>
<h2>完整画面三重对比</h2><div class="grid" id="composites"></div>
<h2>远眼透明原画、恢复及遮挡</h2><div class="grid" id="eyes"></div>
<h2>金色发夹与头发附着</h2><div class="grid" id="clips"></div>
<h2>P0 原始 45° 身份参考</h2><div class="grid"><div class="panel reference"><h3>远眼原图</h3><img src="source-p0-eye45.png"></div><div class="panel reference"><h3>金色交叉发夹</h3><img src="source-p0-clip45.png"></div></div>
</main>
<script>
const D=__DATA__,s=document.getElementById('angle'),c=document.getElementById('composites'),e=document.getElementById('eyes'),p=document.getElementById('clips');
D.forEach((v,i)=>{let o=document.createElement('option');o.value=i;o.textContent=v.yaw+'°';s.append(o)});
function add(el,files,v){el.replaceChildren();for(let [key,name] of files){let node=document.createElement('article');node.className='panel';let h=document.createElement('h3');h.textContent=name;let im=document.createElement('img');im.src=v.prefix+'/'+key+'.png';im.alt=name;node.append(h,im);el.append(node)}}
function draw(){let v=D[Number(s.value)];add(c,[['legacy-composite','P15-21 旧整体淡出'],['recovered-composite','撤销整体淡出'],['bridge-composite','相机锚点鼻梁遮挡候选']],v);
add(e,[['legacy-faded','旧远眼 Alpha'],['inverse-fade','恢复后的远眼原画'],['bridge-proxy','鼻梁代理遮挡后']],v);
add(p,[['clip-legacy','旧发夹 Alpha'],['clip-recovered','恢复发夹'],['clip-hair-attached','覆盖头发区域'],['clip-off-hair','头发外区域']],v);
document.getElementById('metrics').textContent='远眼透明质量 '+v.eye.old+' → '+v.eye.restored+'，鼻梁代理保留 '+(v.eye.visible*100).toFixed(2)+'%；发夹恢复 '+v.clip.old+' → '+v.clip.restored+'，与头发重叠 '+(v.clip.attached*100).toFixed(2)+'%，锚点距离 '+v.clip.anchorDistance+'px。'}
s.onchange=draw;draw();
</script>'''
(O/'index.html').write_text(html.replace('__DATA__',json.dumps(views,ensure_ascii=False)))
Z=P/'exports/p15-29-defade-geometry-review.zip'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted(O.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(O))
with zipfile.ZipFile(Z) as z:assert z.testzip() is None;n=len(z.namelist())
print(json.dumps({'entries':n,'bytes':Z.stat().st_size,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()}))
