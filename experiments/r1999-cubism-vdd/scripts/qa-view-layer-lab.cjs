#!/usr/bin/env node
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.R1999_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const url=process.env.R1999_URL||'http://127.0.0.1:5181';
 const dir=process.env.R1999_QA_DIR||'out/r1999-view-layer-lab';
 fs.mkdirSync(dir,{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1366,height:900}});
 const errors=[],bad=[],external=[];
 page.on('pageerror',e=>errors.push(e.stack||String(e)));
 page.on('response',r=>{if(r.status()>=400)bad.push(r.url())});
 page.on('request',r=>{if(!r.url().startsWith(url+'/'))external.push(r.url())});
 const checks={},details={};
 try{
  await page.goto(url+'/view-layer-lab.html');
  await page.waitForFunction(()=>window.__R1999_LAYER_LAB?.inspect());
  const initial=await page.evaluate(()=>window.__R1999_LAYER_LAB.inspect());
  checks.initialEmpty=initial.keys45===0&&initial.keys90===0&&initial.paired===0;
  checks.initialGateClosed=initial.visualAcceptance==='AWAITING_VALIDATED_INDEPENDENT_ART';
  await page.waitForFunction(()=>document.getElementById('geometryHint').textContent.includes('45°'),null,{timeout:12000});
  const captureGeometry=()=>page.evaluate(()=>{
    const ctx=document.getElementById('geometryRef').getContext('2d',{willReadFrequently:true});
    const rgba=ctx.getImageData(0,0,640,640).data;
    let pixels=0,red=0;
    for(let i=0;i<rgba.length;i+=4)if(rgba[i+3]>16){pixels++;red+=rgba[i];}
    return {pixels,red,label:document.getElementById('geometryHint').textContent};
  });
  const geometry45=await captureGeometry();
  checks.structural45ReferenceLoaded=geometry45.pixels>10000 && geometry45.label.includes('45°');
  checks.creatorCreditVisible=await page.locator('aside').innerText().then(x=>x.includes('WTHN_Ross')&&x.includes('BLUEPOCH'));
  await page.waitForFunction(()=>document.getElementById('nativeHint').textContent.includes('PARTS_01_HAIR_BACK_001'),null,{timeout:12000});
  const nativeAlpha=await page.evaluate(()=>{
    const c=document.getElementById('nativeRef'),d=c.getContext('2d',{willReadFrequently:true}).getImageData(0,0,640,640).data;
    let pixels=0;for(let i=3;i<d.length;i+=4)if(d[i]>0)pixels++;
    return pixels;
  });
  checks.realNativePartRefLoaded=nativeAlpha>100;
  await page.locator('#part').selectOption('nose');
  await page.waitForFunction(()=>document.getElementById('nativeHint').textContent.includes('PARTS_01_NOSE_001'),null,{timeout:12000});
  checks.nativeSemanticPartSwitch=await page.locator('#nativeHint').textContent().then(x=>x.includes('Drawables'));
  await page.locator('#part').selectOption('hair.back');
  await page.locator('#fixture').click();
  const fixture=await page.evaluate(()=>window.__R1999_LAYER_LAB.inspect());
  checks.fixture16=fixture.keys45===8&&fixture.keys90===8&&fixture.synthetic===16&&fixture.paired===8;
  checks.fixtureGateClosed=fixture.visualAcceptance==='AWAITING_VALIDATED_INDEPENDENT_ART';
  let hashes=[];
  for(const yaw of [45,50,55,60,67,75,82,90]){
   await page.locator('#yaw').evaluate((el,y)=>{el.value=String(y);el.dispatchEvent(new Event('input',{bubbles:true}));},yaw);
   await page.waitForTimeout(55);
   const data=await page.evaluate(()=>{
    const d=document.getElementById('center').getContext('2d').getImageData(0,0,640,640).data;
    let total=0,sum=0;
    for(let i=0;i<d.length;i+=4){if(d[i+3]>0){total++;sum+=d[i];}}
    return {angle:window.__R1999_LAYER_LAB.inspect().angle,total,redChecksum:sum};
   });
   hashes.push(data);
  }
  checks.allAnglesInteractive=hashes.every(x=>x.angle>=45&&x.angle<=90&&x.total>1000);
  checks.interpolationChangesWithYaw=new Set(hashes.map(x=>x.redChecksum)).size>=5;
  details.angleMetrics=hashes;
  const geometry90=await captureGeometry();
  checks.structural90ReferenceLoaded=geometry90.pixels>10000 && geometry90.label.includes('90°');
  checks.cameraViewReferenceChanges=Math.abs(geometry90.red-geometry45.red)>10000;
  details.geometry45=geometry45;
  details.geometry90=geometry90;
  await page.screenshot({path:path.join(dir,'view-layer-lab-fixture.png'),fullPage:true});
  // Import one PNG with RGBA and transparent margins through a true browser file input.
  const png=await page.evaluate(()=>{
   const c=document.createElement('canvas');c.width=c.height=640;
   const ctx=c.getContext('2d');ctx.fillStyle='#eb986b';
   ctx.beginPath();ctx.ellipse(315,255,34,50,0,0,Math.PI*2);ctx.fill();
   return c.toDataURL('image/png').split(',')[1];
  });
  await page.locator('#view').selectOption('45');
  await page.locator('#part').selectOption('nose');
  await page.locator('#sourceId').fill('QA-browser-local-test');
  await page.locator('#artFile').setInputFiles({name:'nose.png',mimeType:'image/png',buffer:Buffer.from(png,'base64')});
  await page.locator('#import').click();
  await page.waitForFunction(()=>window.__R1999_LAYER_LAB.inspect().candidate===1,null,{timeout:12000});
  const after=await page.evaluate(()=>window.__R1999_LAYER_LAB.inspect());
  checks.browserLocalFileImport=after.candidate===1&&after.synthetic===15;
  checks.importGateClosed=after.visualAcceptance==='AWAITING_VALIDATED_INDEPENDENT_ART';
  const registry=await page.evaluate(()=>window.__R1999_LAYER_LAB.exportRegistry());
  checks.exportTracksCandidate=registry.records.length===16&&registry.records.some(r=>r.sourceId==='QA-browser-local-test'&&r.sha256?.length===64);
  // Real RGB/RGBA pixels from a licensed 3D PMX are a separate source role:
  // rendered proxy keys may exercise interpolation, never independent-art gate.
  await page.locator('#proxy').click();
  await page.waitForFunction(()=>window.__R1999_LAYER_LAB.inspect().proxy===16,null,{timeout:25000});
  const proxy=await page.evaluate(()=>window.__R1999_LAYER_LAB.inspect());
  checks.pmxProxy16=proxy.proxy===16&&proxy.synthetic===0&&proxy.candidate===0;
  checks.pmxSemanticPairs=proxy.paired===8&&proxy.keys45===8&&proxy.keys90===8;
  checks.pmxIndependentGateClosed=proxy.visualAcceptance==='AWAITING_VALIDATED_INDEPENDENT_ART';
  const proxyRecords=await page.evaluate(()=>window.__R1999_LAYER_LAB.exportRegistry());
  checks.pmxShaAndProvenance=proxyRecords.records.length===16&&proxyRecords.records.every(
    r=>r.role==='third_party_3d_proxy'&&r.sha256?.length===64&&r.sourceId==='WTHN_Ross_Sonetto_PMX_v1.1');
  const realAngles=[];
  for(const degree of [45,67,90]){
   await page.locator('#yaw').evaluate((el,y)=>{
    el.value=String(y);el.dispatchEvent(new Event('input',{bubbles:true}));
   },degree);
   await page.waitForTimeout(70);
   realAngles.push(await page.evaluate(()=>{
    const canvas=document.getElementById('center');
    const data=canvas.getContext('2d',{willReadFrequently:true}).getImageData(0,0,640,640).data;
    let alphaPixels=0,redSum=0,greenSum=0;
    for(let i=0;i<data.length;i+=4){
     if(data[i+3]>0){alphaPixels++;redSum+=data[i];greenSum+=data[i+1];}
    }
    return {yaw:window.__R1999_LAYER_LAB.inspect().angle,alphaPixels,redSum,greenSum};
   }));
   await page.screenshot({path:path.join(dir,'view-layer-lab-pmx-'+degree+'.png'),fullPage:true});
  }
  checks.pmxActualRenderedPixels=realAngles[0].alphaPixels>30000&&realAngles[2].alphaPixels>25000;
  checks.pmxInterpolatedYawChanges=new Set(realAngles.map(x=>x.redSum)).size===3 &&
   new Set(realAngles.map(x=>x.alphaPixels)).size===3;
  details.pmxSemanticPreview={role:'third_party_3d_proxy',independent2DArtCount:0,angles:realAngles};

  checks.noUnexpectedNetwork=external.length===0;
  checks.noBrowserErrors=errors.length===0;
  checks.noFailedResources=bad.length===0;
  details.initial=initial;details.fixture=fixture;details.afterImport=after;
  details.registryRoles=registry.records.reduce((o,x)=>(o[x.role]=(o[x.role]||0)+1,o),{});
 }catch(e){details.exception=e.stack||String(e);}
 finally {await browser.close();}
 const report={schema:'R1999-VIEW-LAYER-HTML-QA-V1',mode:'PMX_RGB_SEMANTIC_PROXY_AND_SYNTHETIC_FIXTURE',
  visualGate:'AWAITING_AUTHORED_ART',
  checks,details,errors,bad,external,
  status:Object.keys(checks).length===24&&Object.values(checks).every(Boolean)&&!details.exception?'PASS_VIEW_LAYER_HTML_ENGINEERING':'FAIL'};
 fs.writeFileSync(path.join(dir,'view-layer-qa.json'),JSON.stringify(report,null,2)+'\n');
 console.log('VIEW_LAYER_HTML_QA',JSON.stringify({status:report.status,checks,exception:details.exception,errors,external}).slice(0,6500));
 if(report.status!=='PASS_VIEW_LAYER_HTML_ENGINEERING')process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
