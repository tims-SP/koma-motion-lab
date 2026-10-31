import {chromium} from 'playwright';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import type {OrganLandmarks} from '../src/organ-register';
import {compareViewLandmarks} from '../src/organ-register';
const out=process.env.HEAD009_OUT??'out/head009';
const reg=JSON.parse(await readFile('reference/organ-landmarks.json','utf8')) as OrganLandmarks;
const yaws=[0,30,45,60,75,90];
await mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--disable-gpu-sandbox']});
const page=await browser.newPage({viewport:{width:1400,height:760},deviceScaleFactor:1});
try{
 await page.goto(process.env.HEAD009_URL??'http://127.0.0.1:4173/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>typeof window.head009?.qa==='function');
 const result=[];
 for(const yaw of yaws){
  const compare=compareViewLandmarks(reg,yaw);
  // Negative control: a deliberately displaced nose must exceed the same reference-error budget.
  const shifted=compareViewLandmarks(reg,yaw,80);
  const caughtFault=shifted.errors['nose.tip']?.errorPx!==undefined&&shifted.errors['nose.tip'].errorPx!>40;
  // We also use actual render-target ID pixels, so this is not merely a synthetic math comparison.
  const visibility=await page.evaluate(y=>window.head009.qa(y).visibleParts,yaw);
  const organPixels=Object.fromEntries(Object.entries(reg.organParts).map(([semantic,part])=>[semantic,visibility[part]??0]));
  const predictions=Object.fromEntries(Object.entries(compare.errors).filter(([_,v])=>v.errorPx>=0).map(([k,v])=>[k,v.predicted]));
  const actualVisiblePartProbes=await page.evaluate(({yaw,predictions,organParts})=>window.head009.probeParts(yaw,predictions,organParts),{yaw,predictions,organParts:reg.organParts});
  result.push({...compare,organPixels,actualVisiblePartProbes,nosePositionFaultDetected:caughtFault});
  const view=reg.views.find(v=>v.yaw===yaw)!;
  const png=await page.evaluate(async({yaw,view,compare})=>{
   window.head009.frame(yaw);
   const img=document.querySelector<HTMLCanvasElement>('#stage')!;
   const source=new Image();source.src='/reference/'+view.source;await source.decode();
   const c=document.createElement('canvas');c.width=1280;c.height=700;
   const g=c.getContext('2d')!;
   g.fillStyle='#1c2638';g.fillRect(0,0,1280,700);
   g.drawImage(source,0,0,640,640);g.drawImage(img,640,0,640,640);
   g.font='bold 16px sans-serif';
   for(const [semantic,match] of Object.entries(compare.errors)){
    const ref=match.reference;const predicted=match.predicted;
    g.lineWidth=2;g.strokeStyle='#ffdc65';g.fillStyle='#ffdc65';
    g.beginPath();g.arc(ref[0],ref[1],4,0,Math.PI*2);g.fill();
    if(match.errorPx>=0){
     g.beginPath();g.arc(predicted[0]+640,predicted[1],4,0,Math.PI*2);g.fill();
     g.strokeStyle='#67ddff';g.beginPath();g.moveTo(ref[0]+640,ref[1]);g.lineTo(predicted[0]+640,predicted[1]);g.stroke();
     g.fillStyle='#67ddff';g.beginPath();g.arc(ref[0]+640,ref[1],3,0,Math.PI*2);g.fill();
    }
   }
   g.fillStyle='white';g.font='bold 17px sans-serif';
   g.fillText('Independent source '+view.source,15,30);
   g.fillText('WebGL '+yaw+' deg | yellow: runtime, cyan: held-out target',652,30);
   g.fillStyle='#d3dce7';g.font='15px sans-serif';
   const legend=Object.entries(compare.errors).map(([k,v])=>k+': '+(v.errorPx<0?'MISSING':v.errorPx.toFixed(1)+'px'));
   for(let i=0;i<legend.length;i++)g.fillText(legend[i]!,15+(i%3)*425,658+Math.floor(i/3)*15);
   return c.toDataURL('image/png').split(',')[1];
  },{yaw,view,compare});
  await writeFile(join(out,'organ-compare-'+String(yaw).padStart(3,'0')+'.png'),Buffer.from(png,'base64'));
  console.log('HEAD009_ORGAN_'+yaw+' '+JSON.stringify({max:compare.maxErrorPx,mean:compare.meanErrorPx,negativeFault:caughtFault,pixels:organPixels}));
 }
 const key=result.filter(x=>x.role==='key'),heldout=result.filter(x=>x.role==='heldout');
 const visibleAnatomy=key.every(x=>['nose','mouth','face','farEye','farEar'].every(p=>Object.entries(x.organPixels).some(([k,v])=>reg.organParts[k]===p&&v>0)));
 const keyCoordinatePass=key.every(x=>(x.maxErrorPx??Infinity)<=8);
 const negativeControlsPass=result.every(x=>x.nosePositionFaultDetected);
 const keyVisibleMisses=key.flatMap(x=>{
  const annotated=reg.views.find(v=>v.yaw===x.yaw)!;
  return Object.entries(x.actualVisiblePartProbes)
   .filter(([name,p])=>!p.within8px&&!annotated.occludedLandmarks?.includes(name))
   .map(([name,p])=>({yaw:x.yaw,name,...p}));
 });
 const intentionalKeyOcclusions=key.map(x=>({yaw:x.yaw,labels:reg.views.find(v=>v.yaw===x.yaw)!.occludedLandmarks??[]}));
 const keyVisibleLandmarkPass=keyVisibleMisses.length===0;
 const heldoutSummary=heldout.map(x=>({yaw:x.yaw,max:x.maxErrorPx,mean:x.meanErrorPx,byOrgan:Object.fromEntries(Object.entries(x.errors).map(([k,v])=>[k,v.errorPx]))}));
 const report={schema:'HEAD009-ORGAN-QA-V1',sourceSha:'see source-hashes.json',angles:yaws,results:result,
  keyCoordinatePass,visibleAnatomy,negativeControlsPass,keyVisibleLandmarkPass,keyVisibleMisses,intentionalKeyOcclusions,heldoutSummary,
  status:keyCoordinatePass&&negativeControlsPass&&keyVisibleLandmarkPass?'PASS_ORGAN_REFERENCE_ENGINEERING':'FAIL_ORGAN_REFERENCE_ENGINEERING',
  visualStatus:'PENDING_INDEPENDENT_REVIEW',scope:'2D landmark reprojection + actual visible Part-ID pixels; not proof of source landmark raster visibility nor anatomical quality'};
 await writeFile(join(out,'organ-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log('HEAD009_ORGAN_SUMMARY '+JSON.stringify({status:report.status,keyCoordinatePass,visibleAnatomy,negativeControlsPass,keyVisibleLandmarkPass,keyVisibleMisses,intentionalKeyOcclusions,heldoutSummary}));
 if(report.status!=='PASS_ORGAN_REFERENCE_ENGINEERING')process.exitCode=1;
}catch(err){console.error(err);process.exitCode=1;}
finally{await browser.close();}
