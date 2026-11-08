(() => {
"use strict";
const root=new URL("../private-assets/",location.href),el=id=>document.getElementById(id);
let qa=null,gap=null,ready=false,errors=[],current=null,generation=0;
const cached=new Map();
const assert=(ok,message)=>{if(!ok)throw Error(message)};
const uriValid=p=>typeof p==="string"&&!p.startsWith("/")&&!p.includes("..");
const shaValid=s=>typeof s==="string"&&/^[a-f0-9]{64}$/.test(s);
async function fetchFile(p){
 assert(uriValid(p),"Invalid source path");
 const response=await fetch(new URL(p,root),{cache:"no-store"});
 assert(response.ok,"Source unavailable "+p+" HTTP "+response.status);
 return response;
}
async function digest(bytes){
 const data=await crypto.subtle.digest("SHA-256",bytes);
 return [...new Uint8Array(data)].map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function artwork(p,expected){
 assert(shaValid(expected),"Required source SHA-256 is missing");
 if(cached.has(expected))return cached.get(expected);
 const promise=(async()=>{
  const r=await fetchFile(p),raw=await r.arrayBuffer();
  assert(await digest(raw)===expected,"Original artwork SHA-256 differs: "+p);
  const type=p.endsWith(".jpg")?"image/jpeg":"image/png";
  const bitmap=await createImageBitmap(new Blob([raw],{type}));
  return bitmap;
 })();
 cached.set(expected,promise);
 promise.catch(()=>cached.delete(expected));
 return promise;
}
function renderMotion(ctx,src1,src2,labels){
 ctx.fillStyle="#35495f";ctx.fillRect(0,0,1024,545);
 const W=500;
 for(const [i,image] of [src1,src2].entries()){
  const x=i*512+6;
  ctx.drawImage(image,x,0,W,W);
  ctx.fillStyle="#f3f7fc";ctx.font="15px system-ui";
  ctx.fillText(labels[i],x+6,530);
 }
}
async function paint(){
 const n=++generation;
 const angle=Number(el("angle").value),mode=el("variant").value,role=el("part").value;
 const reference=qa.methods.find(x=>x.id==="p8-selective");
 const candidate=qa.methods.find(x=>x.id===mode);
 const base=reference.frames.find(x=>x.angle===angle);
 const altered=candidate.frames.find(x=>x.angle===angle);
 const item=gap.parts.find(x=>x.role===role);
 assert(base&&altered&&item,"Original P0 source comparison unavailable");
 assert(item.sourceComparisonPath && item.sourceComparisonSHA256,"Requested source gap imagery missing");
 const [a,b,c]=await Promise.all([
  artwork(base.path,base.sha256),
  artwork(altered.path,altered.sha256),
  artwork(item.sourceComparisonPath,item.sourceComparisonSHA256)
 ]);
 if(n!==generation)return;
 assert(a.width===1024&&a.height===1024&&b.width===1024&&b.height===1024,"Original P0 RGBA canvas mismatch");
 renderMotion(el("motion").getContext("2d"),a,b,
  ["P8 · source-registered ArtMesh · "+angle+"°",
   mode+" · source-registered VDD candidate · "+angle+"°"]);
 const canvas=el("occlusion"),ctx=canvas.getContext("2d");
 ctx.clearRect(0,0,canvas.width,canvas.height);
 ctx.drawImage(c,0,0,canvas.width,canvas.height);
 const ratio=(item.targetOnlyFraction*100).toFixed(1);
 el("status").textContent="P0 来源 SHA-256 验证 3/3 · "+angle+"° · "+mode+
  " · "+role+" 目标角度新增可见区域 "+ratio+"%（可能含配准误差）";
 el("detail").textContent=JSON.stringify({
  characterId:qa.characterId,angle,mode,
  originalP0KeyViews:qa.P0OriginalViews,
  P11ProfilePSDsourceSHA256:qa.P11RealProfilePSD_SHA256,
  P8Motion:base,
  P12Motion:altered,
  P8EdgeRatio:reference.textureRatios[String(angle)]??null,
  P12EdgeRatio:candidate.textureRatios[String(angle)]??null,
  gap:item,
  adoptedMotionRenderer:qa.P12FullMotionAdoption,
  currentQualityGate:qa.P12TextureAdoption,
  artisticAcceptance:qa.status
 },null,2);
 current={angle,mode,part:role,gapRatio:item.targetOnlyFraction,
          verifiedImages:3,status:"P0_ORIGINAL_RENDERED"};
}
async function choose(angle,mode,part){
 if(angle!==undefined)el("angle").value=String(angle);
 if(mode!==undefined)el("variant").value=mode;
 if(part!==undefined)el("part").value=part;
 await paint();
}
async function start(){
 try{
  [qa,gap]=await Promise.all([
   fetchFile("p12-comparison/comparison-qa.json").then(x=>x.json()),
   fetchFile("p12-occlusion-gap/qa.json").then(x=>x.json())
  ]);
  assert(qa.schema==="KOMA-P0-P12-ANATOMY-STROKE-SEMANTIC-GAP-COMPARISON-V1","Source QA schema mismatch");
  assert(qa.characterId==="p0_character_001"&&gap.characterId==="p0_character_001","P0 identity mismatch");
  assert(qa.methods.length===5&&gap.registeredPairCount===13,"P12 source scope mismatch");
  await paint();ready=true;
 }catch(e){errors.push(String(e));el("status").textContent="P12 原画验收失败："+String(e.message||e);}
}
for(const id of ["angle","variant","part"])el(id).addEventListener("change",()=>paint().catch(e=>{errors.push(String(e));el("status").textContent=String(e)}));
window.__KOMA_P12={choose,inspect:()=>({
 ready,characterId:qa?.characterId,methodCount:qa?.methods.length,
 originalSourceViews:qa?.P0OriginalViews,
 regionCount:gap?.registeredPairCount,current,errors:[...errors]
})};
start();
})();
