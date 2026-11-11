#!/usr/bin/env python3
"""P15-37 offline HTML comparison of registered painted 2.5D ArtMesh frames."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import R,P,slug,read

OUT=P/"exports/p15-37-temporal-art-review"
SRC=P/"p15-37-temporal-artmesh"
BASE=P/"p15-35-occlusion-mount"
PAINT=P/"p15-36-qwen-local-paint"
SOURCE45=P/"p2-views/whole/yaw045.png"
QA=R/"evidence/p15-37-visual-review-qa.json"

def sha(file):return hashlib.sha256(Path(file).read_bytes()).hexdigest()

def run():
 src=json.loads((R/"evidence/p15-37-temporal-artmesh-qa.json").read_text())
 if src["characterId"]!="p0_character_001" or len(src["frames"])!=9:
  raise AssertionError("Nine registered P0 frames required")
 if sha(SOURCE45)!=src["sourceP0Original45SHA256"]:
  raise AssertionError("P0 identity source changed")
 OUT.mkdir(parents=True,exist_ok=True)
 shutil.copy2(SOURCE45,OUT/"p0-45-identity.png")
 records=[]
 for f in src["frames"]:
  yaw=f["yaw"];tag=slug(yaw);d=OUT/tag;d.mkdir(parents=True,exist_ok=True)
  donor=57.5 if yaw<=58.75 else 60.
  paintref=P/"p15-36-painting-candidates/generated"/("yaw057p5-dual-source-qwen.png"
     if donor==57.5 else "yaw060-pose-retouch-qwen.png")
  sources={
    "p15-35-reference.png":BASE/tag/"composite.png",
    "p15-37-painted-vdd.png":SRC/tag/"composite.png",
    "eye-far.png":SRC/tag/"eye.far.png",
    "face-skin.png":SRC/tag/"face.skin.png",
    "hair-front.png":SRC/tag/"hair.front.png",
    "clip-gold.png":SRC/tag/"hair.clip.cross_gold.png",
    "eye-hidden-source.png":SRC/tag/"eye.far.hidden-underpaint.png",
    "new-keyart-rgb.png":paintref
  }
  for name,original in sources.items():
   if not original.is_file():raise FileNotFoundError(original)
   shutil.copy2(original,d/name)
  a=np.array(Image.open(sources["p15-35-reference.png"]).convert("RGBA"),np.int16)
  b=np.array(Image.open(sources["p15-37-painted-vdd.png"]).convert("RGBA"),np.int16)
  diff=np.uint8(np.clip(abs(a-b)*4,0,255));diff[:,:,3]=255
  Image.fromarray(diff,"RGBA").save(d/"paint-change-x4.png")
  maps=[]
  for role,name in (("eye.far","eye-far"),("face.skin","face-skin"),
                    ("hair.front","hair-front")):
   old=read(BASE/tag/(role+".png"));new=read(SRC/tag/(role+".png"))
   delta=np.uint8(np.any(old!=new,axis=2)*255)
   maps.append(delta)
  mask=np.maximum.reduce(maps)
  Image.fromarray(mask,"L").save(d/"paint-owner-change.png")
  output={name:sha(d/name) for name in [*sources,"paint-change-x4.png","paint-owner-change.png"]}
  records.append({"angle":yaw,"slug":tag,"sourceType":f["kind"],"paintWeight":f["paintWeight"],
    "fullKeyframeApproved":False,"changedPixels":f["changedCompositePixels"],
    "eyeVisibleAlphaMass":f["eyeDisplayedAlphaMass"],
    "clipHairContactCoverage":f["clipHairContactCoverage"],
    "sourceDonorYaw":donor,"sourceDonorSHA256":sha(paintref),
    "sourcePartOrigins":f["paintSources"],
    "sources":output})
 html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-37 · 45° 身份基准与 55°–65° ArtMesh 动画</title>
<style>
:root{color-scheme:dark;background:#151d29;color:#eff4f9;font:14px/1.55 system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0;padding:20px}main{max-width:1510px;margin:auto}
h1{font-size:22px;margin:0 0 7px}p{color:#cad6e4;max-width:1100px}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:12px;background:#293b53;border-radius:12px;border:1px solid #50627c}
button{font:inherit;padding:7px 13px;color:inherit;background:#3a506c;border:1px solid #677d9b;border-radius:9px;cursor:pointer}
button[aria-pressed=true]{background:#516fa0}
#angles{width:100%;accent-color:#89b3ef}
.gallery{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:15px 0}
article{min-width:0;background:#253347;border:1px solid #435672;border-radius:11px;padding:9px}
h3{font-size:13px;font-weight:650;margin:0 0 8px}
img{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d4dbe5 0% 25%,#f7fafc 0% 50%) 50%/22px 22px}
small{font-size:12px;color:#bbc9dd}#state{margin-top:12px;color:#c8d6e6}
@media(max-width:1050px){.gallery{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.gallery{grid-template-columns:1fr}}
</style><main>
<h1>P15-37 · P0 原画与局部 VDD 连续转头</h1>
<p>冻结的 P0 45° 原画用于身份参照；55°–65° 九帧按 13 个 ArtMesh 语义部件重组，其中 57.5° / 60° 使用已生成的局部 RGB 原画。45°–55° 连续原画与隐藏笔触仍须单独验收。</p>
<div class="bar">
<button id="prev">上一帧</button><b id="angle">55°</b><button id="next">下一帧</button>
<button id="compare" aria-pressed="true">连续画面</button>
<button id="parts" aria-pressed="false">语义部件</button>
<button id="sources" aria-pressed="false">原画来源</button>
<input id="angles" type="range" min="0" max="8" value="0" step="1">
</div><div id="metrics"></div><div class="gallery" id="gallery"></div><div id="state" role="status"></div></main>
<script>
"use strict";(()=>{
const frames=__FRAMES__,modeSources={
 compare:[["p15-35-reference.png","P15-35 · 基线画面"],
 ["p15-37-painted-vdd.png","P15-37 · 13 部件原画连续合成"],
 ["paint-change-x4.png","局部绘画差分 ×4"],
 ["paint-owner-change.png","有新绘画变化的部件区域"]],
 parts:[["eye-far.png","远眼 ArtMesh"],
 ["face-skin.png","面部 ArtMesh"],
 ["hair-front.png","刘海 ArtMesh"],
 ["clip-gold.png","金色发夹 ArtMesh"]],
 sources:[["../p0-45-identity.png","P0 45° 身份参考"],
 ["new-keyart-rgb.png","生成模型原画来源"],
 ["eye-hidden-source.png","远眼的完整隐藏来源"],
 ["p15-37-painted-vdd.png","当前角度的完整画面"]]
};
const $=id=>document.getElementById(id);
const state={index:0,mode:"compare",images:[],errors:[],ready:false};
let request=0;
function result(){return{...state,images:[...state.images],errors:[...state.errors]}}
async function select(index=state.index,mode=state.mode){
 if(!Number.isInteger(index)||index<0||index>=frames.length||!Object.hasOwn(modeSources,mode))throw Error("Invalid angle or view");
 const token=++request;state.index=index;state.mode=mode;state.ready=false;state.images=[];state.errors=[];
 const frame=frames[index];$("angle").textContent=frame.angle+"°";$("angles").value=String(index);
 $("metrics").textContent="来源 "+frame.sourceType+" | 新原画混合权重 "+frame.paintWeight.toFixed(3)+
 " | 画面变化像素 "+frame.changedPixels+" | 发夹/前发接触 "+(100*frame.clipHairContactCoverage).toFixed(1)+"%";
 for(const key of Object.keys(modeSources))$(key).setAttribute("aria-pressed",String(key===mode));
 const gallery=$("gallery");gallery.replaceChildren();
 const items=modeSources[mode].map(([file,label])=>{
  const card=document.createElement("article"),h=document.createElement("h3"),im=document.createElement("img"),note=document.createElement("small");
  h.textContent=label;im.alt=label;im.src=frame.slug+"/"+file;
  note.textContent=file;card.append(h,im,note);gallery.append(card);return{file,image:im}
 });
 const checked=await Promise.allSettled(items.map(async({file,image})=>{
  await image.decode();
  const width=image.naturalWidth,height=image.naturalHeight;
  if(![443,1024].includes(width)||height!==width)throw Error("Missing 443/1024 source "+file);
  return{source:file,width,height}
 }));
 if(token!==request)return result();
 for(const x of checked){if(x.status==="fulfilled")state.images.push(x.value);else state.errors.push(String(x.reason))}
 state.ready=state.images.length===4&&state.errors.length===0;
 $("state").textContent=state.ready?"4 项图像来源加载完成；独立原画验收仍按视觉门禁执行。":"来源图像加载或尺寸异常";
 return result()
}
$("prev").addEventListener("click",()=>void select(Math.max(0,state.index-1)));
$("next").addEventListener("click",()=>void select(Math.min(frames.length-1,state.index+1)));
$("angles").addEventListener("input",()=>void select(Number($("angles").value)));
for(const mode of Object.keys(modeSources))$(mode).addEventListener("click",()=>void select(state.index,mode));
window.__KOMA_P15_37={select,result,frames};void select(0);
})();
</script></html>'''
 (OUT/"index.html").write_text(html.replace("__FRAMES__",json.dumps(records,ensure_ascii=False)))
 result={"schema":"KOMA-P15-37-VISUAL-REVIEW-V1","characterId":"p0_character_001",
   "angles":[r["angle"] for r in records],"frameCount":len(records),
   "modeCount":3,"sourceP0_45SHA256":sha(SOURCE45),
   "newModelPaintedKeyAngles":[57.5,60.],"frames":records,
   "independentlyApprovedFullOriginalKeyviews":0,
   "independentHiddenUnderpaintingApproved":0,
   "formalArtistApproval":False}
 QA.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 (OUT/"qa.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":"NINE_FRAME_PAINTED_ROLE_REVIEW_BUILT",
   "frames":len(records),"angleRange":[min(r["angle"] for r in records),max(r["angle"] for r in records)],
   "modes":3,"sourceAssets":sum(len(r["sources"]) for r in records)}))
 return result
if __name__=="__main__":run()
