#!/usr/bin/env python3
"""P15-38 45–65 original P0 ArtMesh pose review and per-layer provenance."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import R,P,slug,read
from p15_37_temporal_paint_vdd import premul_mix

BASE=P/"p15-38-p0-registered-arc"
REFERENCE=P/"p15-37-temporal-artmesh"
P045=P/"p2-views/whole/yaw045.png"
OUT=P/"exports/p15-38-original-p0-arc-review"
QA=R/"evidence/p15-38-visual-review-qa.json"

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run():
 qa=json.loads((R/"evidence/p15-38-extended-artmesh-qa.json").read_text())
 if qa["characterId"]!="p0_character_001" or len(qa["angles"])!=13:
  raise AssertionError("Registered P0 45–65 arc required")
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"p0-yaw45-original.png").write_bytes(P045.read_bytes())
 old45=read(P045);old55=read(REFERENCE/"yaw55/composite.png")
 registered=[]
 for row in qa["frames"]:
  yaw=row["yaw"];tag=slug(yaw);d=OUT/tag;d.mkdir(parents=True,exist_ok=True)
  if yaw<55:
   t=(yaw-45)/10.
   baseline=premul_mix(old45,old55,t)
   Image.fromarray(baseline,"RGBA").save(d/"whole-crossview-reference.png")
  else:
   (d/"whole-crossview-reference.png").write_bytes((REFERENCE/tag/"composite.png").read_bytes())
  files={
   "p15-38-registered-artmesh.png":BASE/tag/"composite.png",
   "eye-far.png":BASE/tag/"eye.far.png",
   "eye-near.png":BASE/tag/"eye.near.png",
   "face-skin.png":BASE/tag/"face.skin.png",
   "hair-front.png":BASE/tag/"hair.front.png",
   "side-hair.png":BASE/tag/"hair.side.png",
   "gold-clip.png":BASE/tag/"hair.clip.cross_gold.png"
  }
  for name,src in files.items():
   if not src.is_file():raise FileNotFoundError(src)
   (d/name).write_bytes(src.read_bytes())
  a=np.array(Image.open(d/"whole-crossview-reference.png").convert("RGBA"),np.int16)
  b=np.array(Image.open(d/"p15-38-registered-artmesh.png").convert("RGBA"),np.int16)
  change=np.uint8(np.clip(np.abs(a-b)*4,0,255));change[:,:,3]=255
  Image.fromarray(change,"RGBA").save(d/"difference-x4.png")
  hashes={name:sha(d/name) for name in [*files,"whole-crossview-reference.png","difference-x4.png"]}
  aa=a[:,:,3]>16;bb=b[:,:,3]>16
  localIou=round(float((aa&bb).sum()/max(1,(aa|bb).sum())),6)
  registered.append({"yaw":yaw,"dir":tag,"kind":row["kind"],"roleCount":row["roleCount"],
    "alphaIoUWithWholeCrossviewReference":localIou,
    "differentPixels":int(np.count_nonzero(np.any(a!=b,axis=2))),
    "sourceP0_45SHA256":qa["sourceOriginal45"]["sourceP0SHA256"],
    "sourceDisplaySHA256":sha(BASE/tag/"composite.png"),
    "sourceImages":hashes,"artisticallyAccepted":False})
 html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P15-38 · P0 原画 45°–65° 13 语义部件旋转审查</title>
<style>:root{color-scheme:dark;background:#141c28;color:#eff3fa;font:14px/1.5 system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0;padding:16px}main{max-width:1500px;margin:auto}
h1{font-size:23px;margin:0 0 7px}p{color:#c9d5e5;max-width:1000px}
.bar{display:flex;align-items:center;flex-wrap:wrap;gap:11px;background:#27384d;border-radius:10px;padding:12px}
button{font:inherit;color:inherit;background:#3a526b;border:1px solid #617996;padding:8px 11px;border-radius:8px}
button[aria-pressed=true]{background:#526d95}#yaw{font-size:19px}#track{width:100%;accent-color:#7b9cde}
.gallery{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:14px 0}
article{background:#253449;border:1px solid #435571;border-radius:9px;padding:8px;min-width:0}
h3{font-size:14px;margin:0 0 8px}img{width:100%;display:block;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d5dde6 0 25%,#f7f8fb 0 50%) 50%/24px 24px}
small{display:block;color:#b9c9d9}#meta{padding:7px 0;color:#c5d3e2}
@media(max-width:900px){.gallery{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:550px){.gallery{grid-template-columns:1fr}}</style>
<main><h1>P15-38 · P0 45°–65° 原画驱动 13 层连续预览</h1>
<p>P0 45° 与 P15-37 55°–65° 为登记来源，47.5°、50°、52.5° 使用逐部件光流插值。眼、鼻、发夹与被遮挡笔触需进行独立原画视觉核定。</p>
<div class="bar">
<button id="prev">上一帧</button><strong id="yaw">45°</strong><button id="next">下一帧</button>
<button id="compare" aria-pressed="true">整图对照</button>
<button id="face" aria-pressed="false">面部细节</button>
<button id="hair" aria-pressed="false">发夹与头发</button>
<input id="track" type="range" min="0" max="12" step="1" value="0">
</div><div id="meta"></div><div class="gallery" id="gallery"></div><div id="state" role="status"></div>
<script>
"use strict";(()=>{
const frames=__FRAMES__,modes={
compare:[["whole-crossview-reference.png","原画关键帧整体过渡参考"],
 ["p15-38-registered-artmesh.png","P15-38 · 13 部件分层旋转"],
 ["difference-x4.png","RGB/Alpha 差异 ×4"],
 ["../p0-yaw45-original.png","P0 45° 冻结身份参考"]],
face:[["eye-near.png","近眼 ArtMesh"],
 ["eye-far.png","远眼 ArtMesh"],
 ["face-skin.png","面部皮肤 ArtMesh"],
 ["p15-38-registered-artmesh.png","分层合成画面"]],
hair:[["hair-front.png","刘海 ArtMesh"],
 ["side-hair.png","侧发 ArtMesh"],
 ["gold-clip.png","金色交叉发夹"],
 ["p15-38-registered-artmesh.png","完整转头画面"]]
};
const $=s=>document.getElementById(s);
const state={index:0,mode:"compare",ready:false,errors:[],images:[]};let serial=0;
const snapshot=()=>({...state,errors:[...state.errors],images:[...state.images]});
async function select(index=state.index,mode=state.mode){
 if(!Number.isInteger(index)||index<0||index>=frames.length||!Object.hasOwn(modes,mode))throw Error("Invalid yaw or layer mode");
 const ticket=++serial;state.index=index;state.mode=mode;state.ready=false;state.errors=[];state.images=[];
 const f=frames[index];$("yaw").textContent=f.yaw+"°";$("track").value=index;
 $("meta").textContent="角色数 "+f.roleCount+" · 帧类型 "+f.kind+" · 与原画参考轮廓 IoU "+f.alphaIoUWithWholeCrossviewReference.toFixed(5);
 for(const m of Object.keys(modes))$(m).setAttribute("aria-pressed",String(m===mode));
 const gallery=$("gallery");gallery.replaceChildren();
 const elements=modes[mode].map(([file,label])=>{
  const card=document.createElement("article"),title=document.createElement("h3"),im=document.createElement("img"),note=document.createElement("small");
  title.textContent=label;im.alt=label;im.src=f.dir+"/"+file;note.textContent=file;card.append(title,im,note);gallery.append(card);return{file,im}
 });
 const settled=await Promise.allSettled(elements.map(async({file,im})=>{
  await im.decode();
  if(![443,1024].includes(im.naturalWidth)||im.naturalWidth!==im.naturalHeight)throw Error("Invalid canvas "+file);
  return{source:file,width:im.naturalWidth,height:im.naturalHeight}
 }));
 if(ticket!==serial)return snapshot();
 for(const v of settled){if(v.status==="fulfilled")state.images.push(v.value);else state.errors.push(String(v.reason))}
 state.ready=state.images.length===4&&state.errors.length===0;
 $("state").textContent=state.ready?"全部来源载入成功；正式原画视觉签收独立执行。":"原画来源或尺寸校验失败";
 return snapshot()
}
$("prev").addEventListener("click",()=>void select(Math.max(0,state.index-1)));
$("next").addEventListener("click",()=>void select(Math.min(frames.length-1,state.index+1)));
$("track").addEventListener("input",()=>void select(Number($("track").value)));
for(const m of Object.keys(modes))$(m).addEventListener("click",()=>void select(state.index,m));
window.__KOMA_P15_38={select,snapshot,frames};void select(0);
})();
</script></main></html>'''
 (OUT/"index.html").write_text(html.replace("__FRAMES__",json.dumps(registered,ensure_ascii=False)))
 result={"schema":"KOMA-P15-38-ORIGINAL-CAMERA-ARC-REVIEW-V1",
  "characterId":"p0_character_001",
  "frames":registered,"roles":13,"angles":[r["yaw"] for r in registered],
  "modes":["compare","face","hair"],"sourceOriginal45SHA256":sha(P045),
  "fullArtistAcceptance":False,"independentPaintedKeyframesApproved":0}
 QA.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 (OUT/"qa.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":"ORIGINAL_P0_45_TO65_REVIEW_BUILT",
   "frames":len(registered),"modes":3,"imageSources":sum(len(r["sourceImages"]) for r in registered),
   "alphaIoU45to55":[r["alphaIoUWithWholeCrossviewReference"] for r in registered[:5]]}))
 return result
if __name__=="__main__":run()
