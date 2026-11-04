(() => {
'use strict';
const PARTS=['hair.back','face.skin','ear.near','hair.side','eye.near','nose','mouth','hair.front'];
const DEPTH={ 'hair.back':-30,'face.skin':0,'ear.near':5,'hair.side':8,
 'eye.near':12,'nose':15,'mouth':16,'hair.front':30};
const SIZE=640;
const GEOMETRY_NAMES={
 45:'yaw045_three_quarter.png',
 90:'yaw090_profile.png'
};
const geometryImages=new Map();
let geometryReferenceStatus='LOADING';
async function loadGeometryReference(){
 const loads=Object.entries(GEOMETRY_NAMES).map(([yaw,file])=>new Promise(resolve=>{
  const img=new Image();
  img.onload=()=>{geometryImages.set(Number(yaw),img);resolve(true);};
  img.onerror=()=>resolve(false);
  img.src='./private-geometry-view/'+encodeURIComponent(file);
 }));
 const ok=await Promise.all(loads);
 geometryReferenceStatus=ok.every(Boolean)?'AVAILABLE':'PARTIAL';
 refreshGeometryReference();
}
function refreshGeometryReference(){
 const canvas=document.getElementById('geometryRef');
 if(!canvas)return;
 const ctx=canvas.getContext('2d');
 ctx.clearRect(0,0,SIZE,SIZE);
 const yaw=Number(document.getElementById('yaw').value);
 const nearest=yaw<=67?45:90;
 const img=geometryImages.get(nearest);
 const label=document.getElementById('geometryHint');
 if(img){
  ctx.drawImage(img,0,0,SIZE,SIZE);
  label.textContent='相机参考 '+nearest+'° · PMX 正交渲染 · '+img.width+'×'+img.height;
 }else{
  label.textContent='三维结构参考图片读取中 · '+geometryReferenceStatus;
 }
}

const NATIVE_PARTS={
 'face.skin':'__UNPARENTED_DRAWABLES__',
 'eye.near':'PARTS_01_EYE_001',
 'nose':'PARTS_01_NOSE_001',
 'mouth':'PARTS_01_MOUTH_001',
 'ear.near':'PARTS_01_EAR_001',
 'hair.front':'PARTS_01_HAIR_FRONT_001',
 'hair.side':'PARTS_01_HAIR_SIDE_001',
 'hair.back':'PARTS_01_HAIR_BACK_001'
};
let nativeManifest=null;
let nativeRefStatus='LOADING';
async function refreshNative(){
 const ctx=document.getElementById('nativeRef').getContext('2d');
 ctx.clearRect(0,0,640,640);
 const entry=nativeManifest?.entries?.find(e=>e.partId===NATIVE_PARTS[part.value]);
 if(!entry){
  document.getElementById('nativeHint').textContent=nativeRefStatus==='LOADING'?'读取私有图层中':'私有 Cubism 图层待接入';
  return;
 }
 const image=new Image();
 image.onload=()=>{
  ctx.clearRect(0,0,640,640);ctx.drawImage(image,0,0);
  document.getElementById('nativeHint').textContent=entry.partId+' · '+entry.drawableCount+' Drawables · SHA '+entry.sha256.slice(0,10);
 };
 image.onerror=()=>{
  document.getElementById('nativeHint').textContent='原生参考图层读取失败';
 };
 image.src='./private-view-assets/'+encodeURIComponent(entry.filename);
}
async function loadNative(){
 try{
  const response=await fetch('./private-view-assets/front-layer-manifest.json');
  if(!response.ok)throw Error('private assets missing');
  nativeManifest=await response.json();
  nativeRefStatus='AVAILABLE';
 }catch(e){nativeRefStatus='UNAVAILABLE';}
 await refreshNative();
}

const viewKeys=new Map([[45,new Map()],[90,new Map()]]);
const $=id=>document.getElementById(id);
const yaw=$('yaw'),yawLabel=$('yawLabel'),part=$('part'),view=$('view');
for(const id of PARTS){const item=document.createElement('option');item.value=id;item.textContent=id;part.appendChild(item);}
const blend=t=>{const q=Math.min(1,Math.max(0,t));return q*q*(3-2*q);};
function bbox(image){
 const c=document.createElement('canvas');c.width=SIZE;c.height=SIZE;
 const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(image,0,0,SIZE,SIZE);
 const pixels=ctx.getImageData(0,0,SIZE,SIZE).data;
 let minX=SIZE,minY=SIZE,maxX=-1,maxY=-1,total=0,solid=0;
 for(let y=0;y<SIZE;y++)for(let x=0;x<SIZE;x++){
  const a=pixels[(y*SIZE+x)*4+3];if(a===0)continue;
  total++;if(a>230)solid++;
  minX=Math.min(x,minX);minY=Math.min(y,minY);
  maxX=Math.max(x,maxX);maxY=Math.max(y,maxY);
 }
 return total?{left:minX,top:minY,right:maxX+1,bottom:maxY+1,pixels:total,opaque:solid}:null;
}
function quad(b){return [[b.left,b.top],[b.right,b.top],[b.right,b.bottom],[b.left,b.bottom]];}
function lerpQuad(a,b,t){return a.map((p,i)=>[p[0]+(b[i][0]-p[0])*t,p[1]+(b[i][1]-p[1])*t]);}
function affine(ctx,image,src,dst,alpha){
 for(const tri of [[0,1,2],[0,2,3]]){
  const [i0,i1,i2]=tri,[p0,p1,p2]=[src[i0],src[i1],src[i2]],
   [q0,q1,q2]=[dst[i0],dst[i1],dst[i2]];
  const u1=p1[0]-p0[0],v1=p1[1]-p0[1],u2=p2[0]-p0[0],v2=p2[1]-p0[1];
  const denominator=u1*v2-u2*v1;
  if(Math.abs(denominator)<1e-8)continue;
  const a=((q1[0]-q0[0])*v2-(q2[0]-q0[0])*v1)/denominator;
  const c=(u1*(q2[0]-q0[0])-u2*(q1[0]-q0[0]))/denominator;
  const b=((q1[1]-q0[1])*v2-(q2[1]-q0[1])*v1)/denominator;
  const d=(u1*(q2[1]-q0[1])-u2*(q1[1]-q0[1]))/denominator;
  const e=q0[0]-a*p0[0]-c*p0[1],f=q0[1]-b*p0[0]-d*p0[1];
  ctx.save();ctx.beginPath();ctx.moveTo(...q0);ctx.lineTo(...q1);ctx.lineTo(...q2);ctx.closePath();ctx.clip();
  ctx.globalAlpha=alpha;ctx.setTransform(a,b,c,d,e,f);
  ctx.drawImage(image,0,0);ctx.restore();
 }
}
function render(canvasId,angle){
 const canvas=$(canvasId),ctx=canvas.getContext('2d');
 ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,SIZE,SIZE);
 const a=viewKeys.get(45),b=viewKeys.get(90),t=blend((angle-45)/45);
 let visible=0,hasBoth=0;
 for(const id of [...PARTS].sort((x,y)=>DEPTH[x]-DEPTH[y])){
  const ka=a.get(id),kb=b.get(id);
  if(!ka&&!kb)continue;
  if(ka&&kb)hasBoth++;
  const xa=ka||kb,xb=kb||ka;
  const from=quad(xa.bbox),to=quad(xb.bbox);
  const target=lerpQuad(from,to,t);
  if(ka&&kb){
   // Blend only matching semantic parts, after local triangulated deformation.
   affine(ctx,ka.image,quad(ka.bbox),target,1-t);
   affine(ctx,kb.image,quad(kb.bbox),target,t);
  }else{
   const key=ka||kb;
   affine(ctx,key.image,quad(key.bbox),target,ka?(1-t):t);
  }
  visible++;
 }
 return {angle,visible,pairedSemanticParts:hasBoth};
}
let last={};
function refresh(){
 const value=Number(yaw.value);yawLabel.textContent=value+'°';
 const left=render('left',45),center=render('center',value),right=render('right',90);
 $('middleLabel').textContent='局部插值预览 · '+value+'°';
 const n45=viewKeys.get(45).size,n90=viewKeys.get(90).size;
 const synthetic=[...viewKeys.values()].flatMap(v=>[...v.values()]).filter(v=>v.role==='synthetic_fixture').length;
 const candidate=[...viewKeys.values()].flatMap(v=>[...v.values()]).filter(v=>v.role==='candidate_art').length;
 const proxy=[...viewKeys.values()].flatMap(v=>[...v.values()]).filter(v=>v.role==='third_party_3d_proxy').length;
 last={angle:value,keys45:n45,keys90:n90,paired:center.pairedSemanticParts,synthetic,candidate,proxy,
  requiredPairs:PARTS.length,visualAcceptance:'AWAITING_VALIDATED_INDEPENDENT_ART',
  renderer:'Canvas2D semantic-part triangulated warp'};
 $('viewStatus').textContent='45° 图层：'+n45+'/8\n90° 图层：'+n90+'/8\n匹配器官：'+center.pairedSemanticParts+'/8\n几何测试：'+synthetic+'，PMX 代理：'+proxy+'，导入候选：'+candidate;
 $('summary').textContent=JSON.stringify(last);
 return last;
}
function makeFixture(angle,id){
 const canvas=document.createElement('canvas');canvas.width=SIZE;canvas.height=SIZE;
 const ctx=canvas.getContext('2d'),i=PARTS.indexOf(id);
 const cx=285+angle/5+i*4,cy=258+i*9;
 ctx.fillStyle=['#c86e43','#f1c7b3','#c9876e','#ad532d','#e9c9b5','#b77a6b','#b96267','#d98243'][i];
 ctx.strokeStyle='#593d49';ctx.lineWidth=3;
 ctx.beginPath();
 ctx.ellipse(cx,cy,18+i*8,20+(i%4)*13,angle*Math.PI/700,0,Math.PI*2);
 ctx.fill();ctx.stroke();
 ctx.fillStyle='rgba(255,255,255,.50)';
 ctx.fillRect(cx-7,cy-5,5,6);
 return canvas;
}
function loadFixture(){
 for(const angle of [45,90])for(const id of PARTS){
  const image=makeFixture(angle,id),bounds=bbox(image);
  viewKeys.get(angle).set(id,{image,bbox:bounds,role:'synthetic_fixture',sourceId:'geometry-fixture-'+angle+'-'+id,sha256:null});
 }
 refresh();return inspect();
}

async function loadProxyLayers(){
 const root='./private-proxy-layers/';
 const response=await fetch(root+'proxy-semantic-manifest.json');
 if(!response.ok)throw Error('Proxy manifest unavailable');
 const manifest=await response.json();
 if(manifest.schema!=='R1999-PMX-SEMANTIC-PROXY-V1' ||
    manifest.sourceRole!=='third_party_3d_proxy' ||
    manifest.independentArtCoverage!==0 ||
    manifest.layers?.length!==16)throw Error('Proxy provenance/coverage contract rejected');
 const staged=new Map([[45,new Map()],[90,new Map()]]);
 await Promise.all(manifest.layers.map(async record=>{
  const angle=record.yawDeg, id=record.semanticId;
  if(![45,90].includes(angle) || !PARTS.includes(id) ||
     record.role!=='third_party_3d_proxy' ||
     !/^yaw(?:045|090)_[a-z.]+\.png$/.test(record.path) ||
     !/^[0-9a-f]{64}$/.test(record.sha256))throw Error('Proxy part identity invalid');
  if(staged.get(angle).has(id))throw Error('Duplicate semantic proxy');
  const resp=await fetch(root+encodeURIComponent(record.path));
  if(!resp.ok)throw Error('Missing semantic PNG: '+record.path);
  const buffer=await resp.arrayBuffer();
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer)))
    .map(v=>v.toString(16).padStart(2,'0')).join('');
  if(digest!==record.sha256)throw Error('Proxy checksum failed: '+record.path);
  const image=await createImageBitmap(new Blob([buffer],{type:'image/png'}));
  if(image.width!==SIZE || image.height!==SIZE)throw Error('Proxy canvas size invalid');
  const bounds=bbox(image);
  if(!bounds || bounds.pixels<25)throw Error('Empty proxy: '+record.path);
  if(bounds.left<=0 || bounds.top<=0 || bounds.right>=SIZE || bounds.bottom>=SIZE)
   throw Error('Proxy alpha touches canvas border');
  staged.get(angle).set(id,{image,bbox:bounds,role:'third_party_3d_proxy',
     sha256:digest,sourceId:record.sourceId});
 }));
 if(staged.get(45).size!==8 || staged.get(90).size!==8)
   throw Error('Eight semantic IDs required per camera view');
 for(const angle of [45,90]){
  viewKeys.get(angle).clear();
  for(const [id,layer] of staged.get(angle))viewKeys.get(angle).set(id,layer);
 }
 refresh();
 return inspect();
}

