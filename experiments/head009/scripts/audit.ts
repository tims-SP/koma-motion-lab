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
 }
 const report={schema:'HEAD009-QA-V1',angles:yaws,results:reports,status:reports.every((r:any)=>r.result==='PASS_ENGINEERING')?'PASS_ENGINEERING':'FAIL'};
 await writeFile(join(out,'head90-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log('HEAD009_QA '+JSON.stringify(report));
 if(report.status!=='PASS_ENGINEERING')process.exitCode=1;
}catch(e){console.error(e);process.exitCode=1;}
finally{await browser.close();}
