import * as THREE from 'three';
import {idShader,qaPalette} from './turn360-runtime';

/**
 * Explicit front/rear local clipping expectations. This is a *measured*
 * real WebGL part-ID test using isolated alpha-aware raster masks, not a
 * renderer-state-only or "should be visible" declaration.
 * Generic intersecting-alpha clip masks remain a separate capability;
 * these constraints cover the three overlapping facial component pairs.
 */
export type OcclusionRuleResult={
 front:string;back:string;angle:number;overlapPixels:number;
 incorrectlyBackPixels:number;matches:number;status:'PASS'|'FAIL'|'UNTESTED';
};
const rules=[
 {front:'eyes',back:'face',allow:['eyes']},
 {front:'fringe',back:'face',allow:['fringe','eyes']},
 {front:'face',back:'backHair',allow:['face','fringe','eyes']}
] as const;
const ids=['backHair','torso','skirt','face','fringe','eyes','scarf','emblem','leftArm','rightArm','leftLeg','rightLeg'];
function readPixels(renderer:THREE.WebGLRenderer,scene:THREE.Scene,camera:THREE.Camera,objects:THREE.Object3D[],part:string|null):Uint8Array{
 const w=480,h=270,target=new THREE.WebGLRenderTarget(w,h,{depthBuffer:true});
 const states:{mesh:THREE.Mesh;original:THREE.Material;visible:boolean}[]=[];
 const oldTarget=renderer.getRenderTarget();
 const oldColor=renderer.getClearColor(new THREE.Color()).clone(),oldAlpha=renderer.getClearAlpha();
 const pixels=new Uint8Array(w*h*4);
 try {
  for(const obj of objects){
   if(!(obj instanceof THREE.Mesh)||Array.isArray(obj.material))continue;
   const mat=obj.material,pid=obj.userData.partId as string|null;
   states.push({mesh:obj,original:mat,visible:obj.visible});
   if(!pid||!ids.includes(pid)||(part!==null&&pid!==part)){obj.visible=false;continue;}
   obj.material=idShader(mat,part===null?qaPalette[ids.indexOf(pid)]:[255,255,255]);
  }
  renderer.setRenderTarget(target);renderer.setClearColor(0,1);
  renderer.clear();renderer.render(scene,camera);
  renderer.readRenderTargetPixels(target,0,0,w,h,pixels);
 } finally {
  renderer.setRenderTarget(oldTarget);renderer.setClearColor(oldColor,oldAlpha);
  for(const state of states){
    if(state.mesh.material!==state.original){
      const temp=state.mesh.material;
      if(Array.isArray(temp))temp.forEach(x=>x.dispose());else temp.dispose();
    }
    state.mesh.material=state.original;state.mesh.visible=state.visible;
  }
  target.dispose();renderer.render(scene,camera);
 }
 return pixels;
}
const rgb=(arr:Uint8Array,k:number)=>(arr[k]<<16)|(arr[k+1]<<8)|arr[k+2];
const encoded=(id:string):number=>{
 const [r,g,b]=qaPalette[ids.indexOf(id)];
 return (r<<16)|(g<<8)|b;
};
export function auditLocalOcclusion(
 renderer:THREE.WebGLRenderer,scene:THREE.Scene,
 camera:THREE.OrthographicCamera,objects:THREE.Object3D[],
 angle:number
):OcclusionRuleResult[]{
 const real=readPixels(renderer,scene,camera,objects,null);
 const torsoArmRules=angle===0?[
    {front:'leftArm',back:'torso',allow:['leftArm']},
    {front:'rightArm',back:'torso',allow:['rightArm']}
   ]:angle===180?[
    {front:'torso',back:'leftArm',allow:['torso']},
    {front:'torso',back:'rightArm',allow:['torso']}
   ]:[];
 const activeRules=angle===180?torsoArmRules:[...rules,...torsoArmRules];
 const needed=[...new Set(activeRules.flatMap(x=>[x.front,x.back]))];
 const isolated=new Map(needed.map(id=>[id,readPixels(renderer,scene,camera,objects,id)]));
 return activeRules.map(rule=>{
   const front=isolated.get(rule.front)!,back=isolated.get(rule.back)!;
   const allowed=new Set(rule.allow.map(encoded));
   let overlap=0,wrong=0,matched=0;
   for(let p=0;p<real.length;p+=4){
     if(rgb(front,p)!==0xffffff||rgb(back,p)!==0xffffff)continue;
     overlap++;
     const id=rgb(real,p);
     if(allowed.has(id))matched++;
     else if(id===encoded(rule.back))wrong++;
   }
   // Never grant PASS from zero overlap or mere intent-state.
   const status=overlap<6?'UNTESTED':
     wrong>Math.max(2,overlap*.025)?'FAIL':'PASS';
   return {angle,front:rule.front,back:rule.back,overlapPixels:overlap,
      incorrectlyBackPixels:wrong,matches:matched,status};
 });
}
