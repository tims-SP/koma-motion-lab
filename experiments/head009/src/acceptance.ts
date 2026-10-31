import './main';
import {compareViewLandmarks,predictViewLandmarks,type OrganLandmarks} from './organ-register';
type RenderMode=0|1|2|3;
type Review='pending'|'pass'|'review'|'fail';
declare global{
 interface Window{
  __HEAD009_REFS?:Record<string,string>;
  __HEAD009_LANDMARKS?:OrganLandmarks;
  headAcceptance?:{setAngle:(angle:number)=>void;runCheck:()=>unknown;getState:()=>unknown};
 }
}
const register=window.__HEAD009_LANDMARKS;
const svg=window.__HEAD009_REFS;
if(!register||!svg)throw Error('Acceptance artwork manifest is missing.');
const $=<T extends HTMLElement=HTMLElement>(id:string):T=>{
 const el=document.getElementById(id);
 if(!el)throw Error('Missing UI element '+id);
 return el as T;
};
const angle=$<HTMLInputElement>('angle');
const angleValue=$('angle-value'),reference=$<HTMLImageElement>('reference');
const refCaption=$('reference-caption'),overlay=$<HTMLCanvasElement>('organ-overlay');
const refOverlay=$<HTMLCanvasElement>('reference-overlay');
const issues=$('review-grid'),metrics=$('metrics'),engine=$('engine-result');
const context=overlay.getContext('2d')!,referenceContext=refOverlay.getContext('2d')!;
const viewChoices=register.views.map(x=>x.yaw).sort((a,b)=>a-b);
const names=Object.keys(register.organParts);
const acceptedNames=['eye','nose','mouth','chin','ear','fringe','face'];
const reviews:Record<string,Review>=Object.fromEntries(acceptedNames.map(x=>[x,'pending']));
let yaw=0,mode:RenderMode=0,showMarkers=true;
let engineReport:unknown=null;
let frameLastRun:number|null=null;
const now=()=>new Date().toISOString();
const buildIssueRows=()=>{
 for(const key of acceptedNames){
  const row=document.createElement('label');row.className='review-row';
  const text=document.createElement('span');text.textContent=key;
  const select=document.createElement('select');select.dataset.review=key;
  for(const [value,label] of [['pending','待检查'],['pass','通过'],['review','需复核'],['fail','不通过']]){
   const opt=document.createElement('option');opt.value=value;opt.textContent=label;select.append(opt);
  }
  select.addEventListener('change',()=>reviews[key]=select.value as Review);
  row.append(text,select);issues.append(row);
 }
};
function annotate(ctx:CanvasRenderingContext2D,x:number,y:number,label:string,color:string){
 if(x<0||x>640||y<0||y>640)return;
 ctx.beginPath();ctx.arc(x,y,4.5,0,2*Math.PI);ctx.fillStyle=color;ctx.fill();
 ctx.strokeStyle='#102332';ctx.lineWidth=1.4;ctx.stroke();
 ctx.font='11px system-ui';ctx.fillStyle=color;ctx.fillText(label,x+7,y-6);
}
function drawMarkers(){
 context.clearRect(0,0,640,640);
 referenceContext.clearRect(0,0,640,640);
 if(!showMarkers)return;
 const predicted=predictViewLandmarks(register,yaw);
 for(const [name,point] of Object.entries(predicted))
  annotate(context,point[0],point[1],name,'#f7ce65');
 const exact=register.views.find(v=>v.yaw===yaw);
 if(exact)for(const [name,point] of Object.entries(exact.points))
  annotate(referenceContext,point[0]*1.25,point[1]*1.25,name,'#5bddf7');
}
function render(){
 const current=register.views.reduce((best,item)=>Math.abs(item.yaw-yaw)<Math.abs(best.yaw-yaw)?item:best,register.views[0]!);
 angle.value=String(yaw);angleValue.textContent=yaw+'°';
 window.head009.frame(yaw,mode);
 const raw=svg[current.source];
 if(!raw)throw Error('Original reference missing '+current.source);
 if(reference.dataset.file!==current.source){
  reference.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(raw);
  reference.dataset.file=current.source;
 }
 const exact=current.yaw===yaw;
 refCaption.textContent=(exact?'当前角度原画':'最近原画，仅用于对照')+' · '+current.yaw+'° · '+(current.role==='key'?'关键视角':'独立留出视角');
 const match=exact?compareViewLandmarks(register,yaw):null;
 metrics.textContent=match?('注册投影：均值 '+match.meanErrorPx?.toFixed(1)+' px · 最大 '+match.maxErrorPx?.toFixed(1)+' px'):'中间角度：显示实时预测点，独立原画仅覆盖已绘制角度';
 drawMarkers();
 engineReport=null;frameLastRun=null;
 engine.textContent='当前角度尚未执行像素诊断';
 engine.dataset.status='pending';
}
function setAngle(value:number){
 yaw=Math.max(0,Math.min(90,Math.round(Number(value)||0)));
 render();
}
function runCheck(){
 const q=window.head009.qa(yaw);
 const predicted=predictViewLandmarks(register,yaw);
 const probe=window.head009.probeParts(yaw,predicted,register.organParts);
 const closest=register.views.find(v=>v.yaw===yaw);
 const landmark=closest?compareViewLandmarks(register,yaw):null;
 window.head009.frame(yaw,mode);
 engineReport={yaw,source:closest?.source??null,coverage:q.coveragePixels,
  mismatch:q.opaqueCoverageMismatches,negativeMaskFault:q.faultMaskCoverageMismatch,
  negativeDepthFault:q.faultDepthIdChangedPixels,visibleParts:q.visibleParts,
  pixelProbes:probe,landmark,engineeringStatus:q.result};
 frameLastRun=yaw;
 engine.textContent=q.result+' · 可见像素 '+q.coveragePixels+
  ' · 通道差异 '+q.opaqueCoverageMismatches.join('/')+
  ' · 故障注入 '+q.faultMaskCoverageMismatch+'/'+q.faultDepthIdChangedPixels;
 engine.dataset.status=q.result;
 return engineReport;
}
function createReport(){
 return {schema:'HEAD009-HTML-ACCEPTANCE-V1',createdAt:now(),sampleAngle:yaw,
  displayPass:['Beauty','Part ID','Depth','Alpha'][mode],
  sourceArt:{keys:[0,45,90],heldOut:[30,60,75]},
  reviews:{...reviews},checks:frameLastRun===yaw?engineReport:null,
  scope:'0-90 head visual review; quantitative checks are engineering diagnostics, not aesthetic approval'};
}
buildIssueRows();
angle.addEventListener('input',()=>setAngle(Number(angle.value)));
document.querySelectorAll<HTMLButtonElement>('[data-angle]').forEach(button=>
 button.addEventListener('click',()=>setAngle(Number(button.dataset.angle))));
