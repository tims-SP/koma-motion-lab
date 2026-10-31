import {parts,between,type Point,type Id} from './art';
import {applyOrganVdd} from './view-vdd';
export type ViewRole='key'|'heldout';
export interface OrganLandmarks {
 schema:string;units:'SVG512';keyAngles:number[];heldOutAngles:number[];
 organParts:Record<string,Id>;required:string[];
 views:{yaw:number;source:string;role:ViewRole;points:Record<string,Point>;occludedLandmarks?:string[]}[];
}
export const svgToWorld=([x,y]:Point):Point=>[(x-256)*2.7/512,(256-y)*2.7/512];
export const worldToCanvas=([x,y]:Point):Point=>[(x/2.7+.5)*640,(.5-y/2.7)*640];
const lerp=(x:number,y:number,t:number)=>x+(y-x)*t;
const angles=[0,45,90] as const;
const anchors=new Map(parts.map(p=>[p.id,p.anchor]));
export function predictViewLandmarks(register:OrganLandmarks,yaw:number){
 const {a,b,t}=between(yaw),out:Record<string,Point>={};
 const keyViews=angles.map(angle=>register.views.find(v=>v.yaw===angle));
 if(keyViews.some(x=>!x))throw Error('missing key source annotation');
 for(const [semantic,part] of Object.entries(register.organParts)){
  const A=keyViews[a]!.points[semantic],B=keyViews[b]!.points[semantic];
  // A temporarily absent organ is explicitly absent; we do not morph into another organ.
  if(!A||!B)continue;
  const anchor=anchors.get(part);
  if(!anchor)throw Error('missing part: '+part);
  const getPos=(angle:number):Point=>{
   const r=angle*Math.PI/180;
   return [anchor[0]*Math.cos(r)+anchor[2]*Math.sin(r),anchor[1]];
  };
  const ca=getPos(angles[a]),cb=getPos(angles[b]),pos=getPos(yaw);
  const pa=svgToWorld(A),pb=svgToWorld(B);
  out[semantic]=worldToCanvas(applyOrganVdd(part,[
   lerp(pa[0]-ca[0],pb[0]-cb[0],t)+pos[0],
   lerp(pa[1]-ca[1],pb[1]-cb[1],t)+pos[1]
  ],yaw));
 }
 return out;
}
export function compareViewLandmarks(register:OrganLandmarks,yaw:number,deltaPixels=0){
 const view=register.views.find(x=>x.yaw===yaw);
 if(!view)throw Error('missing independent reference at '+yaw);
 const predicted=predictViewLandmarks(register,yaw);
 const diffs:Record<string,{reference:Point;predicted:Point;errorPx:number;status:string}>={};
 for(const [semantic,point] of Object.entries(view.points)){
  const p=predicted[semantic];
  if(!p){diffs[semantic]={reference:[point[0]*1.25,point[1]*1.25],predicted:[-1,-1],errorPx:-1,status:'MISSING_KEY_CORRESPONDENCE'};continue;}
  const ref:Point=[point[0]*1.25,point[1]*1.25],test:Point=[p[0]+(semantic==='nose.tip'?deltaPixels:0),p[1]];
  diffs[semantic]={reference:ref,predicted:test,errorPx:Math.hypot(ref[0]-test[0],ref[1]-test[1]),status:'PROJECTED'};
 }
 const errors=Object.values(diffs).filter(v=>v.errorPx>=0).map(x=>x.errorPx);
 return {yaw,role:view.role,source:view.source,errors:diffs,
  maxErrorPx:errors.length?Math.max(...errors):null,
  meanErrorPx:errors.length?errors.reduce((a,b)=>a+b,0)/errors.length:null,
  missingKeys:Object.values(diffs).filter(x=>x.status==='MISSING_KEY_CORRESPONDENCE').length};
}
