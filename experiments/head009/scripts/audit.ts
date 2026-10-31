import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import process from 'node:process';
const out=process.env.HEAD009_OUT??'out/head009';
await mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--disable-gpu-sandbox']});
const page=await browser.newPage({viewport:{width:760,height:800},deviceScaleFactor:1});
try{
 await page.goto(process.env.HEAD009_URL??'http://127.0.0.1:4173/',{waitUntil:'networkidle'});
 await page.waitForFunction(()=>typeof window.head009?.qa==='function');
 const yaws=[0,15,30,45,60,75,90];
 const reports:unknown[]=[];
 for(const yaw of yaws){
  const report=await page.evaluate(y=>window.head009.qa(y),yaw);
  reports.push(report);
  await page.evaluate(y=>window.head009.frame(y),yaw);
  await page.locator('canvas').screenshot({path:join(out,`head-${String(yaw).padStart(3,'0')}.png`)});
  if ([0,45,75,90].includes(yaw)) {
   const img=await page.locator('canvas').screenshot({type:'jpeg',quality:62});
   console.log('HEAD009_MODEL_IMAGE_'+yaw+' '+img.toString('base64'));
  }
 }
 // Compare the source SVG illustrations to the actual beauty raster at the same view.
 // Key-view accuracy is a hard gate; held-out art is only measured and independently reviewed.
 const referenceMatches:{yaw:number;path:string;silhouetteIoU:number;intersection:number;union:number;role:string}[]=[];
 const refs:[number,string,string][]=[
  [0,'front-000.svg','key'],[30,'heldout-030.svg','heldout'],[45,'threequarter-045.svg','key'],
  [60,'heldout-060.svg','heldout'],[75,'heldout-075.svg','heldout'],[90,'profile-right-090.svg','key']
 ];
 for(const [yaw,path,role] of refs){
  const measured=await page.evaluate(async({yaw,path})=>{
   window.head009.frame(yaw,3); // exact diagnostic alpha coverage, independent of painted color
   const stage=document.querySelector<HTMLCanvasElement>('#stage')!;
   const width=stage.width,height=stage.height;
   const a=document.createElement('canvas');a.width=width;a.height=height;
   const b=document.createElement('canvas');b.width=width;b.height=height;
   const aa=a.getContext('2d')!,bb=b.getContext('2d')!;
   aa.drawImage(stage,0,0);
   const src=new Image();src.src='/reference/'+path;await src.decode();
   bb.drawImage(src,0,0,width,height);
   const x=aa.getImageData(0,0,width,height).data,y=bb.getImageData(0,0,width,height).data;
   let intersection=0,union=0;
   for(let i=0;i<x.length;i+=4){
    const isModel=x[i]>200&&x[i+1]>200&&x[i+2]>200;
    const isSource=Math.max(Math.abs(y[i]-233),Math.abs(y[i+1]-237),Math.abs(y[i+2]-245))>30;
    if(isModel&&isSource)intersection++;
    if(isModel||isSource)union++;
   }
   return {intersection,union,silhouetteIoU:union?intersection/union:0};
  },{yaw,path});
  referenceMatches.push({yaw,path,role,...measured});
 }
 const keyArtAligned=referenceMatches.filter(v=>v.role==='key').every(v=>v.silhouetteIoU>=0.93);
 await writeFile(join(out,'head90-art-compare.json'),JSON.stringify({schema:'HEAD009-ART-COMPARISON-V1',referenceMatches,keyArtAligned},null,2)+'\n');
 console.log('HEAD009_REFERENCE_ALIGNMENT '+JSON.stringify({referenceMatches,keyArtAligned}));
 for(const name of ['front-000','threequarter-045','profile-right-090','heldout-030','heldout-060','heldout-075']) {
  await page.goto((process.env.HEAD009_URL??'http://127.0.0.1:4173/')+'reference/'+name+'.svg');
  const el=page.locator('svg');await el.waitFor();
  await el.screenshot({path:join(out,'reference-'+name+'.png')});
  if(name==='profile-right-090'){const img=await el.screenshot({type:'jpeg',quality:62});console.log('HEAD009_REFERENCE_090 '+img.toString('base64'));}
 }
 const report={schema:'HEAD009-QA-V1',angles:yaws,results:reports,status:reports.every((r:any)=>r.result==='PASS_ENGINEERING')&&keyArtAligned?'PASS_ENGINEERING':'FAIL'};
 await writeFile(join(out,'head90-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log('HEAD009_QA '+JSON.stringify(report));
 if(report.status!=='PASS_ENGINEERING')process.exitCode=1;
}catch(e){console.error(e);process.exitCode=1;}
finally{await browser.close();}
