#!/usr/bin/env node
'use strict';
/** Real-browser P1 ArtMesh screenshot and independent eye-motion smoke test. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const http=require('node:http');
const ROOT=path.resolve(__dirname,'../../..');
const experiment=path.resolve(__dirname,'..');
const psdSource=process.env.KOMA_P1_SOURCE==='seethrough';
const output=path.resolve(process.env.KOMA_P1_QA_OUT||
  path.join(experiment,psdSource
    ?'private-assets/p4-see-through/front/browser'
    :'private-assets/p1-front/browser'));
const {chromium}=require(process.env.KOMA_PLAYWRIGHT_MODULE||'playwright');
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
 '.json':'application/json; charset=utf-8','.png':'image/png','.jpg':'image/jpeg'};
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const server=http.createServer((req,res)=>{
 try{
  const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const file=path.resolve(ROOT,'.'+p);
  if(!file.startsWith(ROOT+path.sep)||!fs.statSync(file).isFile())
    throw Error('not found');
  res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream',
    'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
  fs.createReadStream(file).pipe(res);
 }catch{
  res.writeHead(404,{'Content-Type':'text/plain'});res.end('Not Found');
 }
});
async function main(){
 fs.mkdirSync(output,{recursive:true});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url='http://127.0.0.1:'+server.address().port+
  '/experiments/gif-multiview-keyparts-mvp/review/p1-front.html'+
  (psdSource?'?source=seethrough':'');
 const errors=[],failedRequests=[],screens=[];
 let browser;
 try{
  browser=await chromium.launch({headless:true,
    args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1500,height:970},deviceScaleFactor:1});
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('response',res=>{if(res.status()>=400)failedRequests.push(res.url());});
  await page.goto(url,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>{
   const v=window.__P1_VIEWER?.inspect();
   return Boolean(v && (v.ready || v.error));
  },null,{timeout:30000});
  const initial=await page.evaluate(()=>window.__P1_VIEWER.inspect());
  const capture=async(label)=>{
   const target=path.join(output,label+'.png');
   await page.screenshot({path:target,fullPage:true});
   const info=await page.locator('#metrics').innerText();
   screens.push({name:label,file:target,sha256:sha(target),metricText:info});
  };
  if(initial.ready){
   await capture(psdSource?'p4-psd-front-default':'p1-front-default');
   await page.evaluate(()=>window.__P1_VIEWER.setEyeNear(10));
   await capture(psdSource?'p4-psd-eye-near-10px':'p1-front-eye-near-10px');
   await page.locator('#hair').click();
   await capture(psdSource?'p4-psd-hair-parts':'p1-front-hair-parts');
   await page.evaluate(()=>window.__P1_VIEWER.reset());
   const final=await page.evaluate(()=>window.__P1_VIEWER.inspect());
   if(final.values.eyeNear!==0)errors.push('reset returned wrong eye position');
  }else{
   await capture(psdSource?'p4-psd-source-gate':'p1-front-source-gate');
  }
  const qaFile=psdSource
    ?'private-assets/p4-see-through/front/integrated/integration-qa.json'
    :'private-assets/p1-front/engineering-qa.json';
  const sourceQA=JSON.parse(fs.readFileSync(path.join(experiment,qaFile),'utf8'));
  const expectedStatus=psdSource?'PASS_SEMANTIC_LAYER_REGISTRATION':'PASS_STRUCTURAL_ENGINEERING';
  const status=initial.ready && initial.source===(psdSource?'seethrough':'original') &&
    sourceQA.status===expectedStatus &&
    screens.length===3 && errors.length===0 && failedRequests.length===0 ?
    (psdSource?'PASS_P4_PSD_BROWSER_ENGINEERING':'PASS_P1_BROWSER_ENGINEERING'):
    (psdSource?'FAIL_P4_PSD_BROWSER_ENGINEERING':'FAIL_P1_BROWSER_ENGINEERING');
  const qa={schema:psdSource?'KOMA-P0-P4-PSD-BROWSER-QA-V1':'KOMA-P0-P1-BROWSER-QA-V1',
    characterId:'p0_character_001',status,sourceReady:initial.ready,
    sourceSelection:psdSource?'seethrough':'original',
    assetsSHAverified:initial.ready,renderer:'Chromium Playwright Canvas2D',
    initial,sourceQASummary:{status:sourceQA.status,
      passed:sourceQA.passed,failed:sourceQA.failed,measures:sourceQA.measures},
    shots:screens,errors,failedRequests,
    artStatus:'INDEPENDENT_MOTION_ARTISTIC_REVIEW_REQUIRED'};
  fs.writeFileSync(path.join(output,'browser-qa.json'),JSON.stringify(qa,null,2)+'\n');
  console.log(JSON.stringify({status:qa.status,sourceReady:qa.sourceReady,
    shots:screens.map(x=>({name:x.name,sha256:x.sha256})),errors,failedRequests},null,2));
  process.exitCode=status.startsWith('PASS')?0:2;
 }finally{
  if(browser)await browser.close();
  await new Promise(resolve=>server.close(resolve));
 }
}
main().catch(e=>{console.error(e.stack);server.close();process.exitCode=3;});
