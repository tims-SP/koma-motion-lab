(() => {
'use strict';
const SIZE=1024;
const candidateMode=new URLSearchParams(location.search).get('mode')==='candidate';
const seethroughFront=new URLSearchParams(location.search).get('source')==='seethrough-front';
const URL_BASE=new URL('../private-assets/',location.href);
const byId=id=>document.getElementById(id);
const expectedIds=['body.reference','hair.back','face.skin','ear.far','ear.near','eye.far','eye.near',
 'nose','mouth','hair.side','hair.front','hair.ahoge','hair.clip.cross_gold'];
const validSHA=s=>typeof s==='string'&&/^[0-9a-f]{64}$/.test(s);
const endpoints=[0,45,90];
let registry=new Map(),whole=new Map(),report=null,ready=false,problems=[],angle=0;
function assert(condition,message){if(!condition)throw Error(message);}
function slot(a,id){return registry.get(String(a)+'/'+id);}
function blend(a,b,t){return a+(b-a)*t;}
function easing(t){t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);}
function blankCanvas(id){const c=byId(id);c.getContext('2d').clearRect(0,0,SIZE,SIZE);}
async function fetchJSON(path){const r=await fetch(new URL(path,URL_BASE),{cache:'no-cache'});assert(r.ok,'JSON '+path+': '+r.status);return r.json();}
async function loadPNG(path,sha){
 assert(typeof path==='string'&&!path.startsWith('/')&&!path.includes('..'),'unsafe path '+path);
 assert(validSHA(sha),'invalid sha256 '+path);
 const r=await fetch(new URL(path,URL_BASE),{cache:'no-cache'});
 assert(r.ok,'image '+path+': '+r.status);
 const bytes=await r.arrayBuffer();
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)))
  .map(x=>x.toString(16).padStart(2,'0')).join('');
 assert(digest===sha,'pixel source digest mismatch '+path);
 const image=await createImageBitmap(new Blob([bytes],{type:'image/png'}));
 assert(image.width===SIZE&&image.height===SIZE,'global canvas mismatch '+path);
 return image;
}
function sameTopology(a,b){
 const am=a.mesh,bm=b.mesh;
 return am.vertexIds.length===bm.vertexIds.length &&
  JSON.stringify(am.vertexIds)===JSON.stringify(bm.vertexIds) &&
  JSON.stringify(am.triangles)===JSON.stringify(bm.triangles);
}
function validateMesh(m){
 assert(m&&Array.isArray(m.vertexIds)&&m.vertexIds.length>=4,'missing ArtMesh vertexIds');
 assert(Array.isArray(m.vertices)&&m.vertices.length===m.vertexIds.length,'invalid vertices');
 assert(Array.isArray(m.triangles)&&m.triangles.length>=2,'ArtMesh needs triangles');
 for(const p of m.vertices)assert(Array.isArray(p)&&p.length===2&&p.every(v=>Number.isFinite(v)&&v>=0&&v<=SIZE),'bad vertex');
 for(const t of m.triangles)assert(t.length===3&&t.every(i=>Number.isInteger(i)&&i>=0&&i<m.vertices.length),'bad triangle');
}
function triangle(ctx,img,s,d){
 const [s0,s1,s2]=s,[p0,p1,p2]=d;
 const det=(s1[0]-s0[0])*(s2[1]-s0[1])-(s2[0]-s0[0])*(s1[1]-s0[1]);
 if(Math.abs(det)<0.01)return;
 const a=((p1[0]-p0[0])*(s2[1]-s0[1])-(p2[0]-p0[0])*(s1[1]-s0[1]))/det;
 const b=((p1[1]-p0[1])*(s2[1]-s0[1])-(p2[1]-p0[1])*(s1[1]-s0[1]))/det;
 const c=((p2[0]-p0[0])*(s1[0]-s0[0])-(p1[0]-p0[0])*(s2[0]-s0[0]))/det;
 const dd=((p2[1]-p0[1])*(s1[0]-s0[0])-(p1[1]-p0[1])*(s2[0]-s0[0]))/det;
 const e=p0[0]-a*s0[0]-c*s0[1],f=p0[1]-b*s0[0]-dd*s0[1];
 ctx.save();
 // Canvas anti-aliased triangle clips can leave subpixel lines between
 // independently rasterized triangles. Pad only their clip edges, never their
 // destination affine coordinates, to conserve semantic geometry.
 const centroid=[(p0[0]+p1[0]+p2[0])/3,(p0[1]+p1[1]+p2[1])/3];
 const expand=p=>{
  const dx=p[0]-centroid[0],dy=p[1]-centroid[1];
  const length=Math.hypot(dx,dy)||1;
  return [p[0]+dx/length*1.55,p[1]+dy/length*1.55];
 };
 const [q0,q1,q2]=[p0,p1,p2].map(expand);
 ctx.beginPath();ctx.moveTo(...q0);ctx.lineTo(...q1);ctx.lineTo(...q2);ctx.closePath();ctx.clip();
 ctx.setTransform(a,b,c,dd,e,f);ctx.drawImage(img,0,0);ctx.restore();
}
function warped(ctx,source,target,opacity){
 if(!source||!source.image||opacity<=0)return;
 ctx.save();ctx.globalAlpha=opacity;
 for(const tri of source.mesh.triangles)
  triangle(ctx,source.image,tri.map(i=>source.mesh.vertices[i]),tri.map(i=>target[i]));
 ctx.restore();
}
function viewPair(degree){if(degree<=45)return [0,45];return [45,90];}

