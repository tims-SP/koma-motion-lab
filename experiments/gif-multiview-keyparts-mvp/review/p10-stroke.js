(() => {
"use strict";
const base=new URL("../private-assets/",location.href);
const $=id=>document.getElementById(id);
let stroke=null, baseline=null, ready=false,errors=[],last=null,turn=0;
const bitmaps=new Map();
const assert=(ok,msg)=>{if(!ok)throw Error(msg)};
const safe=s=>typeof s==="string"&&!s.startsWith("/")&&!s.includes("..");
const hex=s=>typeof s==="string"&&/^[a-f0-9]{64}$/.test(s);
async function retrieve(p){
 assert(safe(p),"Invalid P0 artwork filename");
 const r=await fetch(new URL(p,base),{cache:"no-store"});
 assert(r.ok,"P0 asset HTTP "+r.status+": "+p);
 return r;
}
async function checkSha(bytes){
 const d=await crypto.subtle.digest("SHA-256",bytes);
 return [...new Uint8Array(d)].map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function image(entry){
 assert(safe(entry.path)&&hex(entry.sha256),"Missing original P0 image provenance");
 if(bitmaps.has(entry.sha256))return bitmaps.get(entry.sha256);
 const job=(async()=>{
  const r=await retrieve(entry.path);
  const bytes=await r.arrayBuffer();
  assert(await checkSha(bytes)===entry.sha256,"Original P0 image SHA-256 differs");
  const bmp=await createImageBitmap(new Blob([bytes],{type:"image/png"}));
  assert(bmp.width===1024&&bmp.height===1024,"Original P0 canvas differs");
  return bmp;
 })();
 bitmaps.set(entry.sha256,job);
 job.catch(()=>bitmaps.delete(entry.sha256));
 return job;
}
function parts(){
 const pair=$("pair").value;
 const arr=Object.keys(stroke.pairs).filter(x=>x.startsWith(pair+"/")).map(x=>x.split("/")[1]);
 const previous=$("part").value;
 $("part").replaceChildren(...arr.map(p=>{
  const el=document.createElement("option");
  el.value=p;el.textContent=p;return el;
 }));
 $("part").value=arr.includes(previous)?previous:"hair.front";
 if(!$("part").value)$("part").value=arr[0];
 const ys=pair==="0-45"?[0,22.5,45]:[45,67.5,72.5,90];
 $("yaw").replaceChildren(...ys.map(y=>{
  const o=document.createElement("option");
  o.value=String(y);o.textContent=y.toFixed(1)+"°";return o;
 }));
 $("yaw").value=pair==="0-45"?"22.5":"67.5";
}
async function paint(){
 const seq=++turn;
 const pair=$("pair").value;
 const role=$("part").value;
 const threshold=Number($("confidence").value);
 const angle=Number($("yaw").value);
 $("score").textContent=threshold.toFixed(2);
 const record=stroke.pairs[pair+"/"+role];
 assert(record,"P0 stroke pair unavailable "+pair+"/"+role);
 const [a,b]=record.angles;
 const left=stroke.sources[a+"/"+role],right=stroke.sources[b+"/"+role];
 const frame=baseline.frames.find(x=>x.angle===angle);
 assert(frame,"Original P0 intermediate frame not registered "+angle);
 const [srcA,srcB,intermediate]=await Promise.all([
  image(left),image(right),image({path:frame.path,sha256:frame.sha256})
 ]);
 if(seq!==turn)return;
 const W=512,ctx=$("panel").getContext("2d");
 ctx.fillStyle="#34475e";ctx.fillRect(0,0,1536,575);
 for(const [i,bmp] of [srcA,srcB,intermediate].entries()){
  const x=i*W;
  ctx.drawImage(bmp,x,0,W,W);
  ctx.fillStyle="#f0f5fa";
  ctx.font="16px system-ui";
  const t=i===0?role+" "+a+"°":i===1?role+" "+b+"°":"P8 原画 ArtMesh 转头 "+angle+"°";
  ctx.fillText(t,x+11,535);
 }
 const accepted=record.accepted.filter(x=>x.confidence>=threshold);
 const scale=W/443;
 for(const link of accepted){
  const sx=link.sourceXY[0]*scale,sy=link.sourceXY[1]*scale;
  const tx=W+link.targetXY[0]*scale,ty=link.targetXY[1]*scale;
  ctx.strokeStyle="#5ee7ce";ctx.lineWidth=1.5;
  ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(tx,ty);ctx.stroke();
  ctx.fillStyle="#ffdab2";
  for(const [x,y] of [[sx,sy],[tx,ty]]){ctx.beginPath();ctx.arc(x,y,3.4,0,Math.PI*2);ctx.fill();}
 }
 $("status").textContent=
  "P0 原图 SHA-256 已验证 3/3 · "+pair+" · "+role+
  " · 当前可见对应 "+accepted.length+"/"+record.accepted.length+
  " · 视角 "+angle+"° · 未匹配源线条 "+record.occludedCandidates.length;
 $("details").textContent=JSON.stringify({
  characterId:stroke.characterId,
  sourceNativeCanvas:stroke.nativeCanvas,
  originalParts:[{yaw:a,path:left.path,sha256:left.sha256},
                 {yaw:b,path:right.path,sha256:right.sha256}],
  motionFrame:{yaw:frame.angle,path:frame.path,sha256:frame.sha256},
  physicalShift:record.physicalShift,
  totalSourceStrokes:record.sourceStrokeCount,
  totalTargetStrokes:record.targetStrokeCount,
  matches:accepted,
  uncertainOccludedCandidates:record.occludedCandidates,
  uncertainAppearingCandidates:record.appearingCandidates,
  artisticApproval:stroke.visualApproval
 },null,2);
 last={pair,role,angle,visible:accepted.length,sourceStrokes:record.sourceStrokeCount,
       targetStrokes:record.targetStrokeCount,verifiedSources:3,
       status:"P0_REAL_ARTWORK_RENDERED"};
}
async function choose(pair,role,threshold,angle){
 if(pair!==undefined){$("pair").value=pair;parts();}
 if(role!==undefined)$("part").value=role;
 if(threshold!==undefined)$("confidence").value=String(threshold);
 if(angle!==undefined)$("yaw").value=String(angle);
 await paint();
}
async function init(){
 try{
  [stroke,baseline]=await Promise.all([
   retrieve("p10-stroke-identity/qa.json").then(x=>x.json()),
   retrieve("p8-semantic-occlusion/selective-sequence/qa.json").then(x=>x.json())
  ]);
  assert(stroke.schema==="KOMA-P0-P10-INK_STROKE-IDENTITY-CANDIDATES-V1","Wrong source schema");
  assert(stroke.characterId==="p0_character_001"&&baseline.characterId==="p0_character_001","P0 identity mismatch");
  assert(baseline.frameCount===37&&stroke.sourceArtMeshViewSlots===39,"P0 asset coverage incomplete");
  assert(stroke.registeredSemanticPairs===22,"P0 stroke source pairing mismatch");
  assert(stroke.candidateIdentities>0,"P0 stroke candidates missing");
  parts();await paint();ready=true;
 }catch(e){errors.push(String(e));$("status").textContent="验收失败："+String(e.message||e);}
}
$("pair").addEventListener("change",()=>{parts();paint().catch(e=>errors.push(String(e)));});
$("part").addEventListener("change",()=>paint().catch(e=>errors.push(String(e))));
$("confidence").addEventListener("input",()=>paint().catch(e=>errors.push(String(e))));
$("yaw").addEventListener("change",()=>paint().catch(e=>errors.push(String(e))));
window.__KOMA_P10={
 choose,
 inspect:()=>({ready,characterId:stroke?.characterId,
  semanticPairs:stroke?.registeredSemanticPairs,
  strokeCandidates:stroke?.candidateIdentities,
  originalRGBAFrames:baseline?.frameCount,
  last,errors:[...errors]})
};
init();
})();
