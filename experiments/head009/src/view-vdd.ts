import type {Id,Point} from './art';
// Artist-controlled, source-key-space shape corrections, not a fit to test frames.
// 0°, 45°, 90° authored paintings are immutable. The eye identity/occlusion transition
// is handled by source registration and controlled topology, not these spatial warps.
type Control={part:Id;label:string;interval:[number,number];centerSvg:Point;radiusSvg:Point;offsetSvg:Point};
export const correctionControls:readonly Control[]=[
 {part:'face',label:'cheek-jaw silhouette ease',interval:[0,45],centerSvg:[276,388],radiusSvg:[84,61],offsetSvg:[-24,-1]},
 {part:'face',label:'nasal silhouette projection ease',interval:[0,45],centerSvg:[348,286],radiusSvg:[65,80],offsetSvg:[19,-2]},
 {part:'nose',label:'nasal ink projection',interval:[0,45],centerSvg:[326,281],radiusSvg:[95,92],offsetSvg:[11,-2]},
 {part:'mouth',label:'near-profile mouth alignment',interval:[45,90],centerSvg:[344,330],radiusSvg:[85,65],offsetSvg:[-8,0]}
];
export const worldToSvg=(p:Point):Point=>[(p[0]/2.7+0.5)*512,(0.5-p[1]/2.7)*512];
export function applyOrganVdd(part:Id,p:Point,yaw:number):Point {
 const [x,y]=worldToSvg(p);
 let dx=0,dy=0;
 for(const c of correctionControls){
  if(c.part!==part||yaw<=c.interval[0]||yaw>=c.interval[1])continue;
  const phase=Math.sin(Math.PI*(yaw-c.interval[0])/(c.interval[1]-c.interval[0]));
  const sx=(x-c.centerSvg[0])/c.radiusSvg[0],sy=(y-c.centerSvg[1])/c.radiusSvg[1];
  const radius=Math.exp(-0.5*(sx*sx+sy*sy));
  const weight=phase*radius;
  dx+=c.offsetSvg[0]*weight;dy+=c.offsetSvg[1]*weight;
 }
 return [p[0]+dx*2.7/512,p[1]-dy*2.7/512];
}
