#!/usr/bin/env node
/* Inspect a running Cubism Web model without exporting proprietary mesh geometry. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.R1999_PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const url = process.env.R1999_URL || 'http://127.0.0.1:5176';
  const dir = process.env.R1999_QA_DIR || path.resolve('out/r1999-drawables');
  fs.mkdirSync(dir, {recursive:true});
  const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
  const page=await browser.newPage({viewport:{width:1366,height:900}});
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  const readFrame=async () => page.evaluate(async () => {
    const model=window.__R1999_MODEL?.getModel?.();
    if(!model) throw Error('Cubism model missing');
    const drawableCount=model.getDrawableCount(),parameterCount=model.getParameterCount();
    const maskCounts=model.getDrawableMaskCounts(),masks=model.getDrawableMasks();
    const renderOrders=model.getDrawableRenderOrders(),records=[];
    const encoder=new TextEncoder();
    const hex=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(v=>v.toString(16).padStart(2,'0')).join('');
    const failures=[];
    let totalTriangles=0,totalVertices=0,maskedDrawables=0,opacityErrors=0,invalidVertices=0,invalidIndices=0;
    const textureCounts={},blendModes={},visibleCount={true:0,false:0};
    for(let i=0;i<drawableCount;i++){
      const v=model.getDrawableVertexPositions(i),uv=model.getDrawableVertexUvs(i),idx=model.getDrawableVertexIndices(i);
      const vertexCount=model.getDrawableVertexCount(i),indexCount=model.getDrawableVertexIndexCount(i);
      if(v.length!==vertexCount*2 || uv.length!==vertexCount*2 || idx.length!==indexCount) failures.push('length:'+i);
      if(indexCount%3!==0) failures.push('not_triangles:'+i);
      for(const coord of v) if(!Number.isFinite(coord)) invalidVertices++;
      for(const coord of uv) if(!Number.isFinite(coord)) invalidVertices++;
      for(const triangleIndex of idx) if(triangleIndex>=vertexCount || triangleIndex<0) invalidIndices++;
      const texture=model.getDrawableTextureIndex(i),blend=model.getDrawableBlendMode(i);
      textureCounts[texture]=(textureCounts[texture]??0)+1;
      blendModes[blend]=(blendModes[blend]??0)+1;
      const opacity=model.getDrawableOpacity(i);
      // Cubism uses float32: tolerate a single ULP at unit opacity (e.g. 1.000000119).\n      if(opacity< -1e-5 || opacity>1+1e-5 || !Number.isFinite(opacity))opacityErrors++;
      const nc=maskCounts[i];
      maskedDrawables+=nc>0?1:0;
      for(let j=0;j<nc;j++) if(masks[i][j]<0||masks[i][j]>=drawableCount)failures.push('bad_mask:'+i);
      const visible=model.getDrawableDynamicFlagIsVisible(i);
      visibleCount[String(visible)]++;
      totalVertices+=vertexCount;totalTriangles+=indexCount/3;
      const vertexHash=await hex(v.buffer.slice(v.byteOffset,v.byteOffset+v.byteLength));
      const uvHash=await hex(uv.buffer.slice(uv.byteOffset,uv.byteOffset+uv.byteLength));
      const indexHash=await hex(idx.buffer.slice(idx.byteOffset,idx.byteOffset+idx.byteLength));
      records.push({index:i,drawableId:model.getDrawableId(i).getString(),
        parentPartIndex:model.getDrawableParentPartIndex(i),
        texture,vertexCount,indexCount,maskCount:nc,blend,
        renderOrder:renderOrders[i],invertedMask:model.getDrawableInvertedMaskBit(i),
        opacity:Number(opacity.toFixed(6)),visible,
        vertexHash,uvHash,indexHash});
    }
    const params=[];
    let invalidParams=0;
    for(let i=0;i<parameterCount;i++){
      const low=model.getParameterMinimumValue(i), high=model.getParameterMaximumValue(i);
      const def=model.getParameterDefaultValue(i),value=model.getParameterValueByIndex(i);
      if([low,high,def,value].some(v=>!Number.isFinite(v))||high<low)invalidParams++;
      params.push({id:model.getParameterId(i).getString(),value:+value.toFixed(6),
        min:low,max:high,default:def});
    }
    const metadataHash=await hex(encoder.encode(JSON.stringify(records.map(({vertexHash,uvHash,indexHash,...r})=>r))));
    return {drawableCount,parameterCount,partCount:model.getPartCount(),totalVertices,totalTriangles,
      maskedDrawables,textureCounts,blendModes,visibleCount,invalidVertices,invalidIndices,invalidParams,
      opacityErrors,failures,metadataHash,records,params};
  });
  const report={schema:'R1999-CUBISM-DRAWABLE-AUDIT-V1',environment:'Cubism Web 5-r.4 and browser WebGL2',sourceData:'private model, public aggregate only'};
  try{
    await page.goto(url,{waitUntil:'load'});
    await page.waitForFunction(()=>window.__R1999_REVIEW?.getState()?.ready===true,null,{timeout:30000});
    await page.waitForTimeout(2000);
    const a=await readFrame();
    await page.locator('[data-motion="b_diantou"]').click();
    await page.waitForTimeout(900);
    const b=await readFrame();
    await page.locator('[data-motion="b_yaotou"]').click();
    await page.waitForTimeout(900);
    const c=await readFrame();
    const changed=(before,after,key)=>before.records.reduce((n,x,i)=>n+(x[key]!==after.records[i][key]?1:0),0);
    const parameterChanged=(before,after)=>before.params.reduce((n,p,i)=>n+(Math.abs(p.value-after.params[i].value)>1e-5?1:0),0);
    const stableUvs=a.records.every((x,i)=>x.uvHash===b.records[i].uvHash && x.uvHash===c.records[i].uvHash);
    const stableIndices=a.records.every((x,i)=>x.indexHash===b.records[i].indexHash && x.indexHash===c.records[i].indexHash);
    report.frames={
      baseline:{metadataHash:a.metadataHash,visibleCount:a.visibleCount},
      nod:{metadataHash:b.metadataHash,visibleCount:b.visibleCount},
      shake:{metadataHash:c.metadataHash,visibleCount:c.visibleCount}
    };
    report.structure=Object.fromEntries(['drawableCount','parameterCount','partCount','totalVertices','totalTriangles','maskedDrawables','textureCounts','blendModes','invalidVertices','invalidIndices','invalidParams','opacityErrors','failures'].map(k=>[k,a[k]]));
    report.dynamics={
      nodChangedVertexMeshes:changed(a,b,'vertexHash'),
      shakeChangedVertexMeshes:changed(a,c,'vertexHash'),
      nodChangedParameters:parameterChanged(a,b),
      shakeChangedParameters:parameterChanged(a,c),
      uvHashesStableAcrossFrames:stableUvs,
      triangleIndicesStableAcrossFrames:stableIndices,
      baselineVertexHashPreview:a.records.slice(0,3).map(x=>x.vertexHash)
    };
    report.validation={
      geometryLengthsValid:[a,b,c].every(x=>x.failures.length===0),
      allIndicesAndCoordinatesValid:[a,b,c].every(x=>x.invalidVertices===0&&x.invalidIndices===0),
      allParameterRangesValid:[a,b,c].every(x=>x.invalidParams===0),
      allOpacityValuesValid:[a,b,c].every(x=>x.opacityErrors===0),
      meshChangesUnderMotion:report.dynamics.nodChangedVertexMeshes>0 && report.dynamics.shakeChangedVertexMeshes>0,
      stableTopology:stableUvs&&stableIndices,
      maskReferencesExist:a.maskedDrawables>0,
      browserErrorsAbsent:errors.length===0
    };
    report.status=Object.values(report.validation).every(Boolean)?'PASS_DRAWABLE_ENGINEERING':'FAIL';
  }catch(e){report.status='FAIL';report.exception=String(e)}
  finally{report.browserErrors=errors;await browser.close();}
  fs.writeFileSync(path.join(dir,'drawable-qa.json'),JSON.stringify(report,null,2)+'\n');
  console.log('R1999_DRAWABLE_QA',JSON.stringify(report));
  if(report.status!=='PASS_DRAWABLE_ENGINEERING')process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
