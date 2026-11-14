#!/usr/bin/env python3
"""P15-34 offline visual audit: candidate mesh, P15-33, landmark and role layers."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from p15_32_mesh_vdd import R,P,ANGLES,ROLES,slug
OUTPUT=P/"exports/p15-34-source-ink-mesh-review"
MESH=P/"p15-34-feature-mesh"
REF=P/"p15-33-anchor-mesh"

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def iou(a,b):
 ma=a[:,:,3]>16;mb=b[:,:,3]>16
 return round(float((ma&mb).sum()/max(1,(ma|mb).sum())),6)

def build():
 OUTPUT.mkdir(parents=True,exist_ok=True)
 geometry=json.loads((R/"evidence/p15-34-feature-mesh-qa.json").read_text())
 anchors=json.loads((R/"evidence/p15-34-ink-landmarks-qa.json").read_text())
 feature_by_yaw={f["yaw"]:f["features"] for f in anchors["frames"]}
 records=[]
 for frame in geometry["frames"]:
  yaw=float(frame["yaw"]);angle=slug(yaw);dst=OUTPUT/angle;dst.mkdir(parents=True,exist_ok=True)
  new=MESH/angle/"composite.png";old=REF/angle/"composite.png"
  for source,name in [(new,"mesh-composite.png"),(old,"p15-33-reference.png")]:
   shutil.copy2(source,dst/name)
  a=np.array(Image.open(new).convert("RGBA"),np.int16)
  b=np.array(Image.open(old).convert("RGBA"),np.int16)
  diff=np.clip(abs(a-b)*4,0,255).astype("uint8");diff[:,:,3]=255
  Image.fromarray(diff,"RGBA").save(dst/"difference-x4.png")
  marks=Image.open(new).convert("RGBA")
  pen=ImageDraw.Draw(marks)
  if yaw in feature_by_yaw:
   features=feature_by_yaw[yaw]
  else:
   lo,hi=frame["interval"]
   features={}
   for role in ROLES:
    l=feature_by_yaw[lo][role];r=feature_by_yaw[hi][role]
    if l["featureNames"]!=r["featureNames"]:raise AssertionError("Cannot interpolate feature identities")
    lp=np.asarray(l["points443"],float);rp=np.asarray(r["points443"],float)
    features[role]={"featureNames":l["featureNames"],"points443":((lp+rp)*.5).tolist()}
  count=0;sc=1024/443.
  colors=["#ef6a37","#5b57f3","#29966d"]
  for j,role in enumerate(ROLES):
   vals=features[role]
   points=[(float(p[0])*sc,float(p[1])*sc) for p in vals["points443"]]
   color=colors[j]
   if role=="hair.side" and len(points)>=3:pen.line((points[1],points[2]),fill=color,width=3)
   if role=="eye.far" and len(points)>=3:pen.line((points[1],points[2]),fill=color,width=3)
   if role=="hair.clip.cross_gold" and len(points)==5:
    pen.line((points[1],points[2]),fill=color,width=3)
    pen.line((points[3],points[4]),fill=color,width=3)
   for i,(x,y) in enumerate(points):
    pen.ellipse((x-5,y-5,x+5,y+5),fill=color,outline="#ffffff",width=2)
    count+=1
  marks.save(dst/"source-ink-markers.png")
  for role in ROLES:shutil.copy2(MESH/angle/(role+".png"),dst/(role+".png"))
  records.append({"yaw":yaw,"dir":angle,"kind":frame["kind"],
   "sourceMarkerCount":count,"candidateSha256":sha(new),"referenceSha256":sha(old),
   "changedPixels":int(np.count_nonzero(np.any(a!=b,axis=2))),
   "alphaIoU":iou(a,b),"features":{role:features[role] for role in ROLES}})
 html='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
 <title>P15-34 · P0 原画笔触与语义 Mesh</title>
 <style>:root{color-scheme:dark}body{margin:0;background:#151b26;color:#e9f0f7;font:15px/1.5 system-ui;padding:18px}
 main{max-width:1440px;margin:auto}h1{font-size:23px}.note{color:#cad5e1}
 .ctrl{background:#243145;padding:12px;border-radius:10px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
 select,input{accent-color:#8bcaff}select{padding:8px;background:#32445c;color:white}
 #slider{width:100%}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
 .card{background:#243145;border:1px solid #45546b;border-radius:9px;padding:9px;min-width:0}
 .card img{width:100%;aspect-ratio:1;object-fit:contain;background:repeating-conic-gradient(#d2d9e2 0 25%,#f7f8f9 0 50%) 50%/20px 20px}
 .card h3{font-size:13px}p{max-width:950px}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
 @media(max-width:530px){.grid{grid-template-columns:1fr}}</style><main>
 <h1>P15-34 · 墨线采样与局部 Mesh 对照</h1>
 <p class="note">五个参考关键帧、四个三角形 Mesh 中间帧；P0 源像素中的眼部暗线、金色发夹色块与侧发轮廓候选采样点。自动候选点并非人工确认的眼角、交叉金属条端点或特定发束根梢。</p>
 <div class="ctrl"><label>角度 <select id="angle"></select></label><b id="status"></b><input id="slider" type="range" min="0" max="8" step="1" value="0"></div>
 <div class="grid" id="cards"></div><p id="metrics" class="note"></p></main>
 <script>
 const F=__FRAMES__,roles=[["mesh-composite.png","P15-34 · 纹理源笔触 Mesh"],["p15-33-reference.png","P15-33 · 相机 + Alpha 代理点"],["difference-x4.png","RGBA 差分 ×4"],["source-ink-markers.png","像素来源的特征点"],
 ["eye.far.png","远眼 · 原画图层"],["hair.clip.cross_gold.png","交叉发夹 · 原画图层"],["hair.side.png","侧发 · 原画图层"]];
 const a=document.querySelector("#angle"),s=document.querySelector("#slider"),cards=document.querySelector("#cards");
 F.forEach((f,i)=>{const x=document.createElement("option");x.value=String(i);x.textContent=f.yaw+"°";a.append(x)});
 function show(i){const f=F[i],dir=f.dir;cards.replaceChildren();
  for(const [file,label] of roles){const node=document.createElement("section");node.className="card";
   const h=document.createElement("h3");h.textContent=label;const img=document.createElement("img");
   img.alt=label;img.src=dir+"/"+file;node.append(h,img);cards.append(node)}
  document.querySelector("#status").textContent=f.yaw+"° / "+f.kind;
  document.querySelector("#metrics").textContent="与 P15-33 差异像素 "+f.changedPixels+"，轮廓 Alpha IoU "+f.alphaIoU;
  a.value=String(i);s.value=String(i);
 }
 a.addEventListener("change",()=>show(Number(a.value)));
 s.addEventListener("input",()=>show(Number(s.value)));
 window.__KOMA_P15_34={frames:F,select:show};
 show(0);
 </script>'''
 (OUTPUT/"index.html").write_text(html.replace("__FRAMES__",json.dumps(records,ensure_ascii=False)))
 qa={"schema":"KOMA-P15-34-VISUAL-REVIEW-V1","characterId":"p0_character_001",
  "frames":records,"roleCount":len(ROLES),"sourceInkLandmarkApproval":False,
  "productionVddChanged":False,"artisticallyAccepted":False}
 (OUTPUT/"qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"frames":len(records),"markersPerFrame":[x["sourceMarkerCount"] for x in records],
  "changedPixels":[x["changedPixels"] for x in records],"IoU":[x["alphaIoU"] for x in records]}))
 return qa
if __name__=="__main__":build()
