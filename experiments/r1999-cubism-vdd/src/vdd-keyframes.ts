/** Semantic, topology-aware interpolation for independently authored cartoon view keys. */
export type Vec2 = readonly [number,number];
export type Vec3 = readonly [number,number,number];
export type ReferenceRole = 'independent_art' | 'runtime_sample' | 'synthetic_fixture';
export interface PartViewKey {
  yawDeg:number;
  semanticId:string;
  vertexIds:readonly string[];
  xy:readonly Vec2[];
  anchorXYZ:Vec3;
  opacity:number;
  role:ReferenceRole;
  topologyId:string;
}
export interface ViewResult {
  yawDeg:number;
  semanticId:string;
  xy:Vec2[];
  anchorXYZ:Vec3;
  opacity:number;
  sourceKeys:[number,number];
  blend:number;
  trueViewSupport:boolean;
}
const finite=(n:number)=>Number.isFinite(n);
const clamp=(x:number,a=0,b=1)=>Math.min(b,Math.max(a,x));
export const smoothstep=(t:number)=>{const q=clamp(t);return q*q*(3-2*q);};
function validate(k:PartViewKey):void{
 if(!finite(k.yawDeg)||!finite(k.opacity)||k.opacity<0||k.opacity>1)throw Error('Invalid view metadata');
 if(!k.semanticId||!k.topologyId||k.vertexIds.length<3||k.xy.length!==k.vertexIds.length)throw Error('Invalid part topology');
 if(new Set(k.vertexIds).size!==k.vertexIds.length)throw Error('Duplicate landmark IDs');
 if(!k.anchorXYZ.every(finite)||k.xy.some(p=>p.length!==2||!p.every(finite)))throw Error('Nonfinite view data');
}
export function interpolateViews(keys:readonly PartViewKey[],yawDeg:number):ViewResult{
 if(!finite(yawDeg)||keys.length<2)throw Error('Two views and a finite yaw are required');
 keys.forEach(validate);
 const sorted=[...keys].sort((a,b)=>a.yawDeg-b.yawDeg);
 const first=sorted[0],last=sorted.at(-1)!;
 if(yawDeg<first.yawDeg||yawDeg>last.yawDeg)throw Error('Yaw outside authored range');
 if(sorted.some((k,i)=>i&&k.yawDeg===sorted[i-1].yawDeg))throw Error('Duplicate view angles');
 const i=Math.min(sorted.length-2,Math.max(0,sorted.findIndex(k=>k.yawDeg>yawDeg)-1));
 const a=sorted[i],b=sorted[i+1],t=smoothstep((yawDeg-a.yawDeg)/(b.yawDeg-a.yawDeg));
 if(a.semanticId!==b.semanticId||a.topologyId!==b.topologyId||
    a.vertexIds.length!==b.vertexIds.length||a.vertexIds.some((x,j)=>x!==b.vertexIds[j]))
    throw Error('Topology mismatch: requires explicit split/merge or visibility keys');
 const lerp=(u:number,v:number)=>u+(v-u)*t;
 return {yawDeg,semanticId:a.semanticId,
  xy:a.xy.map((p,j)=>[lerp(p[0],b.xy[j][0]),lerp(p[1],b.xy[j][1])] as Vec2),
  anchorXYZ:a.anchorXYZ.map((v,j)=>lerp(v,b.anchorXYZ[j])) as unknown as Vec3,
  opacity:lerp(a.opacity,b.opacity),sourceKeys:[a.yawDeg,b.yawDeg],blend:t,
  trueViewSupport:a.role==='independent_art'&&b.role==='independent_art'};
}
export function authoredCoverage(keys:readonly PartViewKey[],requiredAngles:readonly number[]){
 const authored=new Set(keys.filter(k=>k.role==='independent_art').map(k=>k.yawDeg));
 return {required:[...requiredAngles],verified:requiredAngles.filter(x=>authored.has(x)),
  missing:requiredAngles.filter(x=>!authored.has(x)),complete:requiredAngles.every(x=>authored.has(x))};
}
/**
 * Geometric reference projection for the native Cubism front ArtMesh.
 * This is a diagnostic proxy, not a replacement for real side or rear key artwork.
 */
export function projectHeadProxy(x:number,y:number,source:Vec3,pivot:Vec2,yawDeg:number,influence=1):Vec2 {
 if(![x,y,...source,...pivot,yawDeg,influence].every(finite))throw Error('Nonfinite projection');
 if(yawDeg===0||influence===0)return [x,y];
 const theta=yawDeg*Math.PI/180;
 return [x + influence*((pivot[0]+(x-pivot[0])*Math.cos(theta)+source[2]*Math.sin(theta))-x),y];
}
