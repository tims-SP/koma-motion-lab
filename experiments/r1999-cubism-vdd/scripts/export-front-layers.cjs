#!/usr/bin/env node
// Export one transparent native Cubism front-view PNG per Part group.
// Asset bytes are written to a private directory; commit only the JSON provenance/QA.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require(process.env.R1999_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const url=process.env.R1999_URL||'http://127.0.0.1:5180';
 const dir=process.env.R1999_LAYER_DIR||'out/r1999-c04/front-layers';
 fs.mkdirSync(dir,{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1400,height:900}});
 const errors=[],badRequests=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 page.on('response',r=>{if(r.status()>=400)badRequests.push(r.status()+' '+r.url())});
 try{
  await page.goto(url,{waitUntil:'load'});
  await page.waitForFunction(()=>window.__R1999_ADAPTER?.inspect()?.drawables===263,null,{timeout:30000});
  await page.waitForTimeout(1500);
  await page.evaluate(()=>{window.__R1999_PAUSED=true;window.__R1999_ADAPTER.setYaw(0)});
  const records=await page.evaluate(()=>{
   const m=window.__R1999_MODEL.getModel();const groups=[];
   for(let partIndex=-1;partIndex<m.getPartCount();partIndex++){
    const ids=Array.from({length:m.getDrawableCount()},(_,i)=>i).filter(j=>m.getDrawableParentPartIndex(j)===partIndex);
    groups.push({partIndex,partId:partIndex===-1?'__UNPARENTED_DRAWABLES__':m.getPartId(partIndex).getString().s,
      drawableCount:ids.length,drawableIndices:ids});
   }
   return groups;
  });
  const entries=[],emptyGroups=[];
  for(const group of records){
   if(group.drawableCount===0){emptyGroups.push(group.partId);continue;}
   const data=await page.evaluate(p=>window.__R1999_ADAPTER.capturePart(p),group.partIndex);
   if(data.provenance!=='CUBISM_NATIVE_FRONT_PART_SNAPSHOT')throw Error('Invalid source role '+group.partId);
   if(!data.dataUrl.startsWith('data:image/png;base64,'))throw Error('Invalid PNG URL');
   const bytes=Buffer.from(data.dataUrl.slice('data:image/png;base64,'.length),'base64');
   if(bytes.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('PNG signature '+group.partId);
   const label=group.partId.replace(/[^A-Za-z0-9_-]/g,'_').slice(0,68);
   const filename=String(group.partIndex).padStart(2,'0')+'_'+label+'.png';
   fs.writeFileSync(path.join(dir,filename),bytes);
   entries.push({partIndex:group.partIndex,partId:group.partId,filename,
     drawableCount:group.drawableCount,drawableIndices:group.drawableIndices,
     semanticHint:group.partIndex===-1?'face.base':null,
     role:'native_runtime_part_snapshot',cameraYawCalibrated:false,
     width:640,height:640,hasAlpha:true,nonzeroAlphaPixels:data.nonzeroAlpha,
     opaquePixels:data.opaquePixels,alphaRange:[data.alphaMin,data.alphaMax],
     sizeBytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});
  }
  const annotated=new Set(entries.flatMap(e=>e.drawableIndices));
  const validation={
   nativeDrawableCoverage:annotated.size===263,
   noDuplicateDrawableOwnership:entries.reduce((n,e)=>n+e.drawableCount,0)===annotated.size,
   assetRoleTruthful:entries.every(e=>e.role==='native_runtime_part_snapshot'&&!e.cameraYawCalibrated),
   alphaBackgroundValid:entries.every(e=>e.nonzeroAlphaPixels<640*640),
   nonzeroFace:entries.some(e=>(e.partId==='PARTS_01_FACE_001'||e.partIndex===-1)&&e.nonzeroAlphaPixels>50),
   nonzeroEyes:entries.some(e=>e.partId==='PARTS_01_EYE_001'&&e.nonzeroAlphaPixels>50),
   browserErrorsAbsent:errors.length===0,badRequestsAbsent:badRequests.length===0
  };
  const report={schema:'R1999-C04-FRONT-LAYER-EXPORT-V1',model:'302301_shisihangshi',
   sourceCommit:'45e75248ba3b25053fd32e63ab13c2f9f54dd9df',
   sourceType:'native_Cubism_CubismWeb_5r4',role:'front_pose_not_new_camera_view',
   privateStorage:true,alphaRGBA:true,canvas:[640,640],
   totalParts:46,unparentedGroups:1,filesWritten:entries.length,emptyGroups,
   visualQA:'Source artwork remains original pose; novel-view art coverage gate is separate.',
   validation,errors,badRequests,entries,
   status:Object.values(validation).every(Boolean)?'PASS_NATIVE_FRONT_LAYER_EXPORT':'FAIL'};
  fs.writeFileSync(path.join(dir,'front-layer-manifest.json'),JSON.stringify(report,null,2)+'\n');
  console.log('C04_LAYER_EXPORT',JSON.stringify({status:report.status,filesWritten:report.filesWritten,emptyGroups:emptyGroups.length,
    drawableCoverage:annotated.size,tests:validation,filesWithNonzeroPixels:entries.filter(e=>e.nonzeroAlphaPixels>0).length,
    face:entries.filter(e=>/FACE_001|NOSE_001|EYE_001|HAIR_FRONT_001/.test(e.partId)).map(e=>({partId:e.partId,pixels:e.nonzeroAlphaPixels}))}));
  if(report.status!=='PASS_NATIVE_FRONT_LAYER_EXPORT')process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
