#!/usr/bin/env node
'use strict';
const {chromium}=require('/root/koma-motion-r1999/work/browser/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../private-assets/exports/p15-40-profile-review');
const QA=path.resolve(__dirname,'../evidence/p15-40-browser-qa.json');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 let browser;const result={schema:'KOMA-P15-40-CHROMIUM-REVIEW-V1',checks:[],screenshots:[],errors:[],failedRequests:[]};
 try{
  browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  for(const viewport of [{name:'desktop',width:1440,height:850},{name:'mobile',width:390,height:844}]){
   const page=await browser.newPage({viewport:{width:viewport.width,height:viewport.height}});
   page.on('pageerror',e=>result.errors.push(String(e)));
   page.on('requestfailed',r=>result.failedRequests.push(r.url()+': '+r.failure()?.errorText));
   await page.goto('file://'+path.join(ROOT,'index.html'));
   for(let index=0;index<13;index++)for(const mode of ['whole','zoom','layers']){
    const valid=await page.evaluate(async({index,mode})=>window.__KOMA_P15_40.show(index,mode),{index,mode});
    if(!valid)throw new Error(`Render failed: ${viewport.name} ${index} ${mode}`);
    const imgs=await page.locator('#gallery img').evaluateAll(items=>items.map(x=>({width:x.naturalWidth,height:x.naturalHeight,loaded:x.complete})));
    if(imgs.length!==2||imgs.some(x=>!x.loaded||x.width<400||x.height<400))throw new Error('Invalid images '+JSON.stringify(imgs));
    result.checks.push({viewport:viewport.name,index,mode,images:imgs.length});
    if(viewport.name==='desktop'&&[0,6,8,12].includes(index)&&['whole','zoom'].includes(mode)){
     const file=path.join(ROOT,`browser-${viewport.name}-${index}-${mode}.png`);
     await page.locator('#gallery').screenshot({path:file});
     result.screenshots.push({path:path.relative(path.resolve(__dirname,'..'),file),sha256:sha(file)});
    }
   }
   await page.close();
  }
  if(result.errors.length||result.failedRequests.length)throw Error(JSON.stringify(result.errors.concat(result.failedRequests)));
  result.status='P15_40_BROWSER_REVIEW_READY';result.viewportChecks=result.checks.length;
  fs.writeFileSync(QA,JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({checks:result.viewportChecks,screenshots:result.screenshots.length,errors:result.errors.length}));
 } finally {if(browser)await browser.close()}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