async function importFile({angle,id,file,sourceId}){
 if(![45,90].includes(angle)||!PARTS.includes(id))throw Error('Invalid view or part');
 if(file.type!=='image/png')throw Error('Expected PNG image');
 if(!sourceId?.trim())throw Error('Source ID required');
 if(file.size>18*1024*1024)throw Error('Image exceeds 18 MB');
 const image=await createImageBitmap(file);
 if(image.width!==SIZE||image.height!==SIZE)throw Error('Expected 640 × 640 image');
 const bounds=bbox(image);
 if(!bounds||bounds.pixels>SIZE*SIZE*0.85)throw Error('Invalid anatomical alpha layer');
 if(bounds.left===0||bounds.top===0||bounds.right===SIZE||bounds.bottom===SIZE)
  throw Error('Artwork needs transparent margins');
 const bytes=await file.arrayBuffer();
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');
 viewKeys.get(angle).set(id,{image,bbox:bounds,role:'candidate_art',sourceId:sourceId.trim(),sha256:digest});
 refresh();return {angle,semanticId:id,sourceId,sha256:digest,bbox:bounds,role:'candidate_art'};
}
function inspect(){return {...last};}
function exportRegistry(){
 const records=[];
 for(const [angle,group] of viewKeys.entries())for(const [semanticId,k] of group.entries())
  records.push({yawDeg:angle,semanticId,sourceId:k.sourceId,sha256:k.sha256,role:k.role,
   bbox:k.bbox,visualReviewed:false,partKeyComplete:false,sourceProvenance:'requires_cli_validation'});
 return {schema:'R1999-ARTWORK-LAB-REGISTER-V1',records,visualAcceptance:'AWAITING_VALIDATED_INDEPENDENT_ART'};
}
function downloadRegistry(){
 const json=JSON.stringify(exportRegistry(),null,2);
 const blob=new Blob([json],{type:'application/json'}),url=URL.createObjectURL(blob);
 const a=document.createElement('a');a.href=url;a.download='r1999-view-layer-register.json';a.click();
 setTimeout(()=>URL.revokeObjectURL(url),300);
}
$('yaw').addEventListener('input',()=>{refresh();refreshGeometryReference();});
part.addEventListener('change',refreshNative);
$('fixture').addEventListener('click',loadFixture);
$('proxy').addEventListener('click',async()=>{
 try{await loadProxyLayers();}
 catch(error){$('viewStatus').textContent='PMX 代理读取失败：'+String(error.message||error);}
});
$('import').addEventListener('click',async()=>{
 try{
  const file=$('artFile').files?.[0];
  if(!file)throw Error('Choose a PNG file');
  await importFile({angle:Number(view.value),id:part.value,file,sourceId:$('sourceId').value});
 }catch(e){$('viewStatus').textContent='导入检查：'+String(e.message||e);}
});
$('export').addEventListener('click',downloadRegistry);
window.__R1999_LAYER_LAB={inspect,loadFixture,loadProxyLayers,importFile,exportRegistry,renderAt:(angle)=>render('center',angle)};
refresh();loadNative();loadGeometryReference();
})();