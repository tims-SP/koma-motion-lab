import {parts} from '../src/art';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {join} from 'node:path';
const sourceDir='reference',out='out/head009';
const failures:string[]=[];
const ids=new Set<string>();
const cross=(a:readonly number[],b:readonly number[],c:readonly number[])=>(b[0]!-a[0]!)*(c[1]!-a[1]!)-(b[1]!-a[1]!)*(c[0]!-a[0]!);
for(const part of parts){
 if(ids.has(part.id))failures.push('duplicate_part_id:'+part.id);
 ids.add(part.id);
 const counts=part.keys.map(x=>x.length);
 if(new Set(counts).size!==1)failures.push('semantic_correspondence:'+part.id+':'+counts);
 if(counts.some(n=>n<3))failures.push('degenerate_contour:'+part.id);
 if([...part.anchor,...part.color,...part.depthBias,...part.keys.flat(2)].some(x=>typeof x==='number'&&!Number.isFinite(x)))failures.push('nonfinite:'+part.id);
 for(let k=0;k<3;k++){
  const p=part.keys[k]!;
  for(let i=0;i<p.length;i++)for(let j=i+1;j<p.length;j++){
   if(j===i+1||(i===0&&j===p.length-1))continue;
   const a=p[i]!,b=p[(i+1)%p.length]!,c=p[j]!,d=p[(j+1)%p.length]!;
   if(cross(a,b,c)*cross(a,b,d)<0&&cross(c,d,a)*cross(c,d,b)<0)failures.push('self_intersection:'+part.id+':'+k+':'+i+':'+j);
  }
 }
}
const manifest=JSON.parse(await readFile(join(sourceDir,'manifest.json'),'utf8'));
const all=[...manifest.keys,...manifest.heldOut];
if(all.length!==6)failures.push('source_view_count');
const hashes:Record<string,string>={};
for(const key of all){
 const bytes=await readFile(join(sourceDir,key.path));
 hashes[key.path]=createHash('sha256').update(bytes).digest('hex');
 const svg=bytes.toString('utf8');
 if(!svg.includes('<svg')||!svg.includes('</svg>'))failures.push('invalid_svg:'+key.path);
 if(key.yaw===90&&!svg.includes('data-part-id="ear.near"'))failures.push('profile_missing_ear');
 if(key.yaw===90&&!svg.includes('data-part-id="nose"'))failures.push('profile_missing_nose');
}
if(new Set(Object.values(hashes)).size!==all.length)failures.push('duplicate_reference_art');
await mkdir(out,{recursive:true});
const report={schema:'HEAD009-ASSET-VALIDATION-V1',partCount:parts.length,sourceViewCount:all.length,
 statuses:{keyCorrespondence:failures.filter(x=>x.startsWith('semantic_')).length===0,sourceDistinct:new Set(Object.values(hashes)).size===all.length},
 sourceHashes:hashes,failures,result:failures.length?'FAIL':'PASS_STRUCTURE'};
await writeFile(join(out,'source-hashes.json'),JSON.stringify(report,null,2)+'\n');
console.log('HEAD009_ASSETS '+JSON.stringify(report));
if(failures.length)process.exitCode=1;
