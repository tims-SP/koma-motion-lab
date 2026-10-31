import * as THREE from 'three';
import {parts,between,type Part,type Point} from './art';
import {loadReferenceArt,type SourcePath} from './reference-runtime';
const size=640;
const canvas=document.querySelector<HTMLCanvasElement>('#stage');
if(!canvas)throw Error('missing #stage');
const renderer=new THREE.WebGLRenderer({canvas,antialias:false,alpha:true,preserveDrawingBuffer:true});
renderer.setSize(size,size,false);renderer.setPixelRatio(1);
renderer.outputColorSpace=THREE.LinearSRGBColorSpace;
const scene=new THREE.Scene();
const camera=new THREE.OrthographicCamera(-1.35,1.35,1.35,-1.35,0.1,30);
camera.position.set(0,0,8);camera.lookAt(0,0,0);
const art=await loadReferenceArt();
const vertexShader=`uniform float uDepthNudge;
varying float vLocalX;
void main(){vLocalX=position.x;vec3 p=position;p.z+=uDepthNudge;gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0);}`;
const fragmentShader=`uniform float uPass;
uniform vec3 uColor;
uniform float uId;
uniform float uFaultMask;
varying float vLocalX;
void main(){
 if(uFaultMask>0.5&&vLocalX>0.02)discard;
 if(uPass<0.5)gl_FragColor=vec4(uColor,1.0);
 else if(uPass<1.5)gl_FragColor=vec4(uId/255.0,0.36,0.62,1.0);
 else if(uPass<2.5)gl_FragColor=vec4(.4,.65,.86,1.0);
 else gl_FragColor=vec4(1.0,1.0,1.0,1.0);
}`;
type Component={mesh:THREE.Mesh<THREE.BufferGeometry,THREE.ShaderMaterial>;kind:'fill'|'stroke'};
const objects:{part:Part;components:Component[]}[]=[];
const make=(id:number,part:Part)=>{
 const material=new THREE.ShaderMaterial({vertexShader,fragmentShader,uniforms:{
  uPass:{value:0},uColor:{value:new THREE.Color(0xffffff)},uId:{value:id+1},
  uFaultMask:{value:0},uDepthNudge:{value:0}},
  depthTest:true,depthWrite:true,transparent:false,side:THREE.DoubleSide});
 const mesh=new THREE.Mesh(new THREE.BufferGeometry(),material);scene.add(mesh);return mesh;
};
for(let i=0;i<parts.length;i++){
 const part=parts[i]!;
 objects.push({part,components:[{mesh:make(i,part),kind:'fill'},{mesh:make(i,part),kind:'stroke'}]});
}
const target=new THREE.WebGLRenderTarget(size,size,{format:THREE.RGBAFormat,type:THREE.UnsignedByteType,depthBuffer:true});
const refYaw=[0,45,90];
const anchorScreen=(p:Part,k:number):Point=>{
 const [x,y,z]=p.anchor,theta=refYaw[k]!*Math.PI/180;
 return [x*Math.cos(theta)+z*Math.sin(theta),y];
};
const lerp=(a:number,b:number,t:number)=>a*(1-t)+b*t;
function sourceFor(part:Part,yaw:number):{pts:Point[];source:SourcePath|null;strokeWidth:number}|null{
 const keys=art[part.id]??[],{a,b,t}=between(yaw),A=keys[a]??null,B=keys[b]??null;
 if(!A&&!B)return null;
 if(!A&&t<.5||!B&&t>=.5)return null;
 const src=A??B;
 if(!src)return null;
 const points:Point[]=[];
 const ca=anchorScreen(part,a),cb=anchorScreen(part,b);
 const [ax,ay,az]=part.anchor,rad=yaw*Math.PI/180;
 const pos:Point=[ax*Math.cos(rad)+az*Math.sin(rad),ay];
 for(let i=0;i<src.points.length;i++){
  const pa=(A??B)!.points[i]!,pb=(B??A)!.points[i]!;
  points.push([
   lerp(pa[0]-ca[0],pb[0]-cb[0],t)+pos[0],
   lerp(pa[1]-ca[1],pb[1]-cb[1],t)+pos[1]
  ]);
 }
 return {pts:points,source:src,strokeWidth:lerp((A??B)!.strokeWidth,(B??A)!.strokeWidth,t)};
}
function shapeGeometry(pts:Point[]):THREE.BufferGeometry{
 const shape=new THREE.Shape();
 shape.moveTo(pts[0]![0],pts[0]![1]);
 for(let i=1;i<pts.length;i++)shape.lineTo(pts[i]![0],pts[i]![1]);
 shape.closePath();
 return new THREE.ShapeGeometry(shape);
}
function strokeGeometry(pts:Point[],width:number,closed:boolean):THREE.BufferGeometry{
 const verts:number[]=[];
 const count=closed?pts.length:pts.length-1;
 for(let i=0;i<count;i++){
  const a=pts[i]!,b=pts[(i+1)%pts.length]!;
  const dx=b[0]-a[0],dy=b[1]-a[1],norm=Math.hypot(dx,dy);
  if(norm<1e-8)continue;
  const nx=-dy/norm*width*.5,ny=dx/norm*width*.5;
  const p0=[a[0]+nx,a[1]+ny,0],p1=[a[0]-nx,a[1]-ny,0],
        p2=[b[0]+nx,b[1]+ny,0],p3=[b[0]-nx,b[1]-ny,0];
  verts.push(...p0,...p1,...p2,...p2,...p1,...p3);
 }
 const geo=new THREE.BufferGeometry();
 geo.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));
 return geo;
}
function setScene(yaw:number,pass:number,fault:'none'|'mask'|'depth'='none'){
 const rad=yaw*Math.PI/180,c=Math.cos(rad),s=Math.sin(rad),{a,b,t}=between(yaw);
 for(const {part,components} of objects){
  const v=sourceFor(part,yaw);
  const [ax,,az]=part.anchor;
  const depth=lerp(part.depthBias[a],part.depthBias[b],t);
  // The authored 45° and 90° ear layers are preserved exactly. Between them,
  // the near-side face occludes the ear until its final profile emergence.
  // This per-part depth correction is a view-conditioned occlusion rule (Plan B VDD).
  const earOcclusion=part.id==='farEar'&&yaw>45&&yaw<90
    ? 0.64*Math.sin(Math.PI*(yaw-45)/45) : 0;
  const z=az*c-ax*s+depth-earOcclusion;
  for(const {mesh,kind} of components){
   mesh.visible=!!v && !!(kind==='fill'?v.source?.fill:v.source?.stroke);
   if(!mesh.visible||!v)continue;
   mesh.geometry.dispose();
   mesh.geometry=kind==='fill'?shapeGeometry(v.pts):strokeGeometry(v.pts,v.strokeWidth,v.source!.closed);
   mesh.position.set(0,0,z+(kind==='stroke'?.008:0));
   mesh.material.uniforms.uColor!.value.set(kind==='fill'?v.source!.fill:v.source!.stroke);
   mesh.material.uniforms.uPass!.value=pass;
   mesh.material.uniforms.uFaultMask!.value=fault==='mask'&&pass===1?1:0;
   mesh.material.uniforms.uDepthNudge!.value=fault==='depth'&&pass===1&&part.id==='fringe'?-3:0;
  }
 }
}
function raw(yaw:number,pass:number,fault:'none'|'mask'|'depth'='none'){
 setScene(yaw,pass,fault);
 renderer.setRenderTarget(target);renderer.setClearColor(0,0);renderer.clear(true,true,true);renderer.render(scene,camera);
 const buf=new Uint8Array(size*size*4);renderer.readRenderTargetPixels(target,0,0,size,size,buf);
 renderer.setRenderTarget(null);return buf;
}
export function frame(yaw:number,pass=0){
 setScene(yaw,pass);renderer.setRenderTarget(null);renderer.setClearColor(0x293249,1);
 renderer.clear(true,true,true);renderer.render(scene,camera);
}
function delta(a:Uint8Array,b:Uint8Array,channels:boolean){
 let count=0;
 for(let i=0;i<a.length;i+=4){
  if(channels){if(a[i]!==b[i]||a[i+1]!==b[i+1]||a[i+2]!==b[i+2]||a[i+3]!==b[i+3])count++;}
  else if((a[i+3]>0)!==(b[i+3]>0))count++;
 }return count;
}
export function qa(yaw:number){
 const beauty=raw(yaw,0),id=raw(yaw,1),depth=raw(yaw,2),alpha=raw(yaw,3);
 const faultMask=raw(yaw,1,'mask'),faultDepth=raw(yaw,1,'depth');
 let coverage=0;for(let i=3;i<beauty.length;i+=4)if(beauty[i]>0)coverage++;
 const parity=[delta(beauty,id,false),delta(beauty,depth,false),delta(beauty,alpha,false)];
 const maskFault=delta(beauty,faultMask,false),depthFault=delta(id,faultDepth,true);
 const visibleParts:Record<string,number>={};for(const part of parts)visibleParts[part.id]=0;
 for(let i=0;i<id.length;i+=4)if(id[i+3]>0){
  const index=id[i]-1;if(index>=0&&index<parts.length)visibleParts[parts[index]!.id]!++;
 }
 const actualSideAnatomy=yaw!==90||(['farEye','farEar','nose','mouth'] as const).every(name=>visibleParts[name]>80);
 return {yaw,coveragePixels:coverage,visibleParts,opaqueCoverageMismatches:parity,
  faultMaskCoverageMismatch:maskFault,faultDepthIdChangedPixels:depthFault,actualSideAnatomy,
  result:coverage>10000&&parity.every(x=>x===0)&&maskFault>500&&depthFault>100&&actualSideAnatomy?'PASS_ENGINEERING':'FAIL'};
}
// Pixel-level check against the ACTUAL visible z-buffer part-ID raster.
// readRenderTargetPixels is bottom-up, whereas source annotations use top-left origin.
export function probeParts(yaw:number, points:Record<string,Point>, organParts:Record<string,string>){
 const id=raw(yaw,1);
 const out:Record<string,{part:string;nearestVisiblePx:number|null;within8px:boolean}>={};
 for(const [semantic,[cx,cy]] of Object.entries(points)){
  const target=parts.findIndex(p=>p.id===organParts[semantic]);
  if(target<0)throw Error('unmapped part for '+semantic);
  let near=Infinity;
  for(let dy=-24;dy<=24;dy++)for(let dx=-24;dx<=24;dx++){
   const x=Math.round(cx)+dx,y=Math.round(cy)+dy;
   if(x<0||x>=size||y<0||y>=size)continue;
   const p=((size-1-y)*size+x)*4;
   if(id[p+3]>0 && id[p]===target+1)near=Math.min(near,Math.hypot(cx-x,cy-y));
  }
  out[semantic]={part:parts[target]!.id,nearestVisiblePx:Number.isFinite(near)?near:null,within8px:near<=8};
 }
 return out;
}
frame(0);
declare global {interface Window {head009:{frame:typeof frame;qa:typeof qa;probeParts:typeof probeParts}}}
window.head009={frame,qa,probeParts};
