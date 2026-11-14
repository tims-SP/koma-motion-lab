"use strict";
(()=>{
const base="/experiments/gif-multiview-keyparts-mvp/";
const angles=[45,67.5,72.5,90],roles=["face.skin","eye.near","nose","mouth"];
const canvas=document.querySelector("#overview"),ctx=canvas.getContext("2d");
const status=document.querySelector("#status"),detail=document.querySelector("#detail"),pick=document.querySelector("#role");
const state={ready:false,role:"face.skin",verified:0,matches:0,anchors:0,errors:[]};
const hex=arr=>Array.from(new Uint8Array(arr)).map(v=>v.toString(16).padStart(2,"0")).join("");
const key=(a,b,r)=>String(a)+"-"+String(b)+"/"+r;
let qa=null,version=0;
async function openPng(entry){
 const res=await fetch(base+"private-assets/"+entry.path,{cache:"no-store"});
 if(!res.ok)throw Error("PNG HTTP "+res.status);
 const bytes=await res.arrayBuffer();
 if(hex(await crypto.subtle.digest("SHA-256",bytes))!==entry.sha256)throw Error("PNG SHA mismatch: "+entry.path);
 return createImageBitmap(new Blob([bytes],{type:"image/png"}));
}
function sources(role){
 const slots=new Map();
 for(const [a,b] of [[45,67.5],[67.5,72.5],[72.5,90]]){
  const pair=qa.pairs[key(a,b,role)];if(!pair)throw Error("missing semantic pair");
  for(const [v,item] of [[a,pair.source.a],[b,pair.source.b]]){
   if(slots.has(v)&&slots.get(v).sha256!==item.sha256)throw Error("inconsistent view source");
   slots.set(v,item);
  }
 }
 return slots;
}
function bbox(image){
 const temp=document.createElement("canvas");temp.width=1024;temp.height=1024;
 const work=temp.getContext("2d",{willReadFrequently:true});work.drawImage(image,0,0);
 const rgba=work.getImageData(0,0,1024,1024).data;
 let x0=1023,y0=1023,x1=0,y1=0;
 for(let y=0;y<1024;y+=3)for(let x=0;x<1024;x+=3){
  if(rgba[(y*1024+x)*4+3]<40)continue;
  x0=Math.min(x,x0);y0=Math.min(y,y0);x1=Math.max(x,x1);y1=Math.max(y,y1);
 }
 if(x1<=x0||y1<=y0)throw Error("empty semantic layer");
 return [x0,y0,x1,y1];
}
function at(xy,col,frame,scale=1){
 return [col*350+(xy[0]*scale-frame.x)*350/frame.size,
         6+(xy[1]*scale-frame.y)*350/frame.size];
}
async function render(role){
 const stamp=++version;state.ready=false;state.role=role;state.matches=0;state.verified=0;state.anchors=0;
 const slots=sources(role),imgs=await Promise.all(angles.map(a=>openPng(slots.get(a))));
 if(stamp!==version)return;
 state.verified=imgs.length;
 const boxes=imgs.map(bbox);
 const x0=Math.min(...boxes.map(x=>x[0])),y0=Math.min(...boxes.map(x=>x[1]));
 const x1=Math.max(...boxes.map(x=>x[2])),y1=Math.max(...boxes.map(x=>x[3]));
 const size=Math.min(1024,Math.max(x1-x0,y1-y0)+70);
 const frame={x:Math.max(0,Math.min(1024-size,(x0+x1-size)/2)),
              y:Math.max(0,Math.min(1024-size,(y0+y1-size)/2)),size};
 ctx.clearRect(0,0,1400,410);
 for(let col=0;col<4;col++){
  ctx.fillStyle="#293951";ctx.fillRect(col*350,0,350,356);
  ctx.drawImage(imgs[col],frame.x,frame.y,frame.size,frame.size,col*350,6,350,350);
  ctx.fillStyle=col===0||col===3?"#d2dcf4":"#6ce7be";
  ctx.font="15px system-ui";ctx.fillText(String(angles[col])+"° source SHA OK",col*350+12,390);
 }
 for(let col=0;col<3;col++){
  const pair=qa.pairs[key(angles[col],angles[col+1],role)];
  for(const stroke of pair.accepted){
   const p1=at(stroke.sourceXY,col,frame,1024/443),p2=at(stroke.targetXY,col+1,frame,1024/443);
   ctx.strokeStyle="#5cf6ba";ctx.lineWidth=2;ctx.beginPath();
   ctx.moveTo(...p1);ctx.lineTo(...p2);ctx.stroke();
   for(const [x,y] of [p1,p2]){ctx.fillStyle="#ffd993";ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill();}
   state.matches++;
  }
 }
 for(let col=0;col<4;col++){
  const p=col<2?qa.pairs[key(45,67.5,role)]:
         col===2?qa.pairs[key(67.5,72.5,role)]:qa.pairs[key(72.5,90,role)];
  for(const item of Object.values(p.physicalP5Predictions1024)){
   const [x,y]=at(col===0?item.a:item.b,col,frame);
   ctx.strokeStyle="#ffe7a4";ctx.lineWidth=1.5;ctx.beginPath();
   ctx.moveTo(x-5,y);ctx.lineTo(x+5,y);ctx.moveTo(x,y-5);ctx.lineTo(x,y+5);ctx.stroke();
   state.anchors++;
  }
 }
 detail.textContent=JSON.stringify({role,source:[...slots].map(([angle,s])=>({angle,path:s.path,sha256:s.sha256})),
  pairs:angles.slice(0,3).map((a,i)=>{const p=qa.pairs[key(a,angles[i+1],role)];
    return {angles:p.angles,sourceStrokes:p.sourceStrokeCount,targetStrokes:p.targetStrokeCount,accepted:p.accepted.length}})},null,2);
 status.textContent="已验证 "+state.verified+" 张源图；笔触 "+state.matches+" 条；参考锚点 "+state.anchors+" 个";
 state.ready=true;
}
pick.onchange=()=>render(pick.value).catch(e=>{state.errors.push(String(e));status.textContent=String(e)});
window.__KOMA_P15={inspect:()=>({...state,pairs:qa?.pairCount}),
 choose:async role=>{if(!roles.includes(role))throw Error("invalid role");pick.value=role;await render(role)}};
(async()=>{try{
 const res=await fetch(base+"evidence/p15-facial-correspondence-qa.json");
 qa=await res.json();
 if(qa.characterId!=="p0_character_001"||qa.pairCount!==12)throw Error("invalid P0 QA registry");
 await render(pick.value);
}catch(e){state.errors.push(String(e));status.textContent=String(e)}})();
})();