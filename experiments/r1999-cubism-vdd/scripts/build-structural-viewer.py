#!/usr/bin/env python3
"""Build a single-file offline HTML reviewer for the eight PMX-derived view images.

The viewer is a reference-turntable interface. Between 45-degree keys it
offers an explicitly labeled cross-dissolve rather than claiming VDD.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path

LABELS = ["Front", "Three-quarter", "Profile", "Rear three-quarter",
          "Back", "Rear three-quarter", "Profile", "Three-quarter"]


def build(input_dir: Path, output: Path) -> None:
    report = json.loads((input_dir / "turnaround-qa.json").read_text())
    if report.get("status") != "PASS_3D_REFERENCE_RENDER" or report.get("independent2DArtworkCount") != 0:
        raise ValueError("Expected verified structural reference renders")
    frames = sorted(report["renderedImages"], key=lambda e: e["yawDeg"])
    if [f["yawDeg"] for f in frames] != list(range(0, 360, 45)):
        raise ValueError("Eight 45-degree camera keys required")
    cards = []
    for i, item in enumerate(frames):
        raw = (input_dir / item["filename"]).read_bytes()
        import hashlib
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Image hash changed: " + item["filename"])
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("PNG signature missing")
        src = "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
        cards.append(
            f'<button class="angle" type="button" data-yaw="{item["yawDeg"]}" '
            f'aria-label="Select {item["yawDeg"]} degrees">'
            f'<img src="{src}" alt="{html.escape(LABELS[i])} view">'
            f'<span>{item["yawDeg"]}° · {html.escape(LABELS[i])}</span></button>'
        )
    markup = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sonetto · 360° 结构参考</title>
<style>
:root{font-family:system-ui,"Noto Sans CJK SC",sans-serif;background:#0e1726;color:#eaf0f8;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0}
header{background:#152235;border-bottom:1px solid #34475f;padding:18px max(20px,4vw)}
h1{font-size:23px;margin:0 0 6px}
.header-sub{color:#afbed1;font-size:13px}
main{margin:0 auto;max-width:1480px;padding:20px;display:grid;grid-template-columns:2fr 1fr;gap:18px}
section,aside{background:#152235;border:1px solid #394d65;border-radius:14px;padding:16px}
h2{font-size:16px;margin:0 0 13px}
.stage{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.stage-card{min-width:0}
.stage-title{font-size:13px;color:#c2d1e0;text-align:center;margin:8px}
canvas{display:block;width:100%;aspect-ratio:1;border-radius:10px;
background-color:#e7ecf3;
background-image:linear-gradient(45deg,#dce3ee 25%,transparent 25%),linear-gradient(-45deg,#dce3ee 25%,transparent 25%),
linear-gradient(45deg,transparent 75%,#dce3ee 75%),linear-gradient(-45deg,transparent 75%,#dce3ee 75%);
background-size:22px 22px;background-position:0 0,0 11px,11px -11px,-11px 0}
.controls{margin-top:20px}
.range-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:7px}
input[type="range"]{width:100%;accent-color:#81b8ff}
.ticks{display:flex;justify-content:space-between;font-size:12px;color:#a9bed3}
.buttons{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
button{background:#273a56;border:1px solid #526985;border-radius:8px;color:#eaf0f8;font:inherit;min-height:34px;padding:6px 12px;cursor:pointer}
button:hover,button.active{background:#275782;border-color:#87b6e5}
button:focus-visible{outline:3px solid #91d1fc}
.small{font-size:12px;color:#b9c9da}
pre{white-space:pre-wrap;font-size:12px;overflow-wrap:anywhere;background:#0e1c2d;border-radius:8px;padding:11px}
#angles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}
.angle{padding:4px;text-align:center;min-width:0}
.angle img{width:100%;aspect-ratio:1;object-fit:contain;background:#e7ecf3;border-radius:5px}
.angle span{font-size:10px;display:block;padding:3px 0}
footer{padding:10px max(20px,4vw) 25px;color:#a4b6c9;font-size:12px;line-height:1.7}
.note{border-left:3px solid #8dafda;padding-left:12px;color:#d1dbea;line-height:1.55}
@media(max-width:950px){main{grid-template-columns:1fr}#angles{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:520px){main{padding:10px}.stage{grid-template-columns:1fr}#angles{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
</head>
<body>
<header><h1>Sonetto · 360° 结构参考</h1>
<div class="header-sub">2.75D Anime Studio · 八方向正交视图 · PMX → Blender → RGBA · 离线 HTML 验收</div></header>
<main>
<section>
<h2>视角对照</h2>
<div class="stage">
<div class="stage-card"><canvas id="front" width="768" height="768" aria-label="Front reference"></canvas><div class="stage-title">0° · 正面结构基准</div></div>
<div class="stage-card"><canvas id="selected" width="768" height="768" aria-label="Selected reference"></canvas><div id="selectedLabel" class="stage-title">0° · 当前视角</div></div>
</div>
<div class="controls">
<div class="range-header"><label for="yaw">水平转向</label><strong id="yawLabel">0°</strong></div>
<input id="yaw" type="range" min="0" max="360" step="1" value="0">
<div class="ticks"><span>0°</span><span>90°</span><span>180°</span><span>270°</span><span>360°</span></div>
<div class="buttons">
<button id="previous" type="button">上一关键视角</button>
<button id="play" type="button">播放旋转</button>
<button id="next" type="button">下一关键视角</button>
<button id="mode" type="button">模式：关键帧</button>
<button id="png" type="button">导出当前 PNG</button>
</div>
<p id="modeInfo" class="small">关键帧模式：显示最接近的真实 3D 正交渲染角度。方向中间值可切换为交叉溶解预览。</p>
</div>
</section>
<aside>
<h2>八方向检视</h2>
<div id="angles">__FRAME_BUTTONS__</div>
<h2 style="margin-top:20px">验收信息</h2>
<pre id="state">加载中</pre>
<p class="note">本页用于核对脸部侧轮廓、鼻尖、耳廓、后脑体积、发束与服装结构。中间角度的交叉溶解是图像混合，不是 VDD 网格形变。</p>
<p class="small">视角图为三维结构参考；独立绘制的二维分层原画单独登记及验收。</p>
</aside>
</main>
<footer>角色及原画 © BLUEPOCH / Reverse: 1999。第三方三维模型制作：WTHN_Ross。当前使用为个人非商业结构研究；PMX 模型及纹理文件不包含在本 HTML 中。</footer>
<script>
(() => {
 'use strict';
 const images = [...document.querySelectorAll('#angles img')];
 const slider=document.getElementById('yaw');
 const label=document.getElementById('yawLabel');
 const selectedLabel=document.getElementById('selectedLabel');
 const out=document.getElementById('state');
 const front=document.getElementById('front').getContext('2d');
 const chosen=document.getElementById('selected').getContext('2d');
 const keys=[0,45,90,135,180,225,270,315];
 let dissolve=false,playing=false,start=null,initialYaw=0,ready=false;
 const norm=y=>((y%360)+360)%360;
 function render(){
   if(!ready)return;
   const y=Number(slider.value),normalized=norm(y);
   const a=Math.floor(normalized/45)%8,b=(a+1)%8,blend=(normalized-a*45)/45;
   const nearest=blend<0.5?a:b;
   chosen.clearRect(0,0,768,768);chosen.globalAlpha=1;
   if(dissolve){
     chosen.globalAlpha=1-blend;chosen.drawImage(images[a],0,0,768,768);
     chosen.globalAlpha=blend;chosen.drawImage(images[b],0,0,768,768);
     chosen.globalAlpha=1;
   }else{chosen.drawImage(images[nearest],0,0,768,768);}
   label.textContent=y+'°';
   selectedLabel.textContent=y+'° · '+(dissolve?'参考图像混合':'最近 3D 关键帧');
   for(const btn of document.querySelectorAll('.angle')){
    btn.classList.toggle('active',Number(btn.dataset.yaw)===((dissolve?a:nearest)*45));
   }
   const keyYaw=(dissolve?a:nearest)*45;
   out.textContent='参考角度：'+keyYaw+'°\n观察角度：'+y+'°\n呈现模式：'+(dissolve?'相邻图像交叉溶解':'最近真实 3D 关键帧')+
    '\n结构来源：WTHN_Ross PMX\n图像规格：768 × 768 RGBA\n来源类别：三维结构参考\n独立二维原画：待登记';
 }
 function setYaw(angle){
   slider.value=String((angle+360)%361);
   render();
 }
 function playLoop(t){
  if(!playing)return;
  if(start===null){start=t;initialYaw=Number(slider.value);}
  setYaw(Math.floor((initialYaw+(t-start)*0.03)%360));
  requestAnimationFrame(playLoop);
 }
 function togglePlay(){
  playing=!playing;start=null;
  document.getElementById('play').textContent=playing?'暂停旋转':'播放旋转';
  if(playing)requestAnimationFrame(playLoop);
 }
 slider.addEventListener('input',render);
 document.getElementById('previous').addEventListener('click',()=>setYaw(Math.floor((Number(slider.value)-1)/45)*45));
 document.getElementById('next').addEventListener('click',()=>setYaw((Math.floor(Number(slider.value)/45)+1)*45%360));
 document.getElementById('play').addEventListener('click',togglePlay);
 document.getElementById('mode').addEventListener('click',()=>{
  dissolve=!dissolve;
  document.getElementById('mode').textContent='模式：'+(dissolve?'交叉溶解':'关键帧');
  document.getElementById('modeInfo').textContent=dissolve?
    '交叉溶解用于检查轮廓对齐，不能替代 VDD 的逐器官运动和遮挡处理。':
    '关键帧模式显示真实采集的 3D 正交参考图。';
  render();
 });
 document.getElementById('png').addEventListener('click',()=>{
  const c=document.getElementById('selected');
  c.toBlob(blob=>{
   if(!blob)return;
   const url=URL.createObjectURL(blob),a=document.createElement('a');
   a.download='sonetto-structural-yaw'+slider.value+'.png';
   a.href=url;document.body.appendChild(a);a.click();a.remove();
   setTimeout(()=>URL.revokeObjectURL(url),500);
  },'image/png');
 });
 for(const btn of document.querySelectorAll('.angle')){
  btn.addEventListener('click',()=>setYaw(Number(btn.dataset.yaw)));
 }
 document.addEventListener('keydown',e=>{
  if(e.key==='ArrowLeft')setYaw(Number(slider.value)-5);
  else if(e.key==='ArrowRight')setYaw(Number(slider.value)+5);
  else if(e.code==='Space'&&e.target.tagName!=='BUTTON'){e.preventDefault();togglePlay();}
 });
 Promise.all(images.map(img=>img.decode())).then(()=>{
  ready=true;front.drawImage(images[0],0,0,768,768);render();
  window.__R1999_REFERENCE={inspect:()=>({ready,angle:Number(slider.value),dissolve,playing,imageCount:images.length}),
    setYaw,render,togglePlay};
 }).catch(e=>{out.textContent='参考图加载失败：'+e.message});
})();
</script>
</body></html>
"""
    markup = markup.replace("__FRAME_BUTTONS__", "\n".join(cards))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markup, encoding="utf-8")
    print(json.dumps({"output": str(output), "bytes": output.stat().st_size,
                      "frames": len(frames), "offline": True}))


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--views-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args=p.parse_args()
    build(args.views_dir.resolve(), args.output.resolve())
