#!/usr/bin/env node
// Measure the head-region collapse of the geometry-only view proxy.
// This protects the visual acceptance gate from conflating valid WebGL output with a side face.
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.R1999_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const url=process.env.R1999_URL||'http://127.0.0.1:5181';
 const output=process.env.R1999_VISUAL_QA_REPORT||'out/r1999-c05/visual-readiness.json';
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1400,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 const roi={left:245,top:60,right:465,bottom:275};
 const pixelCount=()=>page.evaluate((region)=>{
  const canvases=[document.querySelector('canvas'),document.getElementById('r1999-three')];
  return canvases.map(canvas=>{
    const c=document.createElement('canvas');c.width=640;c.height=640;
    const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(canvas,0,0);
    const data=ctx.getImageData(region.left,region.top,region.right-region.left,region.bottom-region.top).data;
    let count=0,opaque=0;
    for(let j=0;j<data.length;j+=4){if(data[j+3]>16)count++;if(data[j+3]>220)opaque++;}
    return {coveredPixels:count,opaquePixels:opaque};
  });
 },roi);
 try{
  await page.goto(url);
  await page.waitForFunction(()=>window.__R1999_ADAPTER?.inspect()?.drawables===263,null,{timeout:30000});
  await page.waitForTimeout(900);
  const states=[];
  for(const yaw of [0,45,90]){
   await page.locator('#r1999-yaw').evaluate((el,value)=>{
    el.value=String(value);el.dispatchEvent(new Event('input',{bubbles:true}));
   },yaw);
   await page.waitForTimeout(360);
   const [native,proxy]=await pixelCount();
   const provenance=await page.evaluate(()=>window.__R1999_ADAPTER.inspect().provenance);
   states.push({yawDeg:yaw,native,proxy,headCoverageRatio:proxy.coveredPixels/Math.max(1,native.coveredPixels),provenance});
  }
  const a=states[0],c=states[2];
  const independentArtReady=false;
  const visualPass=independentArtReady&&c.headCoverageRatio>=0.65;
  const guardrail=(a.headCoverageRatio>0.95)&&
    c.provenance==='ESTIMATED_GEOMETRIC_PROXY'&&
    !independentArtReady&&!visualPass&&errors.length===0;
  const report={schema:'R1999-C05-VISUAL-READINESS-V1',
    region:roi,regionNote:'Head ROI established from native Sonetto portrait in 640x640 comparison canvas',
    states,independentArtReady,visualPass,
    finding:'High yaw is geometry-only: the side-face silhouette is not supported by independent art. The visual acceptance gate remains closed.',
    errors,status:guardrail?'PASS_VISUAL_GATE_GUARDRAIL':'FAIL_VISUAL_GATE_TEST'};
  fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
  console.log('C05_VISUAL',JSON.stringify(report));
  if(!guardrail)process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
