// Deliberately authored anatomical contours for three independent source views.
// Points are head-local 2D drawing coordinates, NOT a 3D UV skin or squeezed front image.
export type Key = 0 | 45 | 90;
export type Point = readonly [number, number];
export type Id = 'rearHair'|'face'|'nearEar'|'farEar'|'fringe'|'sideHair'|'nearEye'|'farEye'|'nose'|'mouth'|'neck';
export interface Part {
  id:Id; anchor:readonly [number,number,number]; color:readonly [number,number,number];
  depthBias:readonly [number,number,number];
  keys: readonly [readonly Point[],readonly Point[],readonly Point[]];
  visible: readonly [boolean,boolean,boolean];
}
const P=(...coords:number[]):Point[]=>{
  if(coords.length%2)throw Error('odd coordinates');
  const r:Point[]=[];for(let i=0;i<coords.length;i+=2)r.push([coords[i]!,coords[i+1]!]);
  return r;
};
export const parts:readonly Part[]=[
 {id:'neck',anchor:[0,-.66,-.12],color:[.81,.56,.45],depthBias:[0,0,0],visible:[true,true,true],keys:[
 P(-.27,.15,.27,.15,.23,-.35,-.23,-.35),
 P(-.25,.15,.22,.15,.24,-.35,-.16,-.35),
 P(-.17,.14,.21,.14,.16,-.33,-.17,-.33)]},
 {id:'rearHair',anchor:[0,.04,-.37],color:[.16,.23,.38],depthBias:[0,0,0],visible:[true,true,true],keys:[
 P(-.86,.39,-.74,.83,-.40,1.03,.27,1.01,.79,.64,.90,.04,.80,-.69,.49,-.97,-.57,-.90,-.89,-.48),
 P(-.74,.34,-.62,.86,-.35,1.05,.22,1.01,.60,.65,.62,.02,.42,-.79,.01,-1.02,-.49,-.91,-.79,-.46),
 P(-.58,.28,-.54,.82,-.30,1.02,.18,.93,.46,.58,.42,.03,.22,-.78,-.14,-.94,-.47,-.76,-.58,-.36)]},
 {id:'farEar',anchor:[-.56,-.05,-.08],color:[.85,.57,.48],depthBias:[.0,-.1,-.2],visible:[true,true,false],keys:[
 P(-.20,.20,-.05,.28,.13,.10,.14,-.14,-.04,-.31,-.21,-.16),
 P(-.18,.19,-.08,.25,.09,.10,.14,-.14,-.04,-.26,-.18,-.16),
 P(-.12,.15,-.01,.21,.10,.08,.10,-.12,-.03,-.23,-.13,-.15)]},
 {id:'face',anchor:[0,-.06,.18],color:[.98,.76,.64],depthBias:[0,0,0],visible:[true,true,true],keys:[
 P(0,.72,.48,.66,.70,.40,.74,.07,.73,-.12,.69,-.33,.48,-.67,.16,-.82,-.16,-.82,-.49,-.67,-.69,-.33,-.75,.07,-.69,.40,-.47,.65),
 P(-.14,.72,.33,.68,.58,.43,.64,.20,.83,.06,.79,-.05,.69,-.12,.59,-.40,.36,-.70,-.07,-.84,-.40,-.68,-.61,-.29,-.65,.12,-.54,.49),
 P(-.28,.74,.15,.71,.35,.50,.42,.23,.83,.08,.86,-.02,.62,-.13,.68,-.24,.57,-.42,.23,-.69,-.10,-.79,-.43,-.52,-.55,.18,-.52,.51)]},
 {id:'nearEar',anchor:[.58,-.03,-.02],color:[.93,.64,.53],depthBias:[.08,.10,.14],visible:[true,true,true],keys:[
 P(-.12,.26,.07,.28,.23,.07,.18,-.15,.01,-.33,-.13,-.15),
 P(-.20,.23,-.03,.30,.15,.10,.14,-.12,-.03,-.33,-.19,-.13),
 P(-.38,.26,-.23,.34,-.02,.12,-.04,-.15,-.21,-.35,-.37,-.11)]},
 {id:'sideHair',anchor:[-.40,.03,.28],color:[.19,.28,.45],depthBias:[.04,.06,.07],visible:[true,true,true],keys:[
 P(-.37,.57,-.19,.70,.03,.42,-.03,.10,-.12,-.31,-.03,-.64,-.37,-.70,-.50,-.31),
 P(-.28,.59,-.12,.70,.10,.42,.08,.12,-.03,-.41,.00,-.70,-.25,-.73,-.38,-.33),
 P(-.22,.55,-.07,.67,.10,.40,.08,.05,-.08,-.41,-.05,-.68,-.23,-.68,-.29,-.24)]},
 {id:'fringe',anchor:[0,.55,.35],color:[.21,.31,.48],depthBias:[.06,.07,.08],visible:[true,true,true],keys:[
 P(-.78,.18,-.63,.47,-.17,.55,.41,.50,.78,.22,.68,-.09,.31,-.26,.16,.17,-.12,-.21,-.45,.10,-.67,-.12),
 P(-.64,.20,-.46,.48,-.10,.51,.40,.44,.61,.18,.44,-.12,.13,-.21,.00,.11,-.24,-.14,-.39,.13,-.58,-.08),
 P(-.52,.24,-.32,.45,-.06,.46,.28,.35,.42,.13,.31,-.18,.10,-.12,-.04,.12,-.17,-.17,-.33,.08,-.48,-.05)]},
 {id:'farEye',anchor:[-.26,.05,.42],color:[.11,.17,.29],depthBias:[.04,.04,.04],visible:[true,false,false],keys:[
 P(-.15,.08,0,.15,.17,.07,.12,-.09,-.04,-.13,-.17,-.04),
 P(-.12,.06,0,.12,.10,.04,.08,-.07,-.05,-.10,-.13,-.03),
 P(-.08,.02,0,.07,.04,.02,.04,-.04,-.03,-.06,-.08,-.02)]},
 {id:'nearEye',anchor:[.28,.05,.42],color:[.11,.17,.29],depthBias:[.06,.09,.10],visible:[true,true,true],keys:[
 P(-.17,.08,0,.15,.17,.07,.12,-.09,-.04,-.13,-.17,-.04),
 P(-.15,.08,0,.13,.13,.06,.12,-.08,-.04,-.12,-.16,-.04),
 P(-.11,.05,0,.10,.09,.02,.08,-.08,-.02,-.11,-.10,-.03)]},
 {id:'nose',anchor:[.25,-.11,.46],color:[.82,.49,.41],depthBias:[.08,.10,.13],visible:[true,true,true],keys:[
 P(-.09,.03,.07,.04,.11,-.02,.04,-.07,-.05,-.07),
 P(-.08,.10,.07,.05,.20,-.03,.13,-.12,-.04,-.06),
 P(-.10,.24,.09,.22,.25,.03,.10,-.09,-.08,-.08)]},
 {id:'mouth',anchor:[.14,-.43,.40],color:[.63,.27,.34],depthBias:[.03,.05,.08],visible:[true,true,true],keys:[
 P(-.14,.03,.12,.04,.15,-.03,-.11,-.06),
 P(-.10,.04,.12,.04,.13,-.03,-.08,-.05),
 P(-.08,.04,.13,.04,.12,-.04,-.07,-.06)]}
];
export const keys: readonly Key[]=[0,45,90];
export function keyed<T>(triple:readonly [T,T,T],yaw:number):T{
 return triple[yaw<=22.5?0:yaw<67.5?1:2];
}
export function between(yaw:number):{a:0|1;b:1|2;t:number}{
 const v=Math.max(0,Math.min(90,yaw));
 return v<=45?{a:0,b:1,t:v/45}:{a:1,b:2,t:(v-45)/45};
}
export function outline(part:Part,yaw:number):Point[]{
 const {a,b,t}=between(yaw),left=part.keys[a],right=part.keys[b];
 if(left.length!==right.length)throw Error('semantic point count mismatch: '+part.id);
 return left.map((p,i)=>[p[0]*(1-t)+right[i]![0]*t,p[1]*(1-t)+right[i]![1]*t] as Point);
}
