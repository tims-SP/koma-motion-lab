"use strict";
(()=>{
const prefix="/experiments/gif-multiview-keyparts-mvp/";
const state={ready:false,yaw:65,role:"hair.back",verifiedImages:0,sourceMatch:false,errors:[],underpaint:false};
const yaw=document.querySelector("#yaw"),role=document.querySelector("#role"),under=document.querySelector("#underpaint");
const status=document.querySelector("#status"),detail=document.querySelector("#detail");
const canvas=document.querySelector("#review"),ctx=canvas.getContext("2d");
let qa=null,serial=0;
const hex=b=>Array.from(new Uint8Array(b)).map(x=>x.toString(16).padStart(2,"0")).join("");
async function json(path){const r=await fetch(path,{cache:"no-store"});if(!r.ok)throw Error("QA HTTP "+r.status+" "+path);return r.json()}
async function checkedImage(entry){
 const r=await fetch(prefix+"private-assets/"+entry.path,{cache:"no-store"});
 if(!r.ok)throw Error("PNG HTTP "+r.status+": "+entry.path);
 const b=await r.arrayBuffer();
 const got=hex(await crypto.subtle.digest("SHA-256",b));
 if(got!==entry.sha256)throw Error("source PNG SHA mismatch: "+entry.path);
 return createImageBitmap(new Blob([b],{type:"image/png"}));
}
const key=y=>y===65?"yaw065":"yaw077p5";
function drawFrame(pic,index,title){
 const x=index*400;
 ctx.fillStyle="#304257";ctx.fillRect(x,0,400,400);
 ctx.drawImage(pic,0,0,1024,1024,x,0,400,400);
 ctx.fillStyle="#fff";ctx.font="15px system-ui";ctx.fillText(title,x+9,424);
}
async function render(){
 if(!qa)return;
 const id=++serial;const angle=Number(yaw.value),part=role.value,enhanced=Boolean(under.checked);
 state.ready=false;state.yaw=angle;state.role=part;state.underpaint=enhanced;state.verifiedImages=0;
 status.textContent="正在核验原画与分层 PNG 来源…";
 const found=qa.generatedIndependentCandidateViews.find(x=>x.angle===angle);
 if(!found)throw Error("unknown independent angle");
 const source=found.sourceView===45?
  {path:"p2-views/whole/yaw045.png",sha256:found.sourceViewSHA256}:
  {path:"p2-views/whole/yaw090.png",sha256:found.sourceViewSHA256};
 const base=prefix+"private-assets/p15-independent-candidates/"+key(angle);
 const layerQA=await json(base+"-artmesh/qa.json");
 const enhancedQA=enhanced&&angle===77.5?await json(base+"-inpainted/qa.json"):null;
 const layer=(enhancedQA?enhancedQA.nativeLayers:layerQA.semanticLayerRecords).find(x=>x.semanticId===part);
 if(!layer)throw Error("unknown P0 semantic role");
 const composite=enhancedQA?enhancedQA.composite:layerQA.composite;
 const entries=[source,found.transparentPainting,composite,layer];
 const pictures=await Promise.all(entries.map(x=>checkedImage(x)));
 if(id!==serial)return;
 state.verifiedImages=pictures.length;state.sourceMatch=true;
 ctx.clearRect(0,0,1600,440);
 const bg=["#304257","#304257","#304257","#304257"];
 for(let i=0;i<4;i++){
  const sub=document.createElement("canvas");sub.width=1024;sub.height=1024;
  const s=sub.getContext("2d");s.fillStyle=bg[i];s.fillRect(0,0,1024,1024);
  s.drawImage(pictures[i],0,0);
  drawFrame(sub,i,["P0 original "+found.sourceView+"°","Generated "+angle+"° RGBA","13 ArtMesh exact composite",part+(enhancedQA?" + underpaint":"")][i]);
 }
 detail.textContent=JSON.stringify({
   characterId:qa.characterId,
   yaw:angle,part,
   inputMode:layerQA.paintAdapter,seed:layerQA.paintSeed,
   sourceSHA256:entries.map(x=>({path:x.path,sha256:x.sha256})),
   selectedAlphaPixels:layer.visiblePixels??layer.alphaPixels,
   candidateQuality:qa.artisticQualityStatus,
   originalHeroVerified:qa.referenceHeroSHA256Verified
 },null,2);
 state.ready=true;
 status.textContent="P0 来源验证 "+state.verifiedImages+"/4；当前部件 "+part+"；"+(enhancedQA?"查看隐藏区域补绘":"源原画像素精确重建");
}
function safe(){return render().catch(e=>{state.errors.push(String(e));status.textContent=String(e)})}
yaw.addEventListener("change",safe);role.addEventListener("change",safe);under.addEventListener("change",safe);
window.__KOMA_P15_06={inspect:()=>({...state}),choose:async (y,r,useUnder)=>{
  if(![65,77.5].includes(y))throw Error("invalid yaw");
  yaw.value=String(y);role.value=r;under.checked=Boolean(useUnder);await render();
}};
(async()=>{try{
 qa=await json(prefix+"evidence/p15-06-generated-keyviews-qa.json");
 if(qa.characterId!=="p0_character_001"||qa.candidateViewCount!==2||qa.registeredSemanticRGBA!==26)
  throw Error("P0 candidate QA registry mismatch");
 await render();
}catch(e){state.errors.push(String(e));status.textContent=String(e)}})();
})();