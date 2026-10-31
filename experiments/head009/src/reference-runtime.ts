import type {Id,Point} from './art';
export interface SourcePath {
  points:Point[]; closed:boolean; fill:string|null; stroke:string|null; strokeWidth:number;
}
export type Sources=Record<Id,Array<SourcePath|null>>;
const mapping:Record<string,Id>={
 neck:'neck',rearHair:'rearHair',face:'face',fringe:'fringe',sideHair:'sideHair',
 'ear.far':'farEar','ear.near':'nearEar','eye.far':'farEye','eye.near':'nearEye',
 nose:'nose',mouth:'mouth','asym-hair-mark':'ornament','ear-fold':'earFold'
};
const sourceNames=['front-000.svg','threequarter-045.svg','profile-right-090.svg'] as const;
export async function loadReferenceArt():Promise<Sources>{
 const sources={} as Sources;
 for(let keyIndex=0;keyIndex<sourceNames.length;keyIndex++){
  const name=sourceNames[keyIndex];
  const embedded=(window as Window & {__HEAD009_REFS?:Record<string,string>}).__HEAD009_REFS?.[name];
  let text:string;
  if(typeof embedded==='string')text=embedded;
  else{
   const resp=await fetch('/reference/'+name);
   if(!resp.ok)throw Error('cannot fetch authored source: '+name);
   text=await resp.text();
  }
  const doc=new DOMParser().parseFromString(text,'image/svg+xml');
  if(doc.querySelector('parsererror'))throw Error('invalid source SVG');
  const parsed=doc.documentElement;
  // SVG path geometry is sampled by the browser's actual path implementation.
  const attached=document.importNode(parsed,true);
  const container=document.createElement('div');
  container.style.cssText='position:absolute;visibility:hidden;left:-10000px;top:0';
  container.appendChild(attached);document.body.appendChild(container);
  try{
   for(const el of Array.from(attached.querySelectorAll<SVGPathElement>('path[data-part-id]'))){
    const idRaw=el.getAttribute('data-part-id')??'';
    const id=mapping[idRaw];if(!id)throw Error('unregistered anatomy: '+idRaw);
    const length=el.getTotalLength();
    if(!(length>0))throw Error('degenerate SVG path: '+idRaw);
    const d=el.getAttribute('d')??'';
    const closed=/[zZ]\s*$/.test(d);
    const points:Point[]=[];
    const count=96,scale=2.7/512;
    for(let i=0;i<count;i++){
     const sample=el.getPointAtLength(length*(closed?i/count:i/(count-1)));
     points.push([(sample.x-256)*scale,(256-sample.y)*scale]);
    }
    const fill=el.getAttribute('fill');
    const stroke=el.getAttribute('stroke');
    const result:SourcePath={points,closed,
      fill:fill&&fill!=='none'?fill:null,
      stroke:stroke&&stroke!=='none'?stroke:null,
      strokeWidth:Number(el.getAttribute('stroke-width')??'0')*scale};
    sources[id]??=[null,null,null]; // A source path is a per-anatomical-part raster equivalent.
    if(sources[id][keyIndex])throw Error('multiple paths must be decomposed: '+id);
    sources[id][keyIndex]=result;
   }
  }finally{container.remove();}
 }
 return sources;
}