// P0 original-face contour and color sampled from original source GIF pixels.
// Auxiliary underpaint remains beneath authored hair and facial ArtMeshes.
const P0_SKIN=[250,221,214];
const P0_FACE={
 0:[[189,159],[226,151],[261,159],[284,179],[297,212],[286,254],
    [257,283],[227,294],[195,279],[169,246],[157,215],[161,189]],
 45:[[221,159],[250,158],[281,166],[309,180],[334,224],[325,248],
     [291,283],[253,296],[224,279],[203,253],[193,225],[203,188]],
 90:[[278,160],[308,166],[331,180],[348,202],[364,219],[369,233],[354,247],
     [348,261],[326,283],[298,282],[269,272],[243,248],[241,210],[256,178]]
};
function sampleOutline(poly,count=48){
 const edge=poly.map((p,i)=>Math.hypot(poly[(i+1)%poly.length][0]-p[0],poly[(i+1)%poly.length][1]-p[1]));
 const perimeter=edge.reduce((a,b)=>a+b,0),points=[];
 for(let k=0;k<count;k++){
  let dist=perimeter*k/count,index=0;
  while(index<edge.length-1&&dist>=edge[index])dist-=edge[index++];
  const t=dist/Math.max(1e-6,edge[index]);
  points.push([blend(poly[index][0],poly[(index+1)%poly.length][0],t),
               blend(poly[index][1],poly[(index+1)%poly.length][1],t)]);
 }
 return points;
}
const FACE_OUTLINES=Object.fromEntries(Object.entries(P0_FACE).map(([key,v])=>[key,sampleOutline(v)]));
function renderSourceUnderpaint(ctx,deg){
 if(endpoints.includes(deg))return;
 const [a,b]=viewPair(deg),t=easing((deg-a)/(b-a));
 const A=FACE_OUTLINES[a],B=FACE_OUTLINES[b];
 ctx.save();ctx.beginPath();
 A.forEach((p,i)=>{
  const q=[blend(p[0],B[i][0],t)*SIZE/443,blend(p[1],B[i][1],t)*SIZE/443];
  if(i)ctx.lineTo(...q);else ctx.moveTo(...q);
 });
 ctx.closePath();ctx.fillStyle='rgb('+P0_SKIN.join(',')+')';ctx.fill();ctx.restore();
}
function renderLayer(ctx,id,degree){
 const key=slot(degree,id);
 if(key){if(key.visibility==='visible'&&key.image)ctx.drawImage(key.image,0,0);return;}
 const [a,b]=viewPair(degree),A=slot(a,id),B=slot(b,id);
 if(!A||!B)return;
 const t=easing((degree-a)/(b-a));
 const onA=A.visibility==='visible',onB=B.visibility==='visible';
 if(!onA&&!onB)return;
 if(onA&&onB)assert(sameTopology(A,B),'topology differs: '+id+' '+a+'/'+b);
 const src=t<0.5? (onA?A:B) : (onB?B:A);
 if(!src.image)return;
 const vertices=onA&&onB?
  A.mesh.vertices.map((v,i)=>[blend(v[0],B.mesh.vertices[i][0],t),
                              blend(v[1],B.mesh.vertices[i][1],t)]):
  src.mesh.vertices;
 const opacity=(onA&&onB)?1:(onA?1-t:t);
 warped(ctx,src,vertices,opacity);
}
function render(degree){
 angle=degree;byId('degree').textContent=degree+'°';blankCanvas('result');blankCanvas('source');
 if(!ready){byId('resultLabel').textContent='等待经过校验的 P0 原画';return;}
 const [a,b]=viewPair(degree),exact=endpoints.includes(degree)?degree:null;
 const base=exact!==null?exact:(degree-a<=b-degree?a:b);
 const reference=whole.get(base);
 if(reference)byId('source').getContext('2d').drawImage(reference,0,0);
 byId('sourceLabel').textContent='独立参考视角 '+base+'°';
 const parts=expectedIds.map(id=>{
  const rec=slot(exact===null?(degree-a<=b-degree?a:b):degree,id);
  return {id,depth:rec?.depthOrder??0};
 }).sort((x,y)=>x.depth-y.depth);
 const ctx=byId('result').getContext('2d');
 for(const item of parts){
  if(item.id==='face.skin')renderSourceUnderpaint(ctx,degree);
  renderLayer(ctx,item.id,degree);
 }
 byId('resultLabel').textContent='ArtMesh VDD · '+degree+'°'+(exact!==null?'（原画关键帧）':'（插值检查帧）');
}
async function init(){
 try{
  const registrySource=seethroughFront?'p4-see-through/mv-candidate/':'';
  const manifest=await fetchJSON(registrySource+'parts.json');
  report=await fetchJSON(registrySource+'qa.json');
  assert((report.status==='PASS_ENGINEERING_AND_VISUAL_GATES'&&report.failed===0) || (candidateMode&&report.status==='REVIEW_CANDIDATE'), 'QA admission gate is closed');
  assert(manifest.schema==='KOMA-P0-ARTMESH-MANIFEST-V1','manifest schema mismatch');
  assert(manifest.characterId==='p0_character_001','character identity mismatch');
  assert(JSON.stringify(manifest.canvas)===JSON.stringify([SIZE,SIZE]),'canvas mismatch');
  const parts=manifest.parts;
  assert(Array.isArray(parts),'manifest missing parts');
  for(const rec of parts){
   const key=String(rec.yawDeg)+'/'+rec.semanticId;
   assert(!registry.has(key),'duplicate '+key);
   assert(endpoints.includes(rec.yawDeg),'unexpected yaw');
   assert(expectedIds.includes(rec.semanticId),'unexpected part '+rec.semanticId);
   validateMesh(rec.mesh);
   registry.set(key,rec);
  }
  for(const yaw of endpoints){
   for(const id of expectedIds.filter(x=>x!=='ear.far'&&!(yaw===90&&x==='eye.far'))){
    assert(slot(yaw,id),'required '+yaw+'/'+id);
   }
  }
  for(const id of expectedIds.filter(x=>x!=='ear.far')){
   for(const [a,b] of [[0,45],[45,90]]){
    const A=slot(a,id),B=slot(b,id);
    if(A&&B&&A.visibility==='visible'&&B.visibility==='visible')
     assert(sameTopology(A,B),'ArtMesh cross-view topology mismatch '+id);
   }
  }
  await Promise.all(parts.filter(x=>x.visibility==='visible').map(async rec=>{
   rec.image=await loadPNG(rec.path,rec.frameSha256);
  }));
  if(Array.isArray(manifest.wholeViews)){
   await Promise.all(manifest.wholeViews.map(async x=>{
    if(endpoints.includes(x.yawDeg))whole.set(x.yawDeg,await loadPNG(x.path,x.sha256));
   }));
  }
  assert(whole.size===3,'source reference PNGs at 0/45/90 required');
  ready=true;
  byId('gate').textContent=seethroughFront
    ?'已加载 P0 正面 PSD 遮挡补绘 + 45°/90° 原画候选 · 视觉检查'
    :(candidateMode?'已加载真实 GIF 修复候选 · 视觉验收待完成':'已加载通过工程与视觉门禁的独立原画');
  byId('info').textContent='角色：'+manifest.characterId+'\n校验图层：'+parts.length+'\n视角：0° / 45° / 90°\nRGBA 源图：已验证 SHA-256';
  render(angle);
 }catch(error){
  problems.push(String(error.message||error));
  byId('gate').textContent='正式资产准入门禁：待通过';
  byId('info').textContent=problems.join('\n')+
  '\n请将经校验的原画、part JSON 和 QA 报告置于 private-assets 目录。';
  render(angle);
 }
}
byId('yaw').addEventListener('input',e=>render(Number(e.target.value)));
for(const button of document.querySelectorAll('button[data-angle]')){
 button.addEventListener('click',()=>{byId('yaw').value=button.dataset.angle;render(Number(button.dataset.angle));});
}
window.__KOMA_P0_VIEWER={inspect:()=>({ready,angle,partCount:registry.size,
 qaStatus:report?.status||null,candidateMode,
 source:seethroughFront?'seethrough-front':'original',
 problems:[...problems]}),renderAt:render};
init();
})();
