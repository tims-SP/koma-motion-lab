const {chromium}=require(process.env.R1999_PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const out=process.env.R1999_QA_DIR || path.resolve('out/r1999-c03');
const base=process.env.R1999_URL || 'http://127.0.0.1:5177';
fs.mkdirSync(out,{recursive:true});
const pause=(ms)=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1400,height:860},deviceScaleFactor:1});
 const errors=[],httpErrors=[],unexpectedRequests=[];
 page.on('pageerror',e=>errors.push(e.stack||String(e)));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 page.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()})});
 page.on('request',r=>{if(!r.url().startsWith(base+'/'))unexpectedRequests.push(r.url())});
 const evaluateFrame=()=>page.evaluate(()=>{
  window.__R1999_ADAPTER.renderOnce();
  const c=document.querySelector('canvas'),d=document.querySelector('#r1999-three');
  const W=640,H=640,a=document.createElement('canvas'),b=document.createElement('canvas');
  a.width=b.width=W;a.height=b.height=H;
  const ac=a.getContext('2d',{willReadFrequently:true}),bc=b.getContext('2d',{willReadFrequently:true});
  ac.drawImage(c,0,0);bc.drawImage(d,0,0);
  const x=ac.getImageData(0,0,W,H).data,y=bc.getImageData(0,0,W,H).data;
  let union=0,intersection=0,source=0,adapter=0,largeDiff=0,sumErr=0,alphaErrors=0,foreground=0,maxDiff=0;
  for(let i=0;i<x.length;i+=4){
   let A=x[i+3]>16,B=y[i+3]>16;if(A)source++;if(B)adapter++;
   if(A||B){union++;const delta=(Math.abs(x[i]-y[i])+Math.abs(x[i+1]-y[i+1])+Math.abs(x[i+2]-y[i+2]))/3;sumErr+=delta;foreground++;if(delta>24)largeDiff++;maxDiff=Math.max(maxDiff,delta);}
   if(A&&B)intersection++;
   if(Math.abs(x[i+3]-y[i+3])>16)alphaErrors++;
  }
  const preview=window.__R1999_ADAPTER.inspect();
  return {iou:intersection/Math.max(1,union),sourcePixels:source,adapterPixels:adapter,
   rgbMae:sumErr/Math.max(1,foreground),changedPixels:largeDiff,
   maxChannelMeanError:maxDiff,alphaMismatches:alphaErrors,maskGroups:preview.masks,
   drawableCount:preview.drawables,mode:preview.diagnosticFault};
 });
 try{
  await page.goto(base,{waitUntil:'load'});
  await page.waitForFunction(()=>window.__R1999_ADAPTER?.inspect()?.drawables===263,null,{timeout:35000});
  await page.waitForTimeout(2500);
  const samples={};
  for(const [label,motion,expression,duration] of [
   ['idle',null,null,450],
   ['nod','b_diantou',null,1000],
   ['shake','b_yaotou',null,800],
   ['happy',null,'e_kaixin',800],
   ['surprised',null,'e_chijing',800]]){
    await page.evaluate(({motion,expression})=>{
      window.__R1999_PAUSED=false;
      if(motion)window.__R1999_REVIEW.playMotion(motion);
      if(expression)window.__R1999_REVIEW.setExpression(expression);
    },{motion,expression});
    await pause(duration);
    await page.evaluate(()=>{window.__R1999_PAUSED=true});
    await pause(160);
    samples[label]=await evaluateFrame();
    await page.screenshot({path:path.join(out,'comparison-'+label+'.png')});
  }
  await page.evaluate(()=>window.__R1999_ADAPTER.setFault('mask'));
  await pause(200);
  const maskFault=await evaluateFrame();
  await page.evaluate(()=>window.__R1999_ADAPTER.setFault('order'));
  await pause(200);
  const orderFault=await evaluateFrame();
  await page.evaluate(()=>window.__R1999_ADAPTER.setFault('uv'));
  await pause(300);
  const uvFault=await evaluateFrame();
  await page.evaluate(()=>window.__R1999_ADAPTER.setFault('none'));
  await pause(200);
  const recovered=await evaluateFrame();
  const validations={
    all5HighOverlap:Object.values(samples).every(v=>v.iou>=0.995),
    all5LowRGBError:Object.values(samples).every(v=>v.rgbMae<=1),
    all5AlphaAligned:Object.values(samples).every(v=>v.alphaMismatches<=120),
    maskedDrawablesValidated:maskFault.changedPixels>=samples.surprised.changedPixels+50 && maskFault.alphaMismatches>=samples.surprised.alphaMismatches+40,
    orderValidated:orderFault.changedPixels>samples.surprised.changedPixels+150,
    uvValidated:uvFault.changedPixels>samples.surprised.changedPixels+1000,
    recovered:recovered.iou>0.995&&recovered.rgbMae<=1,
    noConsoleErrors:errors.length===0,
    noHttpErrors:httpErrors.length===0,
    noUnexpectedNetwork:unexpectedRequests.length===0
  };
  const screenshotHash=fs.readdirSync(out).filter(f=>f.endsWith('.png')).map(f=>({filename:f,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(out,f))).digest('hex')}));
  const result={schema:'R1999-C03-REAL-PIXEL-QA-V1',engine:'Official Cubism Web 5-r.4 vs Three.js 0.181.0',canvas:[640,640],
   source:'private Sonetto asset pinned to 45e75248...',samples,negative:{maskFault,orderFault,uvFault,recovered},checks:validations,
   browserErrors:errors,httpErrors,unexpectedRequests,screenshotHash,
   status:Object.values(validations).every(Boolean)?'PASS_C03_ENGINEERING':'FAIL_C03_ENGINEERING'};
  fs.writeFileSync(path.join(out,'c03-qa.json'),JSON.stringify(result,null,2)+'\n');
  console.log('C03_MULTIFRAME',JSON.stringify({status:result.status,samples,negative:{maskFault,orderFault,uvFault,recovered},checks:validations,screenshots:screenshotHash.length,errors}).slice(0,12000));
  if(result.status.startsWith('FAIL'))process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error('FATAL',e);process.exitCode=1});
