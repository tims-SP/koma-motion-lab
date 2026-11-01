#!/usr/bin/env node
/** Inspect actual Cubism parameter ranges for view-source registration; not 3D yaw coverage. */
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.R1999_PLAYWRIGHT_MODULE || 'playwright');

(async () => {
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage();
 const errors=[];
 page.on('pageerror',e=>errors.push(e.stack||String(e)));
 try{
  const url=process.env.R1999_URL||'http://127.0.0.1:5178';
  await page.goto(url);
  await page.waitForFunction(()=>window.__R1999_MODEL?.getModel?.(),null,{timeout:30000});
  const stats=await page.evaluate(()=>{
   const m=window.__R1999_MODEL.getModel();
   const all=Array.from({length:m.getParameterCount()},(_,i)=>({
     id:m.getParameterId(i).getString().s,
     min:m.getParameterMinimumValue(i),
     max:m.getParameterMaximumValue(i),
     default:m.getParameterDefaultValue(i)
   }));
   const selected=[
    'PARAM_ANGLE_X','PARAM_ANGLE_Y','PARAM_ANGLE_Z',
    'PARAM_BODY_ANGLE_X','PARAM_BODY_ANGLE_Y','PARAM_BODY_ANGLE_Z',
    'PARAM_EYE_L_OPEN','PARAM_EYE_R_OPEN','PARAM_MOUTH_OPEN_Y'
   ].map(id=>all.find(p=>p.id===id)||{id,missing:true});
   return {parameterCount:m.getParameterCount(),drawableCount:m.getDrawableCount(),selected};
  });
  const report={
   schema:'R1999-C04-CUBISM-PARAMETER-COVERAGE-V1',
   upstreamCommit:'45e75248ba3b25053fd32e63ab13c2f9f54dd9df',
   officialSamplesTag:'5-r.4',
   sourceModel:'302301_shisihangshi.moc3',
   sourceViewProvenance:'single exported Cubism model with two texture atlases and parameter-driven ArtMesh',
   interpretativeRule:'Cubism PARAM_ANGLE_X is a 2D rig control and cannot be counted as a physical 45/90/180 degree camera key.',
   runtime:stats,
   independentViewArt:{
    front: 'PARTIAL: source is an existing stylized non-photogrammetric portrait, yaw not calibrated',
    right45:'NOT_PRESENT_IN_CHARACTER_DIRECTORY',
    right90:'NOT_PRESENT_IN_CHARACTER_DIRECTORY',
    back180:'NOT_PRESENT_IN_CHARACTER_DIRECTORY',
    left270:'NOT_PRESENT_IN_CHARACTER_DIRECTORY',
    heldout20_55_82:'NOT_PRESENT_IN_CHARACTER_DIRECTORY'
   },
   sourceGaps:[
    'calibrated camera yaw and multi-view drawing conventions',
    'separately authored right and left face silhouettes, eyes, nose, mouth, ears',
    'front/side/back hair caps, strands and occlusion mask variations',
    'independent backside of clothing and hairstyle for 180-degree view',
    'landmark correspondence and transparent per-part masks',
    'independent holdout art for interpolation assessment'
   ],
   browserErrors:errors,
   status:errors.length===0 && stats.selected.every(p=>!p.missing)?'PASS_PARAMETER_INVENTORY_AND_GAP_AUDIT':'FAIL_PARAMETER_SCAN'
  };
  const dest=process.env.R1999_C04_REPORT||path.resolve('out/r1999-c04/parameter-coverage.json');
  fs.mkdirSync(path.dirname(dest),{recursive:true});
  fs.writeFileSync(dest,JSON.stringify(report,null,2)+'\n');
  console.log('R1999_C04_SCAN',JSON.stringify(report));
  if(report.status.startsWith('FAIL'))process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
