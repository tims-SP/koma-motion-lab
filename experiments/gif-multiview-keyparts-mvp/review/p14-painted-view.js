(() => {
"use strict";
const root=new URL("../private-assets/",location.href);
const $=id=>document.getElementById(id);
const assert=(flag,message)=>{if(!flag)throw Error(message)};
const isSafe=s=>typeof s==="string"&&!s.startsWith("/")&&!s.includes("..");
const isSha=s=>typeof s==="string"&&/^[0-9a-f]{64}$/.test(s);
const imageCache=new Map();
let p8=null,p14=null,p0=null,painting67=null,painting72=null,ready=false,errors=[],active=null,ticket=0;
async function fetchRelative(path){
 assert(isSafe(path),"Invalid P0 source path");
 const response=await fetch(new URL(path,root),{cache:"no-store"});
 assert(response.ok,"P0 original source unavailable "+path+" "+response.status);
 return response;
}
async function digest(bytes){
 const hash=await crypto.subtle.digest("SHA-256",bytes);
 return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function verifiedImage(path,expected){
 assert(isSha(expected),"Source PNG needs SHA-256");
 if(imageCache.has(expected))return imageCache.get(expected);
 const task=(async()=>{
  const request=await fetchRelative(path),bytes=await request.arrayBuffer();
  assert(await digest(bytes)===expected,"P0 authored source hash mismatch: "+path);
  const bmp=await createImageBitmap(new Blob([bytes],{type:"image/png"}));
  assert(bmp.width===1024&&bmp.height===1024,"P0 native 1024 canvas required");
  return bmp;
 })();
 imageCache.set(expected,task);task.catch(()=>imageCache.delete(expected));
 return task;
}
function checker(context,x,y,w,h){
 for(let iy=0;iy<Math.ceil(h/24);iy++){
  for(let ix=0;ix<Math.ceil(w/24);ix++){
   context.fillStyle=(ix+iy)%2?"#374c63":"#4e6179";
   context.fillRect(x+24*ix,y+24*iy,24,24);
  }
 }
}
function drawPanels(id,images,labels){
 const node=$(id),ctx=node.getContext("2d");
 const cells=images.length,width=node.width/cells;
 ctx.clearRect(0,0,node.width,node.height);
 for(let i=0;i<cells;i++){
  checker(ctx,Math.floor(i*width),0,width,width);
  ctx.drawImage(images[i],Math.floor(i*width)+4,0,width-8,width-8);
  ctx.font="15px system-ui";ctx.fillStyle="#f1f7fc";
  ctx.fillText(labels[i],i*width+9,width+25);
 }
}
function sourceRole(yaw,semanticId){
 const row=p0.parts.find(x=>x.yawDeg===yaw&&x.semanticId===semanticId);
 assert(row,"P0 approved semantic part "+yaw+"/"+semanticId+" missing");
 return {path:row.path,sha256:row.frameSha256,visibility:row.visibility};
}
function sourcePainted(yaw,id){
 const qa=yaw===67.5?painting67:painting72;
 const rows=yaw===67.5?qa.parts:qa.semanticLayerRecords;
 const rec=rows.find(x=>x.semanticId===id);
 assert(rec,"Painted P0 semantic "+yaw+"/"+id+" not found");
 return {path:rec.path,sha256:rec.sha256,source:qa};
}
async function paint(){
 const currentTicket=++ticket;
 const angle=Number($("angle").value),anglePart=Number($("artView").value);
 const semanticId=$("part").value;
 $("angleLabel").textContent=angle.toFixed(1)+"°";
 const a=p8.frames.find(x=>x.angle===angle),b=p14.frames.find(x=>x.angle===angle);
 assert(a&&b,"P8/P14 full 37-frame animation source missing at "+angle);
 const p45=sourceRole(45,semanticId),p90=sourceRole(90,semanticId);
 const layer=sourcePainted(anglePart,semanticId);
 const [bmpA,bmpB,bmp45,bmpPart,bmp90]=await Promise.all([
  verifiedImage(a.path,a.sha256),
  verifiedImage(b.path,b.sha256),
  verifiedImage(p45.path,p45.sha256),
  verifiedImage(layer.path,layer.sha256),
  verifiedImage(p90.path,p90.sha256)
 ]);
 if(currentTicket!==ticket)return;
 drawPanels("motion",[bmpA,bmpB],[
  "P8 参考 · "+angle+"°","P14 绘制关键帧 VDD · "+angle+"°"
 ]);
 drawPanels("semantic",[bmp45,bmpPart,bmp90],[
  "P0 原画 45° · "+semanticId,
  "P14 候选 "+anglePart+"° · "+semanticId,
  "P0 原画 90° · "+semanticId
 ]);
 $("status").textContent="P0 SHA-256 校验 5/5 · "+angle+"° · 原画部件 "+semanticId+
  " · 视角 "+anglePart+"° · 状态：已登记绘制候选";
 $("detail").textContent=JSON.stringify({
  characterId:"p0_character_001",
  originalAuthorViews:[0,45,90],
  paintedKeyAngles:[67.5,72.5],
  compareYaw:angle,
  activeSourceMethod:p14.method,
  baselineP8:a,viewDependentP14:b,
  approved45Part:p45,
  paintedView:{angle:anglePart,...layer,source:undefined},
  approved90Part:p90,
  semanticID:semanticId,
  sourceArtApproval:p14.visualAcceptance,
  sourceMotionQA:p14.motionAcceptance
 },null,2);
 active={angle,partYaw:anglePart,semanticId,verifiedImages:5,
         motion:"PAINTED_P0_SEMANTIC_VIEW_RECONSTRUCTED"};
}
async function choose(angle,partYaw,role){
 if(angle!==undefined)$("angle").value=String(angle);
 if(partYaw!==undefined)$("artView").value=String(partYaw);
 if(role!==undefined)$("part").value=role;
 await paint();
}
async function init(){
 try{
  [p8,p14,p0,painting67,painting72]=await Promise.all([
   fetchRelative("p8-semantic-occlusion/selective-sequence/qa.json").then(x=>x.json()),
   fetchRelative("p14-authored-candidates/p14-vdd-smooth/qa.json").then(x=>x.json()),
   fetchRelative("p5-see-through/mv-candidate/parts.json").then(x=>x.json()),
   fetchRelative("p14-authored-candidates/yaw067p5-artmesh/qa.json").then(x=>x.json()),
   fetchRelative("p14-authored-candidates/yaw072p5-artmesh/qa.json").then(x=>x.json())
  ]);
  assert([p8,p14,p0,painting67,painting72].every(x=>x.characterId==="p0_character_001"),"P0 character identity changed");
  assert(p14.schema==="KOMA-P0-P14-PAINTED-KEYVIEW-ARTMESH-VDD-V1","P14 original view review metadata differs");
  assert(p8.frameCount===37&&p14.frameCount===37,"37 registered original RGBA frames required");
  assert(painting67.layerCount===13&&painting72.semanticLayerCount===13,"Two painted original ArtMesh views required");
  $("part").replaceChildren(...p14.semanticIDs.map(s=>{
   const opt=document.createElement("option");opt.value=s;opt.textContent=s;return opt;
  }));
  $("part").value="eye.near";
  await paint();ready=true;
 }catch(e){
  errors.push(String(e));$("status").textContent="原画验收失败："+String(e.message||e);
 }
}
for(const id of ["angle","artView","part"])
 $(id).addEventListener(id==="angle"?"input":"change",()=>
  paint().catch(e=>{errors.push(String(e));$("status").textContent=String(e)}));
window.__KOMA_P14={
 choose,inspect:()=>({
  ready,characterId:p14?.characterId,renderFrames:p14?.frameCount,
  semanticRoles:p14?.semanticIDs?.length,
  sourceKeyViews:p14?.originalKeyAngles,
  paintedKeyViews:p14?.paintedCandidateKeyAngles,
  current:active,errors:[...errors]
 })
};
init();
})();
