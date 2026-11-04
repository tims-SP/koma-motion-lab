#!/usr/bin/env node
/* Capture actual HTML Canvas2D PMX semantic VDD proxy output at withheld angles. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require(process.env.R1999_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const url=process.env.R1999_URL||'http://127.0.0.1:5186';
 const root=process.env.R1999_OUTPUT_DIR||'out/r1999-pmx-holdout';
 fs.mkdirSync(root,{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1400,height:1000}});
 const errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 const images=[];
 try{
  await page.goto(url+'/view-layer-lab.html',{waitUntil:'load'});
  await page.waitForFunction(()=>window.__R1999_LAYER_LAB?.inspect());
  await page.locator('#proxy').click();
  await page.waitForFunction(()=>window.__R1999_LAYER_LAB.inspect().proxy===16,null,{timeout:20000});
  for(const degree of [45,55,67,82,90]){
   await page.locator('#yaw').evaluate((el,a)=>{
     el.value=String(a);el.dispatchEvent(new Event('input',{bubbles:true}));
   },degree);
   const record=await page.evaluate(()=>{
    const o=window.__R1999_LAYER_LAB.inspect();
    const blob=document.getElementById('center').toDataURL('image/png').split(',')[1];
    return {angle:o.angle,paired:o.paired,roleCount:o.proxy,gate:o.visualAcceptance,blob};
   });
   if(record.angle!==degree || record.paired!==8 || record.roleCount!==16 ||
      record.gate!=='AWAITING_VALIDATED_INDEPENDENT_ART')throw Error('HTML semantic source invalid');
   const bin=Buffer.from(record.blob,'base64');
   const name='predicted-yaw'+String(degree).padStart(3,'0')+'.png';
   fs.writeFileSync(path.join(root,name),bin);
   images.push({yawDeg:degree,filename:name,bytes:bin.length,
     sha256:crypto.createHash('sha256').update(bin).digest('hex'),role:'pmx_proxy_vdd_prediction'});
  }
 }finally{await browser.close();}
 const result={schema:'R1999-PMX-VDD-CANVAS-PREDICTIONS-V1',
   source:'45/90 PMX RGB semantic proxy + Canvas2D two-key deform',
   modelRole:'third_party_3d_proxy',independent2DArtCoverage:0,
   statuses:{browserErrors:errors,geometryKeyPairCount:8},frames:images,
   status:errors.length===0&&images.length===5?'PASS_PMX_PROXY_CANVAS_CAPTURE':'FAIL'};
 fs.writeFileSync(path.join(root,'predictions-manifest.json'),JSON.stringify(result,null,2)+'\n');
 console.log('PREDICTED_PMX_VDD_FRAMES',result.status,images.map(x=>x.yawDeg));
 if(result.status==='FAIL')process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
