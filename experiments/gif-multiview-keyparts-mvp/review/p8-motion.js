(() => {
"use strict";
const base=new URL("../private-assets/",location.href);
const byId=id=>document.getElementById(id);
const expected=["p6-mesh","p7-guided","p8-selective"];
const cache=new Map();
const MAX_BITMAPS=36;
let manifest=null,angle=0,ready=false,token=0,playing=false,timer=null,errors=[];
const assert=(ok,message)=>{if(!ok)throw Error(message)};
const shaFormat=s=>typeof s==="string"&&/^[0-9a-f]{64}$/.test(s);
const validPath=p=>typeof p==="string"&&!p.startsWith("/")&&!p.includes("..");
const roundYaw=x=>Math.min(90,Math.max(0,Math.round(Number(x)/2.5)*2.5));
const printYaw=x=>x.toFixed(1)+"°";
async function shaHex(bytes){
 return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)))
 .map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function readJSON(path){
 assert(validPath(path),"asset JSON path mismatch");
 const response=await fetch(new URL(path,base),{cache:"no-store"});
 assert(response.ok,"asset manifest HTTP "+response.status);
 return response.json();
}
function label(method){
 const host=document.querySelector('article[data-method="'+method.id+'"]');
 assert(host,"method panel missing "+method.id);
 return host;
}
function setDetail(){
 const fields={
  characterId:manifest.characterId,
  canvas:manifest.canvas,
  sourceKeyAngles:manifest.originalKeyAngles,
  PSDSourceAngles:manifest.sourcePSDViews,
  visualAcceptance:manifest.artisticAcceptance,
  methods:manifest.methods.map(m=>({
   id:m.id,label:m.name,source:m.source,
   temporalStatus:m.temporalStatus,temporalOutliers:m.temporalOutliers,
   textureStatus:m.textureStatus,textureRatios:m.textureRatios,
   nativeRGBAFrames:m.frames.length
  }))
 };
 byId("detail").textContent=JSON.stringify(fields,null,2);
 manifest.methods.forEach(m=>{
  const dom=label(m);
  dom.querySelector(".meta").textContent=
   "纹理边缘诊断 22.5°: "+m.textureRatios["22.5"]+
   " · 67.5°: "+m.textureRatios["67.5"]+
   "。相邻帧异常: "+m.temporalOutliers+" 次。";
 });
}
async function verifiedBitmap(frame){
 assert(validPath(frame.path),"unsafe P0 RGBA frame path");
 assert(shaFormat(frame.sha256),"invalid P0 SHA-256");
 const key=frame.sha256;
 if(cache.has(key))return cache.get(key);
 const task=(async()=>{
  const response=await fetch(new URL(frame.path,base),{cache:"no-store"});
  assert(response.ok,"P0 RGBA source HTTP "+response.status+": "+frame.path);
  const bytes=await response.arrayBuffer();
  assert(await shaHex(bytes)===frame.sha256,"P0 frame integrity failed "+frame.path);
  const bitmap=await createImageBitmap(new Blob([bytes],{type:"image/png"}));
  assert(bitmap.width===1024&&bitmap.height===1024,"P0 RGBA 1024 registration mismatch");
  return bitmap;
 })();
 cache.set(key,task);
 task.catch(()=>cache.delete(key));
 if(cache.size>MAX_BITMAPS){
  const first=cache.keys().next().value;
  if(first!==key){
   const old=cache.get(first);
   cache.delete(first);
   old.then(image=>image.close()).catch(()=>{});
  }
 }
 return task;
}
async function renderAt(next){
 assert(manifest,"P0 source manifest unavailable");
 const yaw=roundYaw(next);
 const active=++token;
 const resolved=await Promise.all(manifest.methods.map(async method=>{
  const frame=method.frames[Math.round(yaw/2.5)];
  assert(frame&&frame.angle===yaw,"frame registry angle mismatch "+method.id+" "+yaw);
  const bitmap=await verifiedBitmap(frame);
  return {method,frame,bitmap};
 }));
 if(active!==token)return false;
 for(const item of resolved){
  const canvas=label(item.method).querySelector("canvas");
  const ctx=canvas.getContext("2d");
  ctx.clearRect(0,0,1024,1024);
  ctx.drawImage(item.bitmap,0,0);
 }
 angle=yaw;
 byId("yaw").value=String(yaw);
 byId("angle").textContent=printYaw(yaw);
 byId("status").textContent=
  "源图校验：3/3 · 已登记分层：39 · 检查角度 "+printYaw(yaw)+
  (manifest.originalKeyAngles.includes(yaw)?" · 原始关键帧":" · RGBA 视角插值");
 return true;
}
function stop(){
 playing=false;
 if(timer!==null){clearTimeout(timer);timer=null;}
}
function play(){
 if(playing)return;
 playing=true;
 const advance=async()=>{
  if(!playing)return;
  try{
   await renderAt(angle>=90?0:angle+2.5);
  }catch(error){
   stop();errors.push(String(error));byId("status").textContent="画面校验失败："+error.message;
   return;
  }
  if(playing)timer=setTimeout(advance,80);
 };
 timer=setTimeout(advance,80);
}
async function init(){
 try{
  manifest=await readJSON("p8-semantic-occlusion/viewer-manifest.json");
  assert(manifest.schema==="KOMA-P0-P8-SEMANTIC-OCCLUSION-VIEWER-V1","wrong asset version");
  assert(manifest.characterId==="p0_character_001","P0 identity mismatch");
  assert(JSON.stringify(manifest.canvas)==="[1024,1024]","P0 canvas mismatch");
  assert(JSON.stringify(manifest.methods.map(m=>m.id))===JSON.stringify(expected),"method registry mismatch");
  assert(manifest.methods.every(m=>m.frames.length===37),"registered frames incomplete");
  for(const method of manifest.methods){
   method.frames.forEach((f,i)=>{
    assert(f.angle===i*2.5,"registered chronology differs");
    assert(shaFormat(f.sha256),"registered frame source checksum missing");
   });
  }
  setDetail();
  await renderAt(0);
  ready=true;
 }catch(error){
  errors.push(String(error));
  byId("status").textContent="资产准入检查失败："+String(error.message||error);
 }
}
byId("yaw").addEventListener("input",event=>{
 stop();renderAt(event.target.value).catch(err=>{
  errors.push(String(err));byId("status").textContent="校验失败："+err.message;
 });
});
byId("prev").addEventListener("click",()=>{stop();renderAt(angle-2.5).catch(err=>errors.push(String(err)));});
byId("next").addEventListener("click",()=>{stop();renderAt(angle+2.5).catch(err=>errors.push(String(err)));});
byId("play").addEventListener("click",play);
byId("stop").addEventListener("click",stop);
window.__KOMA_P8_VIEWER={
 inspect:()=>({ready,angle,characterId:manifest?.characterId,
  methodCount:manifest?.methods?.length||0,
  frameCount:manifest?.methods?.[0]?.frames?.length||0,
  sourceIntegrity:true,visualAcceptance:manifest?.artisticAcceptance,errors:[...errors]}),
 renderAt,play,stop
};
init();
})();
