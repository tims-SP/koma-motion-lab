#!/usr/bin/env node
'use strict';
/** Capture actual P0 source-layer interpolation from a browser, with source gate. */
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..');
const experiment=path.resolve(__dirname,'..');
const out=path.resolve(process.env.KOMA_QA_OUT||'/tmp/koma-gif-review');
const browserModule=process.env.KOMA_PLAYWRIGHT_MODULE||'playwright';
const candidateMode=process.env.KOMA_CANDIDATE_MODE==='1';
const {chromium}=require(browserModule);
function sha(pathname){return crypto.createHash('sha256').update(fs.readFileSync(pathname)).digest('hex');}
const mime={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8',
 '.json':'application/json','.png':'image/png','.gif':'image/gif','.css':'text/css; charset=utf-8'};
const server=http.createServer((req,res)=>{
 try{
  const raw=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const requested=path.resolve(root,'.'+raw);
  if(!requested.startsWith(root+path.sep))throw Error('directory boundary');
  if(!fs.statSync(requested).isFile())throw Error('file required');
  res.writeHead(200,{'Content-Type':mime[path.extname(requested)]||'application/octet-stream',
       'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
  fs.createReadStream(requested).pipe(res);
 }catch{
  res.writeHead(404,{'Content-Type':'text/plain'});res.end('File unavailable');
 }
});
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const port=server.address().port;
 const url='http://127.0.0.1:'+port+
   '/experiments/gif-multiview-keyparts-mvp/review/index.html'+(candidateMode?'?mode=candidate':'');
 const errors=[],httpErrors=[],frames=[];
 let browser;
 try{
  browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1450,height:940},deviceScaleFactor:1});
  page.on('pageerror',error=>errors.push(String(error.stack||error)));
  page.on('response',response=>{if(response.status()>=400)httpErrors.push(response.url());});
  await page.goto(url,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>window.__KOMA_P0_VIEWER&&
    (window.__KOMA_P0_VIEWER.inspect().ready ||
    window.__KOMA_P0_VIEWER.inspect().problems.length>0),null,{timeout:20000});
  const initial=await page.evaluate(()=>window.__KOMA_P0_VIEWER.inspect());
  const status=initial.ready?'READY':'BLOCKED_SOURCE_ASSETS';
  if(initial.ready){
   for(const angle of [0,22.5,45,67.5,90]){
    await page.evaluate(a=>window.__KOMA_P0_VIEWER.renderAt(a),angle);
    await page.waitForTimeout(120);
    const metrics=await page.evaluate(()=>{
      const canvas=document.getElementById('result');
      const data=canvas.getContext('2d',{willReadFrequently:true}).getImageData(0,0,1024,1024).data;
      let pixels=0,rgbaSum=0;
      for(let i=0;i<data.length;i+=4)if(data[i+3]>0){
        pixels++;rgbaSum+=data[i]+data[i+1]*3+data[i+2]*7+data[i+3]*11;
      }
      return {pixels,rgbaSum};
    });
    const name='yaw'+String(angle).replace('.','p').padStart(3,'0')+'.png';
    const full=path.join(out,name);
    await page.screenshot({path:full,fullPage:true});
    frames.push({yawDeg:angle,screenshot:name,sha256:sha(full),...metrics});
   }
  }else{
   const gatePath=path.join(out,'asset-gate.png');
   await page.screenshot({path:gatePath,fullPage:true});
   frames.push({type:'source_gate',screenshot:'asset-gate.png',sha256:sha(gatePath)});
  }
  const changing=initial.ready&&frames.every(x=>x.pixels>1000)&&
   new Set(frames.map(x=>x.rgbaSum)).size>=4;
  const result={schema:'KOMA-P0-VDD-BROWSER-QA-V1',characterId:'p0_character_001',
   status:initial.ready?(changing&&errors.length===0?(candidateMode?'CANDIDATE_RENDER_ENGINEERING_PASS':'RENDER_ENGINEERING_PASS'):'RENDER_CHECKS_FAIL'):status,
   sourceReady:initial.ready,initial,frames,errors,httpErrors,
   visualAcceptance:initial.ready?(candidateMode?'CANDIDATE_ART_VISUAL_REVIEW_REQUIRED':'HUMAN_SOURCE_AND_HOLDOUT_REVIEW_REQUIRED'):'SOURCE_ASSET_BYTES_REQUIRED'};
  fs.writeFileSync(path.join(out,'browser-qa.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({status:result.status,sourceReady:result.sourceReady,frames:frames.length,
    errors,gate:initial.problems},null,2));
  process.exitCode=['RENDER_ENGINEERING_PASS','CANDIDATE_RENDER_ENGINEERING_PASS'].includes(result.status)?0:2;
 }finally{
  if(browser)await browser.close();
  await new Promise(resolve=>server.close(resolve));
 }
})().catch(error=>{console.error(error.stack||error);server.close();process.exitCode=3;});
