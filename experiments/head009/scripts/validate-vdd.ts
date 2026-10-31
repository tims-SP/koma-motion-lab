import {parts,type Point} from '../src/art';
import {correctionControls,applyOrganVdd} from '../src/view-vdd';
const problems:string[]=[];
const ids=new Set(parts.map(p=>p.id));
for(const c of correctionControls){
 if(!ids.has(c.part))problems.push('orphan_part:'+c.label);
 if(![0,45,90].includes(c.interval[0])||![0,45,90].includes(c.interval[1])||c.interval[0]>=c.interval[1])
  problems.push('invalid_support:'+c.label);
 if([...c.centerSvg,...c.radiusSvg,...c.offsetSvg].some(n=>!Number.isFinite(n)))problems.push('nonfinite:'+c.label);
 if(c.radiusSvg.some(n=>n<=0))problems.push('bad_radius:'+c.label);
 if(Math.hypot(...c.offsetSvg)>32)problems.push('too_large:'+c.label);
}
const sample:Point=[.22,-.49];
for(const c of correctionControls){
 for(const yaw of [0,45,90]){
  const p=applyOrganVdd(c.part,sample,yaw);
  if(Math.hypot(p[0]-sample[0],p[1]-sample[1])>1e-10)problems.push('key_not_preserved:'+c.label+':'+yaw);
 }
}
const chin=correctionControls.find(c=>c.label.startsWith('cheek-jaw'));
const tip=correctionControls.find(c=>c.label.startsWith('nasal silhouette'));
if(!chin||!tip)problems.push('mandatory_organs_missing');
const original=applyOrganVdd('face',[.1,-.5],22.5);
if(Math.abs(original[0]-.1)<1e-5)problems.push('no_vdd_effect');
const report={schema:'HEAD009-VDD-CONTROLS-V1',numberOfControls:correctionControls.length,failed:problems,status:problems.length?'FAIL':'PASS_CONTROL_STRUCTURE'};
console.log('HEAD009_VDD_CONTROLS '+JSON.stringify(report));if(problems.length)process.exitCode=1;
