(() => {
"use strict";
const root=new URL("../private-assets/",location.href);
const $=id=>document.getElementById(id);
let p8=null,p13=null,contract=null,ready=false,errors=[],paintToken=0,last=null;
const cache=new Map();
const assert=(condition,message)=>{if(!condition)throw Error(message)};
const safe=p=>typeof p==="string"&&!p.startsWith("/")&&!p.includes("..");
const hex=h=>typeof h==="string"&&/^[a-f0-9]{64}$/.test(h);
async function fetchPath(p){
 assert(safe(p),"Invalid source path");
 const result=await fetch(new URL(p,root),{cache:"no-store"});
 assert(result.ok,"P0 original source unavailable "+p+" HTTP "+result.status);
 return result;
}
async function hash(bytes){
 const dig=await crypto.subtle.digest("SHA-256",bytes);
 return [...new Uint8Array(dig)].map(n=>n.toString(16).padStart(2,"0")).join("");
}
async function originalImage(path,signature){
 assert(hex(signature),"P0 original SHA-256 required");
 if(cache.has(signature))return cache.get(signature);
 const promise=(async()=>{
  const response=await fetchPath(path),data=await response.arrayBuffer();
  assert(await hash(data)===signature,"Original P0 image hash differs "+path);
  const png=await createImageBitmap(new Blob([data],{type:"image/png"}));
  assert(png.width===1024&&png.height===1024,"P0 original global canvas differs");
  return png;
 })();
 cache.set(signature,promise);
 promise.catch(()=>cache.delete(signature));
 return promise;
}
function checker(ctx,x,y,width,height){
 ctx.save();
 for(let row=0;row<Math.ceil(height/22);row++)for(let col=0;col<Math.ceil(width/22);col++){
  ctx.fillStyle=(row+col)%2?"#36475a":"#4d5e72";
  ctx.fillRect(x+col*22,y+row*22,22,22);
 }
 ctx.restore();
}
function renderedKey(angle){
 const key=p8.frames.find(x=>x.angle===angle);
 const trial=p13.frames.find(x=>x.angle===angle);
 assert(key&&trial,"37-frame source P0 motion incomplete");
 return {key,trial};
}
function paintComparison(left,right,angle){
 const ctx=$("motion").getContext("2d");
 ctx.fillStyle="#31445a";ctx.fillRect(0,0,1024,550);
 const W=502;
 for(const [ix,pic] of [left,right].entries()){
  const x=ix*512+5;
  checker(ctx,x,0,W,W);
  ctx.drawImage(pic,x,0,W,W);
  ctx.font="15px system-ui";ctx.fillStyle="#f0f6fd";
  ctx.fillText((ix?"P13 · 分层形变候选":"P8 · 原画动画基线")+" · "+angle+"°",x+8,526);
 }
}
function paintingData(angle,role){
 const view=contract.intermediateViews.find(x=>x.viewAngle===angle);
 assert(view,"P13 intermediate component slot missing");
 const entry=view.parts.find(x=>x.semanticId===role);
 assert(entry,"P13 semantic component missing "+role);
 return {view,entry};
}
function paintPartImages(one,two,three,role,angle){
 const ctx=$("parts").getContext("2d"),W=502;
 ctx.fillStyle="#34455a";ctx.fillRect(0,0,1536,550);
 for(const [ix,pic] of [one,two,three].entries()){
  const x=ix*512+5;
  checker(ctx,x,0,W,W);
  ctx.drawImage(pic,x,0,W,W);
  ctx.font="15px system-ui";ctx.fillStyle="#eef4fb";
  ctx.fillText(role+" · "+(ix===0?"45° 原画":ix===1?"90° 原画":angle+"° 中间层"),x+8,527);
 }
}
async function redraw(){
 const id=++paintToken,angle=Number($("yaw").value);
 const layerAngle=Number($("partYaw").value),role=$("role").value;
 $("yawValue").textContent=angle.toFixed(1)+"°";
 const pair=renderedKey(angle),{view,entry}=paintingData(layerAngle,role);
 const [base,trial,sourceA,sourceB,layer]=await Promise.all([
  originalImage(pair.key.path,pair.key.sha256),
  originalImage(pair.trial.path,pair.trial.sha256),
  originalImage(entry.source45.path,entry.source45.sha256),
  originalImage(entry.source90.path,entry.source90.sha256),
  originalImage(entry.sourceDerivedCandidate.path,entry.sourceDerivedCandidate.sha256)
 ]);
 if(id!==paintToken)return;
 paintComparison(base,trial,angle);
 paintPartImages(sourceA,sourceB,layer,role,layerAngle);
 $("status").textContent="P0 图像 SHA-256 校验 5/5 · 37 帧动画 · "+
  layerAngle+"° / "+role+" · 不透明区域 "+entry.alphaVisibility.opaqueOrTranslucentPixelCount+
  " px · 源原画候选对应已登记";
 $("detail").textContent=JSON.stringify({
  characterId:contract.characterId,
  angle,semanticId:role,layerAngle,
  originalKeyAngles:contract.sourceApprovedCharacterViews,
  P11ProfilePSD_SHA256:contract.sourceP11Editable90PSD_SHA256,
  P8Frame:pair.key,P13SourceDerivedFrame:pair.trial,
  P13IntermediatePart:entry,
  expectedPhysicalAnchors:view.predictedReferenceAnchors,
  P13SourceArtStatus:contract.imageContract.sourcePaintingApproval,
  acceptedMotionStatus:"P8_SEMANTIC_OCCLUSION_ARTMESH"
 },null,2);
 last={angle,layerAngle,role,verifiedImages:5,
       sourceAlphaPixels:entry.alphaVisibility.opaqueOrTranslucentPixelCount,
       state:"P0_REGISTERED_RGBA_COMPARISON"};
}
async function choose(angle,layerAngle,role){
 if(angle!==undefined)$("yaw").value=String(angle);
 if(layerAngle!==undefined)$("partYaw").value=String(layerAngle);
 if(role!==undefined)$("role").value=role;
 await redraw();
}
async function init(){
 try{
  [p8,p13,contract]=await Promise.all([
   fetchPath("p8-semantic-occlusion/selective-sequence/qa.json").then(x=>x.json()),
   fetchPath("p13-source-priority/source-feathered/qa.json").then(x=>x.json()),
   fetchPath("p13-source-priority/p13-paint-contract.json").then(x=>x.json())
  ]);
  assert(contract.schema==="KOMA-P0-P13-INTERMEDIATE-ANGLE-PAINT-CONTRACT-V1","P13 contract changed");
  assert(p8.characterId==="p0_character_001"&&p13.characterId==="p0_character_001"&&contract.characterId==="p0_character_001","P0 character identity changed");
  assert(p8.frameCount===37&&p13.frameCount===37,"37 actual PNG frames required");
  assert(p13.semanticLayerCount===26&&contract.intermediateViews.length===2,"P13 transparency source asset count incomplete");
  const roles=contract.imageContract.componentIDs;
  $("role").replaceChildren(...roles.map(id=>{
   const op=document.createElement("option");op.value=id;op.textContent=id;return op;
  }));
  $("role").value="hair.front";
  await redraw();ready=true;
 }catch(e){errors.push(String(e));$("status").textContent="P0 原画校验失败："+String(e.message||e);}
}
$("yaw").addEventListener("input",()=>redraw().catch(e=>{errors.push(String(e));$("status").textContent=String(e)}));
$("partYaw").addEventListener("change",()=>redraw().catch(e=>{errors.push(String(e));$("status").textContent=String(e)}));
$("role").addEventListener("change",()=>redraw().catch(e=>{errors.push(String(e));$("status").textContent=String(e)}));
window.__KOMA_P13={
 choose,inspect:()=>({ready,characterId:contract?.characterId,
  sourceFrames:p13?.frameCount,sourceSemanticLayers:p13?.semanticLayerCount,
  registeredAngles:contract?.imageContract.viewList,
  current:last,errors:[...errors]})
};
init();
})();