document.querySelectorAll<HTMLButtonElement>('[data-pass]').forEach(button=>
 button.addEventListener('click',()=>{
  mode=Number(button.dataset.pass) as RenderMode;
  document.querySelectorAll('[data-pass]').forEach(x=>x.classList.toggle('selected',x===button));
  render();
 }));
$('markers').addEventListener('change',e=>{showMarkers=(e.target as HTMLInputElement).checked;drawMarkers();});
$('run-check').addEventListener('click',runCheck);
$('export-review').addEventListener('click',()=>{
 const blob=new Blob([JSON.stringify(createReport(),null,2)+'\n'],{type:'application/json'});
 const url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download='head009-acceptance-'+String(yaw).padStart(3,'0')+'.json';link.click();
 setTimeout(()=>URL.revokeObjectURL(url),2000);
});
document.addEventListener('keydown',e=>{
 if(e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement)return;
 if(e.key==='ArrowLeft'){e.preventDefault();setAngle(yaw-1);}
 if(e.key==='ArrowRight'){e.preventDefault();setAngle(yaw+1);}
});
window.headAcceptance={setAngle,runCheck,getState:createReport};
setAngle(0);
$('boot-status').textContent='原画与 WebGL 已加载';
document.documentElement.dataset.acceptanceReady='true';
