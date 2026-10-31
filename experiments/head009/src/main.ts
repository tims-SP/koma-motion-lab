import * as THREE from 'three';
import {parts,outline,between,type Part} from './art';
const size=640;
const canvas=document.querySelector<HTMLCanvasElement>('#stage');
if(!canvas)throw Error('missing #stage');
const renderer=new THREE.WebGLRenderer({canvas,antialias:false,alpha:true,preserveDrawingBuffer:true});
renderer.setSize(size,size,false);
renderer.setPixelRatio(1);
renderer.outputColorSpace=THREE.LinearSRGBColorSpace;
const scene=new THREE.Scene();
const camera=new THREE.OrthographicCamera(-1.35,1.35,1.35,-1.35,0.1,30);
camera.position.set(0,0,8);camera.lookAt(0,0,0);
const vertexShader=`uniform float uDepthNudge;
varying float vLocalX;
void main() { vLocalX=position.x; vec3 p=position; p.z+=uDepthNudge; gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0); }`;
const fragmentShader=`uniform float uPass;
uniform vec3 uColor;
uniform float uId;
uniform float uFaultMask;
varying float vLocalX;
void main() {
  // One coverage predicate for all passes. Deliberate QA mask fault is injected in ID only.
  if (uFaultMask > 0.5 && vLocalX > 0.02) discard;
  if (uPass < 0.5) gl_FragColor=vec4(uColor,1.0);
  else if (uPass < 1.5) gl_FragColor=vec4(uId/255.0,0.36,0.62,1.0);
  else if (uPass < 2.5) gl_FragColor=vec4(0.4,0.65,0.86,1.0);
  else gl_FragColor=vec4(1.0,1.0,1.0,1.0);
}`;
const objects: {part:Part;mesh:THREE.Mesh<THREE.BufferGeometry,THREE.ShaderMaterial>}[]=[];
for(let i=0;i<parts.length;i++){
 const part=parts[i]!;
 const material=new THREE.ShaderMaterial({vertexShader,fragmentShader,
  uniforms:{uPass:{value:0},uColor:{value:new THREE.Vector3(...part.color)},uId:{value:i+1},uFaultMask:{value:0},uDepthNudge:{value:0}},
  depthTest:true,depthWrite:true,transparent:false,side:THREE.DoubleSide});
 const mesh=new THREE.Mesh(new THREE.BufferGeometry(),material);
 scene.add(mesh);objects.push({part,mesh});
}
const rt=new THREE.WebGLRenderTarget(size,size,{format:THREE.RGBAFormat,type:THREE.UnsignedByteType,depthBuffer:true,stencilBuffer:false});
function setScene(yaw:number,pass:number,fault:'none'|'mask'|'depth'='none'):void{
 const rad=yaw*Math.PI/180,c=Math.cos(rad),s=Math.sin(rad);
 const {a,b,t}=between(yaw);
 for(const {part,mesh} of objects){
  const visibleA=part.visible[a],visibleB=part.visible[b];
  const active=visibleA||visibleB;
  mesh.visible=active;
  if(!active)continue;
  // On topological visibility change, part appears at the authored key, not full-face RGB crossfade.
  if(visibleA!==visibleB)mesh.visible=visibleA ? t<0.5 : t>=0.5;
  const pts=outline(part,yaw);
  const shape=new THREE.Shape();
  shape.moveTo(pts[0]![0],pts[0]![1]);
  for(const p of pts.slice(1))shape.lineTo(p[0],p[1]);
  shape.closePath();
  mesh.geometry.dispose();
  mesh.geometry=new THREE.ShapeGeometry(shape);
  const [ax,ay,az]=part.anchor;
  const baseZ=az*c-ax*s;
  const depth=part.depthBias[a]*(1-t)+part.depthBias[b]*t;
  mesh.position.set(ax*c+az*s,ay,baseZ+depth);
  const uniforms=mesh.material.uniforms;
  uniforms.uPass!.value=pass;
  uniforms.uFaultMask!.value=fault==='mask' && pass===1 ? 1 : 0;
  uniforms.uDepthNudge!.value=fault==='depth'&&pass===1 && part.id==='fringe' ? -3 : 0;
 }
}
function raw(yaw:number,pass:number,fault:'none'|'mask'|'depth'='none'):Uint8Array{
 setScene(yaw,pass,fault);
 renderer.setRenderTarget(rt);
 renderer.setClearColor(0x000000,0);renderer.clear(true,true,true);renderer.render(scene,camera);
 const buf=new Uint8Array(size*size*4);renderer.readRenderTargetPixels(rt,0,0,size,size,buf);
 renderer.setRenderTarget(null);return buf;
}
export function frame(yaw:number,pass=0):void{
 setScene(yaw,pass);
 renderer.setRenderTarget(null);renderer.setClearColor(0x293249,1);
 renderer.clear(true,true,true);renderer.render(scene,camera);
}
function delta(a:Uint8Array,b:Uint8Array,channels:boolean):number{
 let count=0;for(let i=0;i<a.length;i+=4){
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
 return {yaw,coveragePixels:coverage,opaqueCoverageMismatches:parity,
  faultMaskCoverageMismatch:maskFault,faultDepthIdChangedPixels:depthFault,
  result:coverage>10000&&parity.every(x=>x===0)&&maskFault>500&&depthFault>100?'PASS_ENGINEERING':'FAIL'};
}
frame(0);
declare global {interface Window {head009:{frame:typeof frame;qa:typeof qa}}}
window.head009={frame,qa};
