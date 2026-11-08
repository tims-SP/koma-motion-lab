(() => {
"use strict";
const base=new URL("../private-assets/",location.href);
const $=id=>document.getElementById(id);
let registry=null,data=null,ready=false,token=0,errors=[],last=null;
const cache=new Map();
const signedSHA=s=>typeof s==="string"&&/^[a-f0-9]{64}$/.test(s);
const assert=(truth,message)=>{if(!truth)throw Error(message)};
const safe=s=>typeof s==="string"&&!s.startsWith("/")&&!s.includes("..");
async function get(path){
 assert(safe(path),"invalid original P0 source path");
 const res=await fetch(new URL(path,base),{cache:"no-store"});
 assert(res.ok,"P0 source response "+res.status);
 return res;
}
async function digest(bytes){
 return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)))
 .map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function originalImage(entry){
 const key=entry.frameSha256;
 assert(signedSHA(key),"missing P0 source SHA-256");
 if(cache.has(key))return cache.get(key);
 const task=(async()=>{
  const resp=await get(entry.path);
  const bytes=await resp.arrayBuffer();
  assert(await digest(bytes)===key,"original image SHA-256 failed "+entry.semanticId);
  const image=await createImageBitmap(new Blob([bytes],{type:"image/png"}));
  assert(image.width===1024&&image.height===1024,"P0 RGBA image resolution mismatch");
  return image;
 })();
 cache.set(key,task);
 task.catch(()=>cache.delete(key));
 return task;
}
function selectOptions(){
 const pair=$("pair").value;
 const records=Object.values(data.pairs).filter(x=>x.sourceAngles.join("-")===pair);
 const previous=$("semantic").value;
 $("semantic").innerHTML="";
 records.forEach(record=>{
  const option=document.createElement("option");
  option.value=record.part;option.textContent=record.part;
  $("semantic").appendChild(option);
 });
 $("semantic").value=records.some(x=>x.part===previous)?previous:"hair.front";
 if(!$("semantic").value&&records.length)$("semantic").value=records[0].part;
}
async function draw(){
 const id=++token;
 const pair=$("pair").value,role=$("semantic").value;
 const cost=Number($("cost").value);
 $("costValue").textContent=String(cost);
 const row=data.pairs[pair+"/"+role];
 assert(row,"registered semantic region source missing");
 const sourceParts=[];
 for(const yaw of row.sourceAngles){
  const original=registry.parts.find(r=>r.yawDeg===yaw&&r.semanticId===role);
  assert(original&&original.visibility==="visible","original P0 semantic slot missing");
  sourceParts.push(original);
 }
 const images=await Promise.all(sourceParts.map(originalImage));
 if(id!==token)return false;
 const ctx=$("viewer").getContext("2d");
 ctx.fillStyle="#2e4057";ctx.fillRect(0,0,1280,660);
 const W=620,scale=W/1024;
 for(let n=0;n<2;n++){
  const x=n*640+10;
  ctx.save();
  ctx.drawImage(images[n],x,8,W,W);
  ctx.restore();
  ctx.fillStyle="#f2f7fc";ctx.font="16px system-ui";
  ctx.fillText(role+" · "+row.sourceAngles[n]+"°",x+12,650);
 }
 const accepted=row.pairs.filter(p=>p.cost<=cost);
 ctx.lineWidth=1.25;ctx.strokeStyle="#43e4c7";ctx.fillStyle="#4af1ce";
 for(const m of accepted){
  const ax=10+m.originXY[0]*(W/443),ay=8+m.originXY[1]*(W/443);
  const bx=650+m.destinationXY[0]*(W/443),by=8+m.destinationXY[1]*(W/443);
  ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(bx,by);ctx.stroke();
  ctx.beginPath();ctx.arc(ax,ay,3,0,Math.PI*2);ctx.fill();
  ctx.beginPath();ctx.arc(bx,by,3,0,Math.PI*2);ctx.fill();
 }
 $("status").textContent=
 "来源：p0_character_001 · "+pair+" · "+role+
 " · 已验证 2 张 RGBA 原画 SHA-256 · 匹配区域 "+accepted.length+"/"+row.matchedRegions+
 " · 原始匹配面积覆盖率 "+(100*row.sourceAreaCoverageFraction).toFixed(1)+"%";
 $("detail").textContent=JSON.stringify({
  characterId:data.characterId,
  sourceRegistrySHA256:data.sourceRegistrySHA256,
  part:role,sourceAngles:row.sourceAngles,
  originalSemanticLayers:sourceParts.map(x=>({
   angle:x.yawDeg,source:x.path,sha256:x.frameSha256,visibility:x.visibility
  })),
  sourceRegionCount:row.sourceRegions,
  destinationRegionCount:row.destinationRegions,
  matchedRegions:row.matchedRegions,
  thresholdCost:cost,
  displayedMatches:accepted
 },null,2);
 last={pair,role,cost,visible:accepted.length,originalLayers:sourceParts.map(x=>x.frameSha256)};
 return true;
}
async function choose(pair,role,cost){
 if(pair!==undefined)$("pair").value=String(pair);
 selectOptions();
 if(role!==undefined)$("semantic").value=String(role);
 if(cost!==undefined)$("cost").value=String(cost);
 return await draw();
}
async function init(){
 try{
  [data,registry]=await Promise.all([
   get("p9-region-correspondence/qa.json").then(r=>r.json()),
   get("p5-see-through/mv-candidate/parts.json").then(r=>r.json())
  ]);
  assert(data.schema==="KOMA-P0-P9-REGION_GUIDED-CORRESPONDENCE-V1","source version mismatch");
  assert(data.characterId==="p0_character_001"&&registry.characterId==="p0_character_001","P0 character mismatch");
  assert(Object.keys(data.pairs).length===data.registeredSemanticPairs,"source registration mismatch");
  selectOptions();await draw();ready=true;
 }catch(e){
  errors.push(String(e));$("status").textContent="来源验证失败："+String(e.message||e);
 }
}
$("pair").addEventListener("change",()=>{selectOptions();draw().catch(e=>errors.push(String(e)));});
$("semantic").addEventListener("change",()=>draw().catch(e=>errors.push(String(e))));
$("cost").addEventListener("input",()=>draw().catch(e=>errors.push(String(e))));
window.__KOMA_P9={choose,inspect:()=>({ready,characterId:data?.characterId,
 sourcePairs:data?.registeredSemanticPairs,matchedRegions:data?.matchedColorRegions,
 current:last,errors:[...errors]})};
init();
})();
