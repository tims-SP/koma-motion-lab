#!/usr/bin/env node
// Enforce provenance and completeness gates for multi-view source artwork.
const fs=require('node:fs'),path=require('node:path');
const defaultRegistry=path.resolve(__dirname,'../evidence/c04-view-source-registry.json');
const registry=JSON.parse(fs.readFileSync(process.env.R1999_VIEW_REGISTRY||defaultRegistry,'utf8'));
function audit(r){
 const errors=[],statuses=[];
 if(r.schema!=='R1999-C04-VIEW-SOURCE-REGISTRY-V1')errors.push('SCHEMA');
 const angles=new Set();
 for(const key of r.keys){
  if(angles.has(key.yawDeg))errors.push('DUPLICATE_YAW_'+key.yawDeg);
  angles.add(key.yawDeg);
  if(key.availability==='available'&&key.role==='independent_art'){
   if(!key.provenanceFile||!key.sha256||!key.transparentAlpha||!key.landmarks)
     errors.push('INDEPENDENT_ART_INCOMPLETE_'+key.yawDeg);
   else statuses.push({yaw:key.yawDeg,truth:true});
  } else if(key.independentVisualTruth===true)errors.push('FALSE_TRUTH_'+key.yawDeg);
  else statuses.push({yaw:key.yawDeg,truth:false});
 }
 if(![0,45,90].every(x=>angles.has(x)))errors.push('REQUIRED_KEY');
 if(r.partIdentity.verifiedLinkedDrawables!==263)errors.push('NATIVE_DRAWABLE_COUNT');
 if(r.holdoutAngles.some(x=>x.availability==='available' && !x.provenanceFile))errors.push('HELDOUT_WITHOUT_REFERENCE');
 const authorshipPassed=[45,90].every(angle=>statuses.some(s=>s.yaw===angle&&s.truth));
 const heldoutsPassed=r.holdoutAngles.every(x=>x.availability==='available'&&x.provenanceFile&&x.sha256);
 return {errors,statuses,registrationValid:errors.length===0,
  readyForVddVisualAcceptance:errors.length===0&&authorshipPassed&&heldoutsPassed,
  missingAuthoredAngles:[45,90].filter(x=>!statuses.some(s=>s.yaw===x&&s.truth)),
  missingHeldoutAngles:r.holdoutAngles.filter(x=>x.availability!=='available').map(x=>x.yawDeg)};
}
const result=audit(registry);
const injected=JSON.parse(JSON.stringify(registry));
injected.keys.find(x=>x.yawDeg===90).availability='available';
injected.keys.find(x=>x.yawDeg===90).independentVisualTruth=true;
const negative=audit(injected);
const report={
 schema:'R1999-C04-SOURCE-GATE-QA-V1',
 registryPath:'experiments/r1999-cubism-vdd/evidence/c04-view-source-registry.json',
 ...result,
 falseSourceDeclarationRejected:negative.errors.includes('INDEPENDENT_ART_INCOMPLETE_90'),
 status:result.registrationValid&&negative.errors.length>0?'PASS_SOURCE_REGISTRATION':'FAIL',
 nextAction:'Add genuine per-part RGBA 45 and 90 degree artwork with provenance, landmarks, masks, and independent heldouts.'
};
const output=process.env.R1999_C04_QA_REPORT||'out/r1999-c04/source-gate-qa.json';
fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log('C04_SOURCE_GATE',JSON.stringify(report));
if(report.status!=='PASS_SOURCE_REGISTRATION')process.exitCode=1;
