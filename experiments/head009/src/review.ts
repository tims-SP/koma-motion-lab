import './main';
import type {Point} from './art';
import {predictViewLandmarks,compareViewLandmarks,type OrganLandmarks} from './organ-register';
type Runtime=Window & {
 head009:{frame:(yaw:number,pass?:number)=>void;qa:(yaw:number)=>unknown;probeParts:(yaw:number,points:Record<string,Point>,p:Record<string,string>)=>unknown};
 __HEAD009_REFS?:Record<string,string>;
 __HEAD009_ORGAN?:OrganLandmarks;
 __HEAD009_READY?:boolean;
};
const w=window as Runtime;
const refs=w.__HEAD009_REFS??{};
const register=w.__HEAD009_ORGAN as OrganLandmarks;
if(!register)throw Error('Missing embedded original organ landmarks');
const byId=<T extends HTMLElement>(id:string)=>{const el=document.getElementById(id);if(!el)throw Error('Missing #'+id);return el as T};
const slider=byId<HTMLInputElement>('yaw'), output=byId<HTMLOutputElement>('angleOut');
const pass=byId<HTMLSelectElement>('pass'),play=byId<HTMLButtonElement>('play');
const marks=byId<HTMLCanvasElement>('marks'),refMarks=byId<HTMLCanvasElement>('refMarks');
const keys=[0,30,45,60,75,90], shortLabel=(s:string)=>s.replace(/\.center$/,'').replace('fringe.','hair.');
const reviewKeys=['eyes','nose','mouth','jaw','ears','hair','occlusion','overall'] as const;
type ReviewStatus='pending'|'pass'|'rework';
const manualReview:Record<string,ReviewStatus>=Object.fromEntries(reviewKeys.map(k=>[k,'pending'])) as Record<string,ReviewStatus>;
let yaw=0,playing=false,raf=0,previous=0,reviewData:unknown=null;
const raw=(v:number)=>Math.max(0,Math.min(90,Math.round(v)));
const sourceAt=(angle:number)=>register.views.find(x=>x.yaw===angle)!;
const referenceAngle=(angle:number)=>keys.reduce((a,b)=>Math.abs(a-angle)<=Math.abs(b-angle)?a:b);
const renderPoint=(ctx:CanvasRenderingContext2D,p:Point,color:string,radius=4)=>{
 ctx.fillStyle=color;ctx.strokeStyle='#101827';ctx.lineWidth=1.7;
 ctx.beginPath();ctx.arc(p[0],p[1],radius,0,Math.PI*2);ctx.fill();ctx.stroke();
};
function overlay(){
 const ctx=marks.getContext('2d')!,rc=refMarks.getContext('2d')!;
 ctx.clearRect(0,0,640,640);rc.clearRect(0,0,640,640);
 if(!byId<HTMLInputElement>('landmarks').checked)return;
 const projected=predictViewLandmarks(register,yaw);
 for(const pt of Object.values(projected))renderPoint(ctx,pt,'#ffe36f');
 const source=sourceAt(referenceAngle(yaw));
 if(source.yaw===yaw){
  for(const pt of Object.values(source.points))renderPoint(rc,[pt[0]*1.25,pt[1]*1.25],'#6ee7ff');
 }
}
function updateReference(){
 const angle=referenceAngle(yaw),v=sourceAt(angle),s=refs[v.source];
 const img=byId<HTMLImageElement>('refImage');
 img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(s);
 byId('refLabel').textContent=angle+'° '+(angle===yaw?'对位':'最近参考');
 byId('refAngleCell').textContent=angle+'°';
 const refMatch=angle===yaw;
 byId('referenceNote').textContent=refMatch?(v.role==='key'?'关键视角源原画':'当前开发参考（仅用于诊断）'):'当前没有同角度独立原画；右侧显示 '+angle+'° 参考，不能用于同角度误差评定';
 if(!refMatch){byId('meanCell').textContent='未测量';byId('maxCell').textContent='未测量';byId('organTable').textContent='选择 0° / 30° / 45° / 60° / 75° / 90° 查看对应原画标注';return;}
 const comp=compareViewLandmarks(register,yaw);
 byId('meanCell').textContent=comp.meanErrorPx?.toFixed(1)+'px';
 byId('maxCell').textContent=comp.maxErrorPx?.toFixed(1)+'px';
 const vals=Object.entries(comp.errors);
 byId('organTable').innerHTML='<table><thead><tr><th>器官语义点</th><th>位置偏差</th></tr></thead><tbody>'+
 vals.map(([k,v])=>'<tr><td>'+shortLabel(k)+'</td><td>'+(v.errorPx<0?'缺少对应':v.errorPx.toFixed(1)+'px')+'</td></tr>').join('')+'</tbody></table>';
}
function draw(){
 w.head009.frame(yaw,Number(pass.value));
 output.textContent=yaw+'°';byId('angleCell').textContent=yaw+'°';slider.value=String(yaw);
 byId('renderLabel').textContent=pass.selectedOptions[0].textContent??'Beauty';
 for(const btn of Array.from(document.querySelectorAll<HTMLButtonElement>('#keyAngles button')))btn.classList.toggle('active',Number(btn.dataset.yaw)===yaw);
 updateReference();overlay();
}
function setYaw(next:number){yaw=raw(next);draw();byId('qaStatus').textContent='当前角度的 QA 尚未执行';byId('log').textContent='';reviewData=null;}
function stop(){playing=false;cancelAnimationFrame(raf);play.textContent='播放旋转';}
function tick(now:number){
 if(!playing)return;
 if(!previous)previous=now;
 if(now-previous>=38){previous=now;setYaw(yaw>=90?0:yaw+1);}
 raf=requestAnimationFrame(tick);
}
function togglePlay(){playing=!playing;play.textContent=playing?'暂停旋转':'播放旋转';previous=0;if(playing)raf=requestAnimationFrame(tick);else cancelAnimationFrame(raf);}
function save(name:string,data:string,type:string){
 const url=URL.createObjectURL(new Blob([data],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
slider.addEventListener('input',()=>{stop();setYaw(Number(slider.value));});
pass.addEventListener('change',draw);
const manualContainer=byId('manualReview');
for(const key of reviewKeys){
 const label=document.createElement('label');label.className='review-control';
 label.textContent=({eyes:'眼睛',nose:'鼻子',mouth:'嘴巴 / 口腔',jaw:'下巴 / 面颊',ears:'耳朵',hair:'头发',occlusion:'深度 / 遮挡',overall:'整体视觉质量'} as Record<string,string>)[key];
 const select=document.createElement('select');select.dataset.organ=key;
 for(const [value,text] of [['pending','待验收'],['pass','通过'],['rework','需修正']]){const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);}
 select.addEventListener('change',()=>{manualReview[key]=select.value as ReviewStatus});
 label.append(select);manualContainer.append(label);
}
byId('prev').addEventListener('click',()=>{stop();setYaw(yaw-1)});
byId('next').addEventListener('click',()=>{stop();setYaw(yaw+1)});
for(const btn of Array.from(document.querySelectorAll<HTMLButtonElement>('#keyAngles button')))btn.addEventListener('click',()=>{stop();setYaw(Number(btn.dataset.yaw))});
play.addEventListener('click',togglePlay);
byId('landmarks').addEventListener('change',overlay);
byId('showRef').addEventListener('change',()=>{byId('refPanel').style.display=byId<HTMLInputElement>('showRef').checked?'':'none'});
document.addEventListener('keydown',ev=>{
 if(ev.target instanceof HTMLInputElement || ev.target instanceof HTMLSelectElement)return;
 if(ev.key==='ArrowRight'){ev.preventDefault();stop();setYaw(yaw+1)}
 if(ev.key==='ArrowLeft'){ev.preventDefault();stop();setYaw(yaw-1)}
 if(ev.key===' '){ev.preventDefault();togglePlay()}
});
byId('runQa').addEventListener('click',()=>{
 stop();const mode=Number(pass.value);
 const result=w.head009.qa(yaw);reviewData=result;
 w.head009.frame(yaw,mode);overlay();
 const state=(result as {result:string}).result;
 byId('qaStatus').textContent='当前角度 '+yaw+'°：'+state;
 byId('log').textContent=JSON.stringify(result,null,2);
});
byId('saveShot').addEventListener('click',()=>{
 const c=document.createElement('canvas');c.width=640;c.height=640;const ctx=c.getContext('2d')!;
 ctx.drawImage(byId<HTMLCanvasElement>('stage'),0,0);ctx.drawImage(marks,0,0);
 const a=document.createElement('a');a.download='head009-'+String(yaw).padStart(3,'0')+'-review.png';a.href=c.toDataURL('image/png');a.click();
});
byId('saveReport').addEventListener('click',()=>{
 const payload={schema:'HEAD009-HTML-REVIEW-V1',yaw,renderPass:Number(pass.value),timestamp:new Date().toISOString(),
 source:sourceAt(referenceAngle(yaw)).source,sourceAngle:referenceAngle(yaw),
 sourceReferenceRole:sourceAt(referenceAngle(yaw)).role,hasSameAngleReference:keys.includes(yaw),
 landmarkComparison:keys.includes(yaw)?compareViewLandmarks(register,yaw):null,
 realPixelQa:reviewData,manualReview:{...manualReview},manualReviewComplete:Object.values(manualReview).every(v=>v!=='pending')};
 save('head009-'+String(yaw).padStart(3,'0')+'-review.json',JSON.stringify(payload,null,2),'application/json');
});
w.__HEAD009_READY=true;
byId('loadStatus').textContent='离线可用 · 实时 WebGL';
draw();
