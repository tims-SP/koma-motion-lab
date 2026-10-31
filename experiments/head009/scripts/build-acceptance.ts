import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {join} from 'node:path';
import {build} from 'esbuild';
const outputDir='out/head009';
const refNames=['front-000.svg','threequarter-045.svg','profile-right-090.svg',
 'heldout-030.svg','heldout-060.svg','heldout-075.svg'];
const refs:Record<string,string>={};
for(const name of refNames)refs[name]=await readFile(join('reference',name),'utf8');
const register=JSON.parse(await readFile('reference/organ-landmarks.json','utf8'));
const bundled=await build({
 entryPoints:['src/acceptance.ts'],bundle:true,write:false,platform:'browser',format:'esm',
 target:'chrome120',minify:true,logLevel:'warning',legalComments:'none',
});
const source=bundled.outputFiles?.[0]?.text;
if(!source||source.length<10000)throw Error('Three.js renderer bundle absent');
const safe=(value:unknown)=>JSON.stringify(value).replace(/</g,'\\u003c').replace(/>/g,'\\u003e');
const html=`<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HEAD009 · 头部交互验收</title>
<style>
:root{color-scheme:dark;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#10141e;color:#e8edf5}
*{box-sizing:border-box}body{margin:0}.app{max-width:1500px;margin:auto;padding:20px}
header{display:flex;align-items:start;justify-content:space-between;gap:16px;margin-bottom:18px}
h1{font-size:24px;margin:0 0 6px}h2{font-size:16px;margin:0 0 12px}small,.muted{color:#aeb9ca}
main{display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,340px);gap:18px}
.panels{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel,.controls,.section{background:#192231;border:1px solid #344459;border-radius:12px;padding:14px}
.render{position:relative;aspect-ratio:1;background:#293249;width:100%;overflow:hidden;border-radius:8px}
.render>canvas,.render>img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
.render>#stage,.render>#reference{z-index:0}.render>canvas.overlay{z-index:1;pointer-events:none}
.controls{margin-top:16px}.slider-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px}
input[type=range]{width:100%;accent-color:#83c4ec}
.steps,.modes{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px}
button,select{border:1px solid #53647c;border-radius:7px;background:#26364a;color:#f4f7fb;padding:8px 11px;font:inherit;cursor:pointer}
button:hover,button.selected{border-color:#83c4ec;background:#345878}
button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid #8fd2f0;outline-offset:3px}
aside{display:flex;flex-direction:column;gap:14px}.review-row{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:5px 0;border-bottom:1px solid #344459}
.review-row select{width:126px}.button-main{background:#315c75}.machine[data-status="PASS_ENGINEERING"]{color:#97ddbd}
.machine[data-status="FAIL"]{color:#e7a7a7}
.note{font-size:13px;line-height:1.6;color:#becadb;margin:10px 0 0}
.note strong{color:#e5f2ff}.legend{font-size:13px;color:#b8c8d6;margin:8px 0}
#angle-value{font-weight:700;font-size:20px}#metrics,#engine-result{font-size:13px;line-height:1.65;overflow-wrap:anywhere}
@media(max-width:1100px){main{grid-template-columns:1fr}aside{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:680px){.app{padding:10px}.panels{grid-template-columns:1fr}aside{display:block}aside>.section{margin-bottom:12px}header{display:block}h1{font-size:20px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>
</head><body><div class="app">
<header><div><h1>2.75D Anime Studio · HEAD009</h1>
<div class="muted">头部 0°–90° · 多视角分层原画 / ArtMesh / VDD</div></div>
<div id="boot-status" role="status">初始化中</div></header>
<main><div>
<div class="panels">
<section class="panel"><h2>实时 WebGL 形变</h2><div class="render">
<canvas id="stage" width="640" height="640"></canvas>
<canvas id="organ-overlay" class="overlay" width="640" height="640"></canvas></div>
<p class="legend">黄色：原画关键点经过插值与 VDD 的预测位置</p></section>
<section class="panel"><h2>独立绘制的参考原画</h2><div class="render">
<img id="reference" alt="独立绘制的角色角度参考原画">
<canvas id="reference-overlay" class="overlay" width="640" height="640"></canvas></div>
<p class="legend">蓝色：原画标注位置</p><div id="reference-caption" class="muted"></div></section>
</div>
<div class="controls"><div class="slider-head"><strong>水平视角</strong><span id="angle-value">0°</span></div>
<input id="angle" type="range" min="0" max="90" step="1" value="0" aria-label="水平视角">
<div class="steps">
<button data-angle="0">0° 正面</button><button data-angle="15">15°</button>
<button data-angle="30">30°</button><button data-angle="45">45°</button>
<button data-angle="60">60°</button><button data-angle="75">75°</button>
<button data-angle="90">90° 侧面</button></div>
<div class="modes" aria-label="渲染诊断通道">
<button class="selected" data-pass="0">原画渲染</button><button data-pass="1">部件 ID</button>
<button data-pass="2">深度</button><button data-pass="3">Alpha</button></div>
<label style="display:block;margin-top:12px"><input id="markers" type="checkbox" checked> 显示器官语义点</label>
<p class="note">方向键可逐度调整视角。参考图为独立绘制的固定角度；其他角度显示最近参考，不作为逐像素真实目标。</p>
</div></div>
<aside>
<section class="section"><h2>器官注册对照</h2><div id="metrics"></div><hr style="border:0;border-top:1px solid #354358;margin:14px 0">
<button class="button-main" id="run-check">检测当前角度</button>
<div id="engine-result" class="machine" data-status="pending" aria-live="polite" style="margin-top:10px"></div>
<p class="note">工程诊断核对四通道覆盖及故障注入。人工视觉结论独立记录。</p></section>
<section class="section"><h2>器官视觉检查</h2><div id="review-grid"></div>
<button class="button-main" id="export-review" style="margin-top:14px">导出本次验收 JSON</button>
<p class="note"><strong>关注：</strong>近侧眼连续性、鼻梁与鼻尖、嘴部位置、下颌轮廓、耳朵显露过程、发际线和侧发遮挡。</p></section>
<section class="section"><h2>验收范围</h2>
<div class="note">真实 Three.js 渲染与六张原始 SVG 均打包在此文件中。浏览器直接打开即可使用，包含部件层级、角度切换、参考叠加、机器检查及人工记录。当前为头部 0°–90° 技术原型。</div>
</section></aside></main></div>
<script>window.__HEAD009_REFS=${safe(refs)};window.__HEAD009_LANDMARKS=${safe(register)};</script>
<script type="module">${source.replaceAll('</script','<\\/script')}</script>
</body></html>`;
await mkdir(outputDir,{recursive:true});
const path=join(outputDir,'acceptance.html');await writeFile(path,html);
const summary={schema:'HEAD009-HTML-BUILD-V1',file:path,bytes:Buffer.byteLength(html),
 sources:refNames,containsRenderer:html.includes('head009'),offline:true};
await writeFile(join(outputDir,'html-build-manifest.json'),JSON.stringify(summary,null,2)+'\n');
console.log('HEAD009_HTML_BUILD '+JSON.stringify(summary));
