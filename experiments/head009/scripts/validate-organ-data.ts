import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {parts} from '../src/art';
import type {OrganLandmarks} from '../src/organ-register';
const out='out/head009';await mkdir(out,{recursive:true});
const data=JSON.parse(await readFile('reference/organ-landmarks.json','utf8')) as OrganLandmarks;
const manifest=JSON.parse(await readFile('reference/manifest.json','utf8'));
const expected=new Map([...manifest.keys,...manifest.heldOut].map((x:{yaw:number;path:string})=>[x.yaw,x.path]));
const keyAngles=[0,45,90],heldoutAngles=[30,60,75];
const partIds=new Set(parts.map(x=>x.id));
const invalid=(doc:OrganLandmarks):string[]=>{
 const problems:string[]=[];
 const yaws=doc.views.map(x=>x.yaw),n=new Set(yaws);
 if(n.size!==6||n.size!==yaws.length)problems.push('view_count_or_duplicate');
 if([...keyAngles,...heldoutAngles].some(x=>!n.has(x)))problems.push('view_angles');
 const values=Object.keys(doc.organParts);
 if(values.length<9)problems.push('organ_count');
 for(const [semantic,part] of Object.entries(doc.organParts)){
  if(!partIds.has(part))problems.push('orphan_part:'+semantic);
 }
 for(const name of doc.required)if(!(name in doc.organParts))problems.push('missing_organ_definition:'+name);
 for(const v of doc.views){
  const correct=expected.get(v.yaw);
  if(v.source!==correct)problems.push('source_mismatch:'+v.yaw);
  if(v.role!==(keyAngles.includes(v.yaw)?'key':'heldout'))problems.push('role_mismatch:'+v.yaw);
  for(const required of doc.required)if(!v.points[required])problems.push('required_missing:'+v.yaw+':'+required);
  for(const [name,pt] of Object.entries(v.points)){
   if(!(name in doc.organParts))problems.push('unknown_organ:'+name);
   if(!Array.isArray(pt)||pt.length!==2||pt.some(x=>!Number.isFinite(x)||x<0||x>512))problems.push('out_of_bounds:'+v.yaw+':'+name);
  }
  if(v.yaw>=60&&v.points['eye.R.center'])problems.push('far_eye_marked_visible:'+v.yaw);
  if(v.yaw>=60&&!v.points['eye.L.center'])problems.push('persistent_eye_missing:'+v.yaw);
 }
 return problems;
};
const checked=invalid(data);
const altered=structuredClone(data);
altered.views.find(x=>x.yaw===75)!.points['nose.tip']=[600,285];
const faultCoordinate=invalid(altered).some(x=>x.startsWith('out_of_bounds:75:nose.tip'));
const removed=structuredClone(data);
delete removed.views.find(x=>x.yaw===60)!.points['mouth.center'];
const faultMissing=invalid(removed).some(x=>x.startsWith('required_missing:60:mouth.center'));
const report={schema:'HEAD009-ORGAN-SOURCE-VALIDATION-V1',viewCount:data.views.length,organCount:Object.keys(data.organParts).length,
 requiredCount:data.required.length,sourceErrors:checked,
 negativeControls:{badNoseCoordinateCaught:faultCoordinate,missingMouthCaught:faultMissing},
 status:checked.length===0&&faultCoordinate&&faultMissing?'PASS_SOURCE_SCHEMA':'FAIL_SOURCE_SCHEMA'};
await writeFile(join(out,'organ-source-validation.json'),JSON.stringify(report,null,2)+'\n');
console.log('HEAD009_ORGAN_SOURCE '+JSON.stringify(report));
if(report.status!=='PASS_SOURCE_SCHEMA')process.exitCode=1;
