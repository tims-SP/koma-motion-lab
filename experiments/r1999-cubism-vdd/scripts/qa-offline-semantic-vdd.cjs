#!/usr/bin/env node
/* Validate the self-contained private Cubism+PMX 45/90 semantic reviewer. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require(process.env.R1999_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const file=path.resolve(process.env.R1999_OFFLINE_HTML);
 const output=path.resolve(process.env.R1999_QA_DIR||'out/r1999-semantic-offline');
 const refManifest=JSON.parse(fs.readFileSync(process.env.R1999_PREDICTIONS_MANIFEST,'utf8'));
 fs.mkdirSync(output,{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1366,height:900}});
 const browserErrors=[],network=[];
 page.on('pageerror',e=>browserErrors.push(String(e)));
 page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
 const checks={},details={};
 try{
  await page.goto('file://'+file,{waitUntil:'load'});
  await page.waitForFunction(()=>window.__R1999_LAYER_LAB?.inspect()?.proxy===16,null,{timeout:30000});
  const current=await page.evaluate(()=>window.__R1999_LAYER_LAB.inspect());
  checks.eightSemanticPairs=current.proxy===16&&current.paired===8&&current.synthetic===0&&current.candidate===0;
  checks.independentArtGatePreserved=current.visualAcceptance==='AWAITING_VALIDATED_INDEPENDENT_ART';
  await page.waitForFunction(()=>document.querySelector('#nativeHint')?.textContent.includes('Drawables'),null,{timeout:20000});
  checks.nativeCubismReference=await page.locator('#nativeHint').innerText().then(x=>x.includes('PARTS_01_')&&x.includes('SHA'));
  await page.waitForFunction(()=>document.querySelector('#geometryHint')?.textContent.includes('PMX'),null,{timeout:20000});
  checks.true3DReference=await page.locator('#geometryHint').innerText().then(x=>x.includes('768×768'));
  checks.attribution=await page.locator('aside').innerText().then(x=>x.includes('WTHN_Ross')&&x.includes('BLUEPOCH'));
  const match=[];
  for(const yaw of [45,67,90]){
   await page.locator('#yaw').evaluate((el,y)=>{
    el.value=String(y);el.dispatchEvent(new Event('input',{bubbles:true}));
   },yaw);
   const base64=await page.evaluate(()=>document.getElementById('center').toDataURL('image/png').split(',')[1]);
   const buf=Buffer.from(base64,'base64'),digest=crypto.createHash('sha256').update(buf).digest('hex');
   const ref=refManifest.frames.find(x=>x.yawDeg===yaw);
   const ok=!!ref&&ref.sha256===digest;
   match.push({yaw,sha256:digest,expected:ref?.sha256,equivalent:ok});
   fs.writeFileSync(path.join(output,'review-yaw'+yaw+'.png'),buf);
  }
  details.pixelParity=match;
  checks.yaw45PixelParity=match[0].equivalent;
  checks.yaw67PixelParity=match[1].equivalent;
  checks.yaw90PixelParity=match[2].equivalent;
  await page.screenshot({path:path.join(output,'offline-review-67.png'),fullPage:true});
  checks.zeroExternalNetwork=network.length===0;
  checks.zeroBrowserExceptions=browserErrors.length===0;
  checks.logoAndPartSourceVisible=await page.locator('#proxy').textContent().then(x=>x.includes('PMX'));
 }catch(e){details.exception=e.stack||String(e);}
 finally{await browser.close();}
 const qa={schema:'R1999-C06-OFFLINE-SEMANTIC-HTML-QA-V1',file:path.basename(file),
  checks,details,errors:browserErrors,network,sourceRole:'third_party_3d_proxy',
  status:Object.keys(checks).length===11&&Object.values(checks).every(Boolean)&&!details.exception?
   'PASS_OFFLINE_SEMANTIC_HTML':'FAIL'};
 fs.writeFileSync(path.join(output,'offline-semantic-qa.json'),JSON.stringify(qa,null,2)+'\n');
 console.log('R1999_OFFLINE_HTML_QA',JSON.stringify({status:qa.status,checks,errors:qa.errors,network:qa.network,exception:details.exception}).slice(0,5000));
 if(qa.status!=='PASS_OFFLINE_SEMANTIC_HTML')process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
