#!/usr/bin/env python3
"""P15-36 independent painted face/keypart source and HTML comparison."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from p15_32_mesh_vdd import R,P,slug,read
ORIGINAL=P/"p15-35-occlusion-mount"
PAINTED=P/"p15-36-qwen-local-paint"
STROKES=P/"p15-36-keypart-cel"
DONOR=P/"p15-36-painting-candidates/generated"
OUT=P/"exports/p15-36-original-keypart-review"
QA=R/"evidence/p15-36-visual-review-qa.json"
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def run():
 data=json.loads((R/"evidence/p15-36-qwen-local-repair-qa.json").read_text())
 control=json.loads((R/"evidence/p15-36-cel-keypart-qa.json").read_text())
 if data["characterId"]!=control["characterId"] or data["characterId"]!="p0_character_001":
  raise AssertionError("Identity differs")
 frames=[]
 for r in data["frames"]:
  yaw=r["yaw"];key=slug(yaw);d=OUT/key;d.mkdir(parents=True,exist_ok=True)
  files={
   "original-p15-35.png":ORIGINAL/key/"composite.png",
   "new-original-keyparts.png":PAINTED/key/"composite.png",
   "full-qwen-paint-source.png":P/r["donor"],
   "cel-stroke-comparison.png":STROKES/key/"composite.png",
   "eye-far-rgba.png":PAINTED/key/"eye.far.png",
   "face-skin-rgba.png":PAINTED/key/"face.skin.png",
   "hair-fringe-rgba.png":PAINTED/key/"hair.front.png",
   "gold-cross-rgba.png":PAINTED/key/"hair.clip.cross_gold.png",
   "eye-far-local-paint.png":PAINTED/key/"eye.far.donor-paint.png",
   "face-local-paint.png":PAINTED/key/"face.skin.donor-paint.png",
   "fringe-local-paint.png":PAINTED/key/"hair.front.donor-paint.png",
   "eye-far-original.png":PAINTED/key/"eye.far.original-underpaint.png",
   "eye-far-hidden.png":PAINTED/key/"eye.far.hidden-original.png",
  }
  for name,src in files.items():
   if not src.exists():raise FileNotFoundError(src)
   shutil.copy2(src,d/name)
  original=np.asarray(Image.open(files["original-p15-35.png"]).convert("RGBA"),dtype=np.int16)
  repaired=np.asarray(Image.open(files["new-original-keyparts.png"]).convert("RGBA"),dtype=np.int16)
  delta=np.uint8(np.clip(abs(original-repaired)*4,0,255))
  delta[:,:,3]=255
  Image.fromarray(delta,"RGBA").save(d/"difference-x4.png")
  hashes={name:sha(d/name) for name in [*files,"difference-x4.png"]}
  frames.append({"yaw":yaw,"dir":key,"outputSHA256":r["compositeSHA256"],
   "sourceSHA256":r["oldCompositeSHA256"],
   "donorSHA256":r["donorSHA256"],"donorRegistrationOffset":r["registrationOffset"],
   "modelPaintedRoleCount":len(r["newPaintedSemanticRoles"]),
   "semanticRoles":r["roleCount"],"newPixelsChanged":r["changedCompositePixels"],
   "independentHiddenUnderpaintApproved":False,
   "artisticApproval":False,"sha256":hashes})
 html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
 <title>P15-36 · P0 多视角原画局部补绘审查</title>
 <style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;padding:16px;background:#151c29;color:#edf3fa;font:14px/1.5 system-ui}
 main{max-width:1400px;margin:auto}h1{font-size:23px;margin:0 0 6px}p{color:#ccd8e6;max-width:1000px}
 .ctrl{display:flex;align-items:center;flex-wrap:wrap;gap:10px;background:#29374d;border:1px solid #485974;padding:11px;border-radius:10px}
 button{font:inherit;color:inherit;border-radius:8px;border:1px solid #627c9e;background:#364d67;padding:8px 12px;cursor:pointer}
 button[aria-pressed=true]{background:#557ea9}#meta{margin:10px 0;color:#cbd8e7}
 .gallery{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
 article{border:1px solid #40536a;background:#263448;border-radius:10px;padding:9px;min-width:0}
 h3{font-size:14px;line-height:1.3;margin:0 0 10px}img{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d3d9df 0% 25%,#f9fafb 0% 50%) 50%/24px 24px}
 small{display:block;color:#c4d2e5;margin:7px 0 0}footer{color:#cbd8e7;padding:10px 0}
 @media(max-width:1100px){.gallery{grid-template-columns:repeat(2,minmax(0,1fr))}}
 @media(max-width:580px){.gallery{grid-template-columns:1fr}}</style>
 <main><h1>P15-36 · P0 原画与远眼遮挡补绘审查</h1>
 <p>57.5°、60° 的真实新绘画像素被映射到远眼、面部和刘海三个独立 RGBA 文件。完整 13 个原有部件继续保留。可比较原始姿态、局部补绘、原始生成图与隐藏眼睛图层。所有候选均需独立的画质确认。</p>
 <div class="ctrl"><button id="a57" aria-pressed="true">57.5°</button><button id="a60" aria-pressed="false">60°</button>
 <button id="compare" aria-pressed="true">整图对照</button><button id="parts" aria-pressed="false">语义分层</button>
 <button id="hidden" aria-pressed="false">隐藏补绘</button></div>
 <p id="meta"></p><div id="gallery" class="gallery"></div>
 <footer id="status">图像来源加载中</footer>
 </main><script>
 const F=__FRAMES__,modes={
 compare:[["original-p15-35.png","P15-35 原始 ArtMesh"],["new-original-keyparts.png","P15-36 局部补绘候选"],["full-qwen-paint-source.png","新增原画 RGB 输入"],["difference-x4.png","画面差分 ×4"]],
 parts:[["eye-far-rgba.png","远眼 ArtMesh RGBA"],["face-skin-rgba.png","面部 ArtMesh RGBA"],["hair-fringe-rgba.png","刘海 ArtMesh RGBA"],["gold-cross-rgba.png","原始金色发夹 RGBA"]],
 hidden:[["eye-far-local-paint.png","远眼新增原画区域"],["face-local-paint.png","面部新增原画区域"],["eye-far-original.png","远眼原始完整图层"],["eye-far-hidden.png","远眼隐藏像素保留"]]};
 let angle=57.5,mode="compare",serial=0;const $=x=>document.getElementById(x);
 const state={angle,mode,ready:false,errors:[],images:[]};
 function result(){return{angle:state.angle,mode:state.mode,ready:state.ready,errors:[...state.errors],images:[...state.images]}}
 async function select(a=angle,m=mode){
  if(![57.5,60].includes(a)||!Object.hasOwn(modes,m))throw Error("Unknown P15-36 review state");
  const token=++serial;angle=a;mode=m;state.angle=a;state.mode=m;state.ready=false;state.errors=[];state.images=[];
  $("a57").setAttribute("aria-pressed",String(a===57.5));$("a60").setAttribute("aria-pressed",String(a===60));
  for(const k of Object.keys(modes))$(k==="compare"?"compare":k).setAttribute("aria-pressed",String(k===m));
  const f=F.find(x=>x.yaw===a);
  $("meta").textContent="角度 "+a+"° | 新绘画来源图像局部配准 "+f.donorRegistrationOffset.join(", ")+" px | 新 RGB 像素导致的复合变化 "+f.newPixelsChanged+" px";
  const gallery=$("gallery");gallery.replaceChildren();
  const slots=modes[m].map(([name,label])=>{
   const card=document.createElement("article"),head=document.createElement("h3"),
    im=document.createElement("img"),foot=document.createElement("small");
   head.textContent=label;im.alt=label;im.src=f.dir+"/"+name;
   foot.textContent=name;card.append(head,im,foot);gallery.append(card);
   return {name,image:im};
  });
  const checked=await Promise.allSettled(slots.map(async({name,image})=>{
   await image.decode();if(![443,1024].includes(image.naturalWidth)||image.naturalWidth!==image.naturalHeight)
    throw Error("Missing ArtMesh image "+name);
   return {role:name,path:image.getAttribute("src"),width:image.naturalWidth,height:image.naturalHeight};
  }));
  if(token!==serial)return result();
  for(const x of checked){if(x.status==="fulfilled")state.images.push(x.value);else state.errors.push(String(x.reason))}
  state.ready=state.images.length===4&&state.errors.length===0;
  $("status").textContent=state.ready?"4 张来源图像已加载，仍需原画视觉签收。":"来源校验异常";
  return result();
 }
 $("a57").addEventListener("click",()=>void select(57.5,mode));
 $("a60").addEventListener("click",()=>void select(60,mode));
 for(const k of Object.keys(modes))$(k).addEventListener("click",()=>void select(angle,k));
 window.__KOMA_P15_36={select,result,frames:F};
 void select(angle,mode);
 </script></html>'''
 (OUT/"index.html").write_text(html.replace("__FRAMES__",json.dumps(frames,ensure_ascii=False)))
 report={"schema":"KOMA-P15-36-KEYPART-INTERACTIVE-REVIEW-V1",
  "characterId":"p0_character_001","angles":[57.5,60],"roleCount":13,
  "frames":frames,"modeCount":3,"modes":list(("compare","parts","hidden")),
  "artisticApproval":False,
  "underpaintFromExistingSource":True,"newModelPaintedSemanticRolesPerAngle":3}
 (OUT/"qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 QA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"status":"P15_36_INTERACTIVE_HTML_CREATED","frames":len(frames),
   "sourceAssetsPerAngle":len(files),"modes":report["modes"],
   "newPaintedRolesPerAngle":3}))
 return report

if __name__=="__main__":run()
