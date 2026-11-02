#!/usr/bin/env node
/** Real Chromium WebGL checks for the C05 3D Anchor view proxy, including provenance. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require(process.env.R1999_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const url=process.env.R1999_URL||'http://127.0.0.1:5180';
 const dest=process.env.R1999_QA_DIR||'out/r1999-c05';
 fs.mkdirSync(dest,{recursive:true});
 const browser=await chromium.launch({headless:true,args:[
  '--no-sandbox','--use-gl=angle','--use-angle=swiftshader',
  '--enable-webgl','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'
 ]});
 const page=await browser.newPage({viewport:{width:1400,height:1000},deviceScaleFactor:1});
 const errors=[],httpErrors=[],external=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',m=>{if(m.type()==='error')errors.push('console: '+m.text());});
 page.on('response',r=>{if(r.status()>=400)httpErrors.push({status:r.status(),url:r.url()})});
 page.on('request',r=>{if(!r.url().startsWith(url+'/'))external.push(r.url())});
 const frame=()=>page.evaluate(()=>{
  const c=document.querySelector('canvas'),d=document.getElementById('r1999-three');
  if(!c||!d)return {error:'CANVAS_MISSING'};
  const w=640,h=640;
  const a=document.createElement('canvas'),b=document.createElement('canvas');
  a.width=b.width=w;a.height=b.height=h;
  a.getContext('2d').drawImage(c,0,0);b.getContext('2d').drawImage(d,0,0);
  const px=a.getContext('2d').getImageData(0,0,w,h).data;
  const py=b.getContext('2d').getImageData(0,0,w,h).data;
  let union=0,intersect=0,changed=0,mae=0,source=0,adapter=0,alphaMismatch=0;
  for(let i=0;i<px.length;i+=4){
    let A=px[i+3]>16,B=py[i+3]>16;
    if(A)source++;if(B)adapter++;if(A&&B)intersect++;
    if(A||B){
      union++;
      const diff=(Math.abs(px[i]-py[i])+Math.abs(px[i+1]-py[i+1])+Math.abs(px[i+2]-py[i+2]))/3;
      mae+=diff;if(diff>24)changed++;
    }
    if(Math.abs(px[i+3]-py[i+3])>16)alphaMismatch++;
  }
  return {iou:intersect/Math.max(1,union),mae:mae/Math.max(1,union),
    changed,source,adapter,alphaMismatch,...window.__R1999_ADAPTER.inspect(),
    label:document.getElementById('r1999-view-provenance')?.textContent};
 });
 try {
 await page.goto(url,{waitUntil:'load'});
 await page.waitForFunction(()=>window.__R1999_ADAPTER?.inspect()?.drawables===263,null,{timeout:35000});
 await page.waitForTimeout(1600);
 const samples=[];
 for(const yaw of [0,15,30,45,60,75,90,45,0]){
  // Test the actual HTML range input to verify the UI dataflow.
  await page.locator('#r1999-yaw').evaluate((el,value)=>{
   el.value=String(value);el.dispatchEvent(new Event('input',{bubbles:true}));
  },yaw);
  await page.waitForTimeout(250);
  const v=await frame();
  samples.push(v);
  if([0,45,90].includes(yaw))
   await page.screenshot({path:path.join(dest,'anchor-yaw'+yaw+'-'+samples.length+'.png')});
 }
 const zero=samples[0],returnZero=samples[samples.length-1],at45=samples[3],at90=samples[6];
 const invalidRejected=await page.evaluate(()=>{
  try{window.__R1999_ADAPTER.setYaw(91);return false;}catch{return true;}
 });
 const tests={
  runtimeLoaded:samples.every(v=>v.drawables===263&&v.masks===4),
  zeroParity:zero.iou>0.995&&zero.mae<1,
  afterReturnParity:returnZero.iou>0.995&&returnZero.mae<1,
  distinctYaw45:at45.changed>500&&at45.cameraYawDeg===45,
  distinctYaw90:at90.changed>1000&&at90.cameraYawDeg===90,
  honesty:samples.every(v=>v.cameraYawDeg===0 ?
    v.provenance==='NATIVE_ART' :
    v.provenance==='ESTIMATED_GEOMETRIC_PROXY'&&v.authored45===false&&v.authored90===false),
  htmlSliderUpdates:at45.label.includes('估算几何代理')&&at90.label.includes('90°'),
  rejectsInvalidAngles:invalidRejected,
  finiteCoverage:samples.every(v=>Number.isFinite(v.iou)&&Number.isFinite(v.mae)&&Number.isFinite(v.alphaMismatch)),
  noBrowserExceptions:errors.length===0,noFailedResources:httpErrors.length===0,noExternalRequests:external.length===0
 };
 const images=fs.readdirSync(dest).filter(x=>x.endsWith('.png')).map(f=>({
  name:f,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dest,f))).digest('hex')
 }));
 const report={schema:'R1999-C05-ANCHOR-PROXY-HTML-QA-V1',mode:'GEOMETRIC_PROXY',
  independentViewTruth:false,
  note:'Animation-source ArtMesh projected with heuristic depths; no independent 45/90 side drawings registered.',
  checkpoints:samples,tests,errors,httpErrors,external,images,
  status:Object.values(tests).every(Boolean)?'PASS_ANCHOR_PROXY_ENGINEERING':'FAIL'};
 fs.writeFileSync(path.join(dest,'c05-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log('C05_RESULT',JSON.stringify({status:report.status,tests,samples:samples.map(x=>({
   yaw:x.cameraYawDeg,iou:x.iou,changed:x.changed,mae:x.mae,provenance:x.provenance
 })),screenshots:images.length,errors}).slice(0,8500));
 if(report.status!=='PASS_ANCHOR_PROXY_ENGINEERING')process.exitCode=1;
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
