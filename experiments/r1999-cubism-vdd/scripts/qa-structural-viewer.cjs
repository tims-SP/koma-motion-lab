#!/usr/bin/env node
/* Verify the delivered HTML is genuinely offline and its controls affect pixels. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require(process.env.R1999_PLAYWRIGHT_MODULE||'playwright');

(async()=>{
 const html=path.resolve(process.env.R1999_VIEWER_HTML||'out/r1999-sonetto/sonetto-360-reference-viewer.html');
 const dir=path.resolve(process.env.R1999_QA_DIR||'out/r1999-sonetto/viewer-qa');
 fs.mkdirSync(dir,{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1366,height:940},acceptDownloads:true});
 const errors=[],httpRequests=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('request',r=>{if(/^https?:/.test(r.url()))httpRequests.push(r.url());});
 const checks={},states={};
 const snapshot=async()=>{
  return page.evaluate(()=>{
   const c=document.getElementById('selected'),d=c.getContext('2d',{willReadFrequently:true}).getImageData(0,0,c.width,c.height).data;
   let coverage=0,red=0,alpha=0;
   for(let i=0;i<d.length;i+=4){if(d[i+3]>16){coverage++;red+=d[i];alpha+=d[i+3];}}
   return {...window.__R1999_REFERENCE.inspect(),coverage,red,alpha};
  });
 };
 try{
  await page.goto('file://'+html,{waitUntil:'load'});
  await page.waitForFunction(()=>window.__R1999_REFERENCE?.inspect()?.ready===true,null,{timeout:30000});
  states.front=await snapshot();
  checks.eightEmbeddedViews=states.front.imageCount===8&&states.front.coverage>50000;
  checks.frontYaw=states.front.angle===0;
  await page.locator('button.angle[data-yaw="90"]').click();
  states.side90=await snapshot();
  checks.sideControl=states.side90.angle===90;
  checks.sideSilhouette=states.side90.coverage<states.front.coverage*0.85;
  checks.sidePixelChange=Math.abs(states.side90.red-states.front.red)>100000;
  await page.screenshot({path:path.join(dir,'viewer-profile-90.png')});
  await page.locator('button.angle[data-yaw="180"]').click();
  states.back180=await snapshot();
  checks.backControl=states.back180.angle===180;
  await page.screenshot({path:path.join(dir,'viewer-back-180.png')});
  await page.evaluate(()=>window.__R1999_REFERENCE.setYaw(360));
  states.wrap=await snapshot();
  checks.fullRotation=states.wrap.angle===360;
  checks.circularIdentity=states.wrap.coverage===states.front.coverage && states.wrap.red===states.front.red;
  await page.locator('#mode').click();
  await page.evaluate(()=>window.__R1999_REFERENCE.setYaw(67));
  states.dissolve67=await snapshot();
  checks.dissolveIsLabeled=states.dissolve67.dissolve===true &&
    await page.locator('#modeInfo').textContent().then(x=>x.includes('不能替代 VDD'));
  const promise=page.waitForEvent('download');
  await page.locator('#png').click();
  const download=await promise;
  const location=path.join(dir,'exported-reference.png');
  await download.saveAs(location);
  const blob=fs.readFileSync(location);
  checks.exportValidPNG=blob.subarray(0,8).toString('hex')==='89504e470d0a1a0a'&&blob.length>50000;
  await page.locator('#play').click();
  await page.waitForTimeout(240);
  const playing=await page.evaluate(()=>window.__R1999_REFERENCE.inspect());
  await page.locator('#play').click();
  checks.animationChangesYaw=playing.playing===true&&playing.angle!==67;
  checks.creatorCredit=await page.locator('footer').textContent().then(x=>x.includes('WTHN_Ross')&&x.includes('BLUEPOCH'));
  checks.sourceClassification=await page.locator('aside').textContent().then(x=>x.includes('三维结构参考')&&x.includes('独立绘制'));
  checks.offline=httpRequests.length===0;
  checks.browserErrorsAbsent=errors.length===0;
 }catch(e){states.exception=e.stack||String(e);}
 finally {await browser.close();}
 const report={schema:'R1999-STRUCTURAL-OFFLINE-HTML-QA-V1',source:'PMX Blender 4.0 structural renders',
   htmlFile:path.basename(html),checks,states,errors,httpRequests,
   status:Object.keys(checks).length===15&&Object.values(checks).every(Boolean)&&!states.exception?'PASS_OFFLINE_360_REFERENCE_VIEWER':'FAIL'};
 fs.writeFileSync(path.join(dir,'offline-viewer-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log('OFFLINE_VIEWER_QA',JSON.stringify({status:report.status,checks,exception:states.exception,errors}).slice(0,7000));
 if(report.status!=='PASS_OFFLINE_360_REFERENCE_VIEWER')process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
