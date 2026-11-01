#!/usr/bin/env node
/* Browser-based acceptance of the actual Cubism model and HTML controls. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.R1999_PLAYWRIGHT_MODULE || 'playwright');

async function main() {
  const base=process.env.R1999_URL || 'http://127.0.0.1:5176';
  const dir=process.env.R1999_QA_DIR || path.resolve('out/r1999-native');
  fs.mkdirSync(dir,{recursive:true});
  const browser=await chromium.launch({headless:true,args:[
    '--no-sandbox','--disable-gpu-sandbox','--use-gl=angle',
    '--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader',
    '--ignore-gpu-blocklist'
  ]});
  const page=await browser.newPage({viewport:{width:1366,height:900},
    deviceScaleFactor:1,acceptDownloads:true});
  const failures=[],errors=[],badResponses=[],external=[];
  page.on('pageerror',e=>errors.push(e.stack || String(e)));
  page.on('response',r=>{if(r.status()>=400)badResponses.push({status:r.status(),url:r.url()});});
  page.on('request',r=>{if(!r.url().startsWith(base+'/') && !r.url().startsWith('data:'))
    external.push(r.url());});
  let result={};
  try{
    await page.goto(base,{waitUntil:'load'});
    await page.waitForFunction(()=>window.__R1999_REVIEW?.getState()?.ready===true,null,{timeout:30000});
    await page.waitForTimeout(1300);
    const state0=await page.evaluate(()=>window.__R1999_REVIEW.getState());
    await page.screenshot({path:path.join(dir,'native-baseline.png')});
    await page.locator('[data-motion="b_diantou"]').click();
    await page.waitForTimeout(800);
    const nod=await page.evaluate(()=>window.__R1999_REVIEW.getState());
    await page.screenshot({path:path.join(dir,'native-nod.png')});
    await page.locator('[data-motion="b_yaotou"]').click();
    await page.waitForTimeout(1000);
    const shake=await page.evaluate(()=>window.__R1999_REVIEW.getState());
    await page.screenshot({path:path.join(dir,'native-shake.png')});
    await page.locator('#r1999-expressions').selectOption('e_kaixin');
    await page.waitForTimeout(900);
    const expression=await page.evaluate(()=>window.__R1999_REVIEW.getState());
    await page.screenshot({path:path.join(dir,'native-happy.png')});
    await page.locator('#r1999-pause').click();
    const paused=await page.evaluate(()=>window.__R1999_REVIEW.getState());
    const downloadPromise=page.waitForEvent('download');
    await page.locator('#r1999-png').click();
    const downloaded=await downloadPromise;
    const pngPath=path.join(dir,'native-export.png');
    await downloaded.saveAs(pngPath);
    const bytes=fs.readFileSync(pngPath);
    if(bytes.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')failures.push('png_signature');
    if(bytes.length<5000)failures.push('png_export_too_small');
    if(state0.drawableCount<50)failures.push('drawable_count');
    if(state0.parameterCount<30)failures.push('parameter_count');
    if(nod.lastMotion!=='b_diantou'||shake.lastMotion!=='b_yaotou')failures.push('motion_switching');
    if(expression.lastExpression!=='e_kaixin')failures.push('expression_switching');
    if(!paused.paused)failures.push('pause_state');
    if(errors.length || badResponses.length || external.length)failures.push('browser_requests_or_exceptions');
    const pixelInfo=await page.evaluate(()=>{
      const c=document.querySelector('canvas');
      return {canvas:[c.width,c.height],webgl:!!c.getContext('webgl2'),controlPanel:!!document.getElementById('r1999-panel')};
    });
    result={initial:state0,nod,shake,expression,paused,pixelInfo,pngBytes:bytes.length};
  } catch(e) {
    failures.push(String(e));
  } finally {
    await page.close(); await browser.close();
  }
  const report={
    schema:'R1999-NATIVE-CUBISM-BROWSER-QA-V1',
    status:failures.length?'FAIL':'PASS_BROWSER_NATIVE_INTERACTION',
    url:'localhost-only',
    engine:'Official Cubism Web Samples + Cubism Core',
    environment:'Chromium headless WebGL2 SwiftShader 1366x900',
    ...result,errors,badResponses,external,failures
  };
  fs.writeFileSync(path.join(dir,'native-browser-qa.json'),JSON.stringify(report,null,2)+'\n');
  console.log('R1999_HTML_NATIVE_QA '+JSON.stringify(report));
  if(failures.length)process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1});
