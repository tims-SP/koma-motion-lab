(() => {
'use strict';
const psdSource=new URLSearchParams(location.search).get('source')==='seethrough';
const ROOT=new URL(psdSource
 ?'../private-assets/p4-see-through/front/integrated/'
 :'../private-assets/p1-front/',location.href);
const size=1024;
const state={loaded:false,parts:[],reference:null,sourceSHA:null,
  manifest:null,qa:null,values:{eyeNear:0,eyeFar:0,fringeX:0},shown:new Set(),error:null};
const byId=x=>document.getElementById(x);
const validSHA=s=>typeof s==='string'&&/^[0-9a-f]{64}$/.test(s);
async function getJSON(rel){
 const r=await fetch(new URL(rel,ROOT),{cache:'no-cache'});
 if(!r.ok)throw Error('manifest missing '+rel+' HTTP '+r.status);
 return r.json();
}
async function loadPNG(rel,expectedSha){
 const url=new URL(rel,ROOT);
 const response=await fetch(url,{cache:'no-cache'});
 if(!response.ok)throw Error('missing PNG '+rel+' HTTP '+response.status);
 const buffer=await response.arrayBuffer();
 const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',buffer));
 const actual=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
 if(expectedSha){
   if(!validSHA(expectedSha)||actual!==expectedSha)throw Error('SHA256 mismatch '+rel);
 }
 const bitmap=await createImageBitmap(new Blob([buffer],{type:'image/png'}));
 if(bitmap.width!==size||bitmap.height!==size)throw Error('global canvas mismatch '+rel);
 return {bitmap,actual};
}
function clear(id){
 const context=byId(id).getContext('2d');
 context.setTransform(1,0,0,1,0,0);
 context.clearRect(0,0,size,size);
 return context;
}
function displaced(semantic){
 if(semantic==='eye.near')return state.values.eyeNear;
 if(semantic==='eye.far')return state.values.eyeFar;
 if(semantic==='hair.front')return state.values.fringeX;
 return 0;
}
function paint(){
 if(!state.loaded)return;
 const context=clear('artmesh');
 for(const part of state.parts){
   if(!state.shown.has(part.semanticId)||part.visibility!=='visible')continue;
   context.drawImage(part.image,displaced(part.semanticId),0);
 }
 const reference=byId('reference').getContext('2d',{willReadFrequently:true});
 const target=byId('artmesh').getContext('2d',{willReadFrequently:true});
 const a=reference.getImageData(0,0,size,size).data;
 const b=target.getImageData(0,0,size,size).data;
 let sum=0,different=0,holes=0;
 for(let i=0;i<a.length;i+=4){
  let pixelDifferent=false;
  for(let k=0;k<4;k++){
   const diff=Math.abs(a[i+k]-b[i+k]);
   sum+=diff;
   if(diff>1)pixelDifferent=true;
  }
  if(pixelDifferent)different++;
  if(a[i+3]>250&&b[i+3]<245)holes++;
 }
 byId('metrics').textContent=
  '已登记部件：'+state.parts.length+
  '\n可见部件：'+state.shown.size+
  '\n原画 SHA-256：'+state.sourceSHA+
  '\n通道 MAE：'+(sum/a.length).toFixed(5)+
  '\n差异像素（容差1）：'+different+
  '\n源画面不透明区域缺口：'+holes+
  '\n工程状态：'+(state.qa?.status||'待核实')+
  '\n动作视觉：独立验收';
}
function updateSlider(id,v){
 state.values[id]=Number(v);
 byId(id+'Val').textContent=String(v);
 paint();
}
function choose(ids){
 state.shown=new Set(ids);
 for(const box of document.querySelectorAll('input[data-semantic]')){
  box.checked=state.shown.has(box.dataset.semantic);
 }
 paint();
}
async function initialize(){
 try{
  state.manifest=await getJSON(psdSource?'integrated-parts.json':'parts.json');
  state.qa=await getJSON(psdSource?'integration-qa.json':'engineering-qa.json');
  if(state.manifest.schema!=='KOMA-P0-ARTMESH-MANIFEST-V1'||
     state.manifest.characterId!=='p0_character_001'||state.manifest.yaw!==0)
    throw Error('P0 identity/manifests mismatch');
  const referenceMeta=state.manifest.referenceImage;
  if(!referenceMeta)throw Error('reference metadata required');
  const ref=await loadPNG(referenceMeta.path,referenceMeta.sha256);
  state.reference=ref.bitmap;state.sourceSHA=ref.actual;
  const parts=state.manifest.parts;
  if(parts.length!==13)throw Error('expected 13 semantic slots');
  await Promise.all(parts.map(async p=>{
   const rel=psdSource?p.path:p.path.replace(/^p1-front\//,'');
   const {bitmap}=await loadPNG(rel,p.frameSha256);
   p.image=bitmap;
  }));
  state.parts=parts.sort((a,b)=>a.depthOrder-b.depthOrder);
  state.shown=new Set(parts.map(p=>p.semanticId));
  const root=byId('parts');
  for(const p of parts){
   const lab=document.createElement('label');
   const check=document.createElement('input');
   check.type='checkbox';check.checked=true;check.dataset.semantic=p.semanticId;
   check.addEventListener('change',()=>{if(check.checked)state.shown.add(p.semanticId);
     else state.shown.delete(p.semanticId);paint();});
   const txt=document.createElement('span');txt.textContent=p.semanticId;
   lab.append(check,txt);root.append(lab);
  }
  clear('reference').drawImage(state.reference,0,0);
  state.loaded=true;
  if(psdSource){
   document.title='P0 · See-through PSD 补绘 ArtMesh 审查';
   document.querySelector('header h1').textContent='p0_character_001 · See-through PSD 13 层动作审查';
  }
  byId('status').textContent=psdSource
   ?'P0 PSD 真实 RGBA 图层 SHA-256 已核对 · 补绘视觉复核'
   :'独立 RGBA 图层 SHA-256 已核对 · P1 动作画质检查';
  paint();
 }catch(e){
  state.error=String(e.message||e);
  byId('status').textContent='源文件或校验信息不完整';
  byId('metrics').textContent=state.error;
 }
}
for(const id of ['eyeNear','eyeFar','fringeX']){
 byId(id).addEventListener('input',e=>updateSlider(id,e.target.value));
}
byId('reset').addEventListener('click',()=>{
 for(const id of ['eyeNear','eyeFar','fringeX']){
  byId(id).value=0;state.values[id]=0;byId(id+'Val').textContent='0';
 }
 choose(state.parts.map(p=>p.semanticId));
});
byId('eyes').addEventListener('click',()=>choose(['face.skin','eye.near','eye.far','nose','mouth']));
byId('hair').addEventListener('click',()=>choose(state.parts.filter(p=>p.semanticId.startsWith('hair.')).map(p=>p.semanticId)));
byId('all').addEventListener('click',()=>choose(state.parts.map(p=>p.semanticId)));
window.__P1_VIEWER={inspect:()=>({ready:state.loaded,partCount:state.parts.length,
  qaStatus:state.qa?.status,sourceSHA:state.sourceSHA,values:state.values,
  source:psdSource?'seethrough':'original',error:state.error}),
  setEyeNear:v=>{byId('eyeNear').value=v;updateSlider('eyeNear',v);},
  reset:()=>byId('reset').click()};
initialize();
})();
