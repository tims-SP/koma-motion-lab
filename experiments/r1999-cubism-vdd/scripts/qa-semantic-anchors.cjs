#!/usr/bin/env node
// Extract the native Cubism part-to-drawable identity graph and provisional 3D anchors.
// Source artwork is never serialized. XYZ anchors are engineering estimates, not recovered 3D geometry.
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.R1999_PLAYWRIGHT_MODULE || 'playwright');

(async function(){
 const out=process.env.R1999_C04_REPORT||'out/r1999-c04/semantic-anchors.json';
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1400,height:860}});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 try {
  await page.goto(process.env.R1999_URL||'http://127.0.0.1:5179');
  await page.waitForFunction(()=>window.__R1999_MODEL?.getModel?.(),null,{timeout:30000});
  const data=await page.evaluate(()=>{
    const m=window.__R1999_MODEL.getModel(),partCount=m.getPartCount(),drawCount=m.getDrawableCount();
    function family(id){
      if(/EYE_BALL|EYE_001/i.test(id))return 'eyes';
      if(/NOSE/i.test(id))return 'nose';
      if(/MOUTH/i.test(id))return 'mouth';
      if(/BROW/i.test(id))return 'brows';
      if(/EAR/i.test(id))return 'ears';
      if(/HAIR_FRONT/i.test(id))return 'hair.front';
      if(/HAIR_SIDE/i.test(id))return 'hair.side';
      if(/HAIR_BACK|Hair_B_/i.test(id))return 'hair.back';
      if(/Hair_M_/i.test(id))return 'hair.middle';
      if(/FACE/i.test(id))return 'face';
      if(/NECK/i.test(id))return 'neck';
      if(/Leg_|PARTS_01_BODY|Cloak|Part[34569]/i.test(id))return 'body';
      return 'unclassified';
    }
    const depthByFamily={'hair.back':-0.30,'hair.middle':0.09,'hair.side':0.18,'hair.front':0.30,
      'face':0,'eyes':0.18,'nose':0.26,'mouth':0.14,'brows':0.20,'ears':-0.05,'neck':-0.10,
      'body':0,'unclassified':0};
    const arr=[];
    for(let i=0;i<partCount;i++){
      const partId=m.getPartId(i).getString().s,drawables=[];
      let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity,totalVertices=0;
      for(let j=0;j<drawCount;j++){
        if(m.getDrawableParentPartIndex(j)!==i)continue;
        const verts=m.getDrawableVertexPositions(j);
        for(let k=0;k<verts.length;k+=2){
          let x=verts[k],y=verts[k+1];if(!Number.isFinite(x)||!Number.isFinite(y))continue;
          minX=Math.min(x,minX);maxX=Math.max(x,maxX);
          minY=Math.min(y,minY);maxY=Math.max(y,maxY);totalVertices++;
        }
        drawables.push(j);
      }
      const semantic=family(partId);
      arr.push({partIndex:i,partId,semantic,drawables,vertexSamples:totalVertices,
        bbox:drawables.length?[minX,minY,maxX,maxY].map(x=>+x.toFixed(5)):null,
        anchorXYZ:drawables.length?
          [+((minX+maxX)/2).toFixed(5),+((minY+maxY)/2).toFixed(5),depthByFamily[semantic]]:null,
        depthProvenance:'heuristic_visual_proxy'});
    }
    const mapped=arr.reduce((n,p)=>n+p.drawables.length,0);
    const seen=new Set(arr.flatMap(p=>p.drawables));
    const missing=Array.from({length:drawCount},(_,i)=>i).filter(i=>!seen.has(i));
    const face=arr.find(p=>p.semantic==='face'&&p.bbox);
    const headPivot=face?face.anchorXYZ.slice(0,2):null;
    return {parts:arr,counts:{partCount,drawableCount:drawCount,mapped,unmapped:missing.length,unmappedIndices:missing,
       identifiedFaceParts:arr.filter(x=>x.semantic==='face').length,
       classified:arr.filter(x=>x.semantic!=='unclassified'&&x.drawables.length>0).reduce((n,x)=>n+x.drawables.length,0)},
       headPivot,depthUnits:'Cubism model-space heuristic'};
  });
  const actual={
    schema:'R1999-C04-PART-ANCHORS-V1',
    sourceCommit:'45e75248ba3b25053fd32e63ab13c2f9f54dd9df',
    model:'302301_shisihangshi',
    provenance:{partIds:'native_Cubism_Core',positions:'runtime_drawable_vertex_bbox',
      depth:'heuristic_not_measured',yaw:'camera_yaw_independent_from_native_PARAMS'},
    ...data,browserErrors:errors,
    status:data.counts.unmapped===0&&data.counts.partCount===46&&data.counts.drawableCount===263&&
      data.headPivot!==null&&errors.length===0?'PASS_SEMANTIC_RUNTIME_INVENTORY':'FAIL'
  };
  fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(actual,null,2)+'\n');
  console.log('C04_PARTS',JSON.stringify({status:actual.status,counts:actual.counts,
    headPivot:actual.headPivot,semantics:[...new Set(actual.parts.map(x=>x.semantic))],errors}));
  if(actual.status!=='PASS_SEMANTIC_RUNTIME_INVENTORY')process.exitCode=1;
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
