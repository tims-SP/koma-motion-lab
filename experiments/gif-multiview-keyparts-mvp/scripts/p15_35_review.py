#!/usr/bin/env python3
"""Offline P15-35 eye-depth and front-hair clip attachment visual audit."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p15_32_mesh_vdd import R,P,slug
ROOT=P/"p15-35-occlusion-mount"
REF=P/"p15-34-feature-mesh"
OUT=P/"exports/p15-35-face-depth-hair-review"
SOURCE=R/"evidence/p15-35-occlusion-mount-qa.json"
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def build():
 qa=json.loads(SOURCE.read_text())
 if qa["characterId"]!="p0_character_001":raise AssertionError("Source identity changed")
 rows=[]
 for f in qa["frames"]:
  y=f["yaw"];tag=slug(y);d=OUT/tag;d.mkdir(parents=True,exist_ok=True)
  files={
   "depth-mounted.png":ROOT/tag/"composite.png",
   "source-p15-34.png":REF/tag/"composite.png",
   "eye-original.png":ROOT/tag/"eye.far.original.png",
   "eye-retained.png":ROOT/tag/"eye.far.png",
   "eye-hidden.png":ROOT/tag/"eye.far.hidden-underpaint.png",
   "depth-mask.png":ROOT/tag/"face-depth-proxy.png",
   "hair-mounted-clip.png":ROOT/tag/"hair.clip.cross_gold.png",
   "source-clip.png":REF/tag/"hair.clip.cross_gold.png",
   "front-hair.png":REF/tag/"hair.front.png",
   "face-skin.png":REF/tag/"face.skin.png",
  }
  for name,src in files.items():
   if not src.is_file():raise FileNotFoundError(src)
   shutil.copy2(src,d/name)
  a=np.asarray(Image.open(files["depth-mounted.png"]).convert("RGBA"),np.int16)
  b=np.asarray(Image.open(files["source-p15-34.png"]).convert("RGBA"),np.int16)
  delta=np.clip(np.abs(a-b)*4,0,255).astype("uint8");delta[:,:,3]=255
  Image.fromarray(delta,"RGBA").save(d/"difference-x4.png")
  rows.append({"yaw":y,"dir":tag,
   "visibleFraction":f["eyeAlphaPartitionFractions"]["eyeVisible"],
   "faceOccluded":f["eyeAlphaPartitionFractions"]["hiddenByFace"],
   "noseOccluded":f["eyeAlphaPartitionFractions"]["hiddenByNose"],
   "bangOccluded":f["eyeAlphaPartitionFractions"]["hiddenByBangs"],
   "sourceClipHairContact":f["clipAttachment"]["sourceContactCoverage"],
   "attachedClipHairContact":f["clipAttachment"]["attachedContactCoverage"],
   "clipUVResidual":f["clipAttachment"]["uvResidual"],
   "shift":f["clipAttachment"]["clipPixelShift"],
   "compositeChanged":f["changedCompositePixelsVsP15_34"],
   "outputs":{name:sha(d/name) for name in [*files,"difference-x4.png"]}})
 html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
 <title>P15-35 · 面部深度与发夹附着实验</title>
 <style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;padding:18px;background:#151d29;color:#f1f5fa;font:15px/1.5 system-ui}
 main{max-width:1440px;margin:auto}h1{font-size:23px}.ctrl{padding:12px;border-radius:9px;background:#263348;display:flex;gap:14px;flex-wrap:wrap;align-items:center}
 input{width:100%;accent-color:#89cfff}select{padding:8px;background:#334967;color:white}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px}
 .card{min-width:0;background:#263348;padding:8px;border-radius:9px;border:1px solid #3c4d68}.card h3{font-size:13px}
 img{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d6dce3 0 25%,#fafbfc 0 50%) 50%/24px 24px}
 p{color:#d0dce9}@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
 @media(max-width:520px){.grid{grid-template-columns:1fr}}</style><main>
 <h1>P15-35 · 远眼前景遮挡与发夹局部绑定</h1>
 <p>9 帧 55°–65° 实验：使用原有脸部材质做近侧面遮挡，记录眼睛完整源 RGB 与遮挡分解；金色发夹按 hair.front 的局部像素坐标对齐。以上均为可审查 2.5D 空间假设，不是已确认真实三维头部几何。</p>
 <div class="ctrl"><label>角度 <select id="angle"></select></label><b id="status"></b><input id="slider" type="range" min="0" max="8" step="1" value="0"></div>
 <p id="metrics"></p><div class="grid" id="cards"></div>
 <script>
 const data=__FRAMES__,items=[
 ["depth-mounted.png","P15-35 面部遮挡 + 发夹附着"],
 ["source-p15-34.png","P15-34 原图角色参考"],
 ["difference-x4.png","整体图像像素差异 ×4"],
 ["eye-original.png","远眼完整原画 RGBA"],
 ["eye-retained.png","深度测试后的远眼可见层"],
 ["eye-hidden.png","隐藏原画像素保存层"],
 ["depth-mask.png","近面部局部深度遮挡代理"],
 ["hair-mounted-clip.png","随前发局部坐标移动的发夹"],
 ["source-clip.png","原始金色发夹 RGBA"],
 ["front-hair.png","发夹附着的前发图层"],
 ["face-skin.png","已有的面部原画材质"]];
 const angle=document.querySelector("#angle"),slider=document.querySelector("#slider"),cards=document.querySelector("#cards");
 data.forEach((r,i)=>{const o=document.createElement("option");o.value=i;o.textContent=r.yaw+"°";angle.append(o)});
 function render(i){const r=data[i];angle.value=String(i);slider.value=String(i);
  document.querySelector("#status").textContent=r.yaw+"°";
  document.querySelector("#metrics").textContent="远眼可见 "+(r.visibleFraction*100).toFixed(1)+"% · 皮肤面遮挡 "+(r.faceOccluded*100).toFixed(1)+"% · 发夹接触 "+(r.sourceClipHairContact*100).toFixed(1)+"% → "+(r.attachedClipHairContact*100).toFixed(1)+"% · 发夹平移 "+JSON.stringify(r.shift)+" · 变化像素 "+r.compositeChanged;
  cards.replaceChildren();for(const [file,title] of items){const section=document.createElement("section");section.className="card";
   const h=document.createElement("h3");h.textContent=title;const im=document.createElement("img");
   im.alt=title;im.src=r.dir+"/"+file;section.append(h,im);cards.append(section)}}
 angle.addEventListener("change",()=>render(Number(angle.value)));
 slider.addEventListener("input",()=>render(Number(slider.value)));
 window.__KOMA_P15_35={data,render};render(0);
 </script>'''
 (OUT/"index.html").write_text(html.replace("__FRAMES__",json.dumps(rows,ensure_ascii=False)))
 review={"schema":"KOMA-P15-35-VISUAL-ROLE-DEPTH-REVIEW-V1",
   "characterId":"p0_character_001","frames":rows,"roleCount":13,
   "originalEyeRGBRetained":True,"faceProxyGeometryArtistApproved":False,
   "clipParentMaterialVerified":False,"productionVDDChanged":False,
   "artisticallyAccepted":False}
 (OUT/"qa.json").write_text(json.dumps(review,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"frames":len(rows),
   "visible":[x["visibleFraction"] for x in rows],
   "clipContact":[x["attachedClipHairContact"] for x in rows],
   "compositeChanged":[x["compositeChanged"] for x in rows]}))
 return review
if __name__=="__main__":build()
