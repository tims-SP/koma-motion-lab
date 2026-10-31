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
 for(const name of ['front-000','threequarter-045','profile-right-090','heldout-030','heldout-060','heldout-075']) {
  await page.goto((process.env.HEAD009_URL??'http://127.0.0.1:4173/')+'reference/'+name+'.svg');
  const el=page.locator('svg');await el.waitFor();
  await el.screenshot({path:join(out,'reference-'+name+'.png')});
  if(name==='profile-right-090'){const img=await el.screenshot({type:'jpeg',quality:62});console.log('HEAD009_REFERENCE_090 '+img.toString('base64'));}
 }
 const report={schema:'HEAD009-QA-V1',angles:yaws,results:reports,status:reports.every((r:any)=>r.result==='PASS_ENGINEERING')?'PASS_ENGINEERING':'FAIL'};
 await writeFile(join(out,'head90-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log('HEAD009_QA '+JSON.stringify(report));
 if(report.status!=='PASS_ENGINEERING')process.exitCode=1;
}catch(e){console.error(e);process.exitCode=1;}
finally{await browser.close();}
