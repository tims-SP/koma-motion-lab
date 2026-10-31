import * as THREE from 'three';
import {LEFT_CONTOURS,LEFT_VDD_SHIFT} from './left-keyviews';
import {auditLocalOcclusion} from './qa/occlusion-audit';
import {createRegisteredArt, artTextureProof, artTexturePNG} from './rgba-view-art';
import {Turn360Recorder, qaPalette, idShader, countIdPixels} from './qa/turn360-runtime';
import type {FrameTrace} from './qa/turn360-contract';

/**
 * MVP-003: exactly one small 3-keyview, 12-part character driven by
 * 3D anchors/bones/analytic 3D IK, per-part orientation space, VDD,
 * UV-mapped ArtMesh, depth occlusion and moving art-directed light.
 * This is technical proxy art: no complex game assets and no photoreal claim.
 */
type XY = readonly [number, number];
type View = 0 | 90 | 180 | 270;
type PartId = 'backHair'|'torso'|'skirt'|'face'|'fringe'|'eyes'|'scarf'|'emblem'|'leftArm'|'rightArm'|'leftLeg'|'rightLeg';
type Role = 'body'|'head'|'arm'|'leg';
interface KeyArt { yaw:View; contour:readonly XY[]; shift:XY; visible:number; }
interface Part { id:PartId; role:Role; anchor:THREE.Vector3; size:XY; color:string; keys:readonly [KeyArt,KeyArt,KeyArt,KeyArt]; }
interface FrameStats {
  frame:number; time:number; yaw:number; headLocalYaw:number;
  partCount:number; keyViewCount:number; artMeshCount:number;
  ikError:number; handMinusTorsoDepth:number; armLocalYaw:number;
  lightAngle:number; shadowOffset:number; blink:number; targetX:number; handX:number;
  faceVisibility:number;faceShadowOpacity:number;
}
declare global {interface Window {
  renderIntegrated:(frame:number,total:number)=>FrameStats;
  integratedInfo:{parts:number;views:number;method:string};
  integratedArtProof:{transparent:boolean;centerOpaque:boolean;allDistinct:boolean;views:number};
  exportArtPNG:(partId:PartId,angle:View)=>string;
  renderTurn360:(yaw:number,frameIndex:number)=>{stats:FrameStats;trace:FrameTrace};
  renderDynamic360:(yaw:number,frameIndex:number)=>{stats:FrameStats;trace:FrameTrace;pose:{
    reach:number;fore:number;headLocalYaw:number;shoulderXYZ:number[];elbowXYZ:number[];
    handXYZ:number[];targetXYZ:number[];handDistance:number;footLXYZ:number[];footRXYZ:number[];
    poseTime:number;handTorsoLocalZ:number
  }};
  captureTurnPass:(pass:'id'|'depth'|'mask',includeImage:boolean)=>{counts:Record<string,number>;dataUrl?:string;bounds?:readonly [number,number,number,number]};
  turnSourceViews:{angles:number[];independent270:boolean;derivedPartIds:string[];authoredGeometry:{id:string;right:readonly XY[];left:readonly XY[];rightVDD:XY;leftVDD:XY}[]};
  auditTurnOcclusion:()=>ReturnType<typeof auditLocalOcclusion>;
}}

const screen=document.querySelector<HTMLCanvasElement>('#viewport');
if (!screen) throw Error('Missing #viewport');
const renderer=new THREE.WebGLRenderer({canvas:screen,antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);
renderer.setSize(960,540,false);
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.setClearColor('#101a30');
const scene=new THREE.Scene();
const camera=new THREE.OrthographicCamera(-4.7,4.7,2.64,-2.64,.1,60);
camera.position.set(0,1.95,15);camera.lookAt(0,1.95,0);camera.updateProjectionMatrix();
const root=new THREE.Group();scene.add(root);
const drawn:THREE.Object3D[]=[];
const qaRecorder=new Turn360Recorder();
const qaBindings=new Map<PartId,{local:THREE.Vector3;world:THREE.Matrix4;boneId:string}>();
const PART_IDS:PartId[]=['backHair','torso','skirt','face','fringe','eyes','scarf','emblem','leftArm','rightArm','leftLeg','rightLeg'];
const V=(x:number,y:number,z=0)=>new THREE.Vector3(x,y,z);
const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const smooth=(x:number)=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x);};
const wrap=(a:number)=>(a%360+360)%360;
const DEG=Math.PI/180;
const contour=(pairs:number[][]):readonly XY[]=>pairs.map(p=>[p[0],p[1]] as XY);
const base=contour([[-.65,.74],[-.35,.93],[.2,.98],[.64,.78],[.83,.24],[.75,-.39],[.39,-.82],[0,-1],[-.43,-.78],[-.8,-.35],[-.82,.26]]);
const side=contour([[-.49,.75],[-.30,.94],[.20,.92],[.53,.62],[.58,.17],[.90,-.07],[.52,-.64],[.06,-.98],[-.38,-.79],[-.60,-.35],[-.60,.28]]);
const rear=contour([[-.69,.70],[-.30,.93],[.25,.95],[.68,.72],[.82,.20],[.72,-.43],[.40,-.86],[0,-.96],[-.48,-.80],[-.80,-.37],[-.83,.19]]);
const skirtFront=contour([[-.47,.92],[-.28,1],[.27,1],[.49,.90],[.92,-.60],[.67,-.82],[.22,-.74],[-.13,-.90],[-.54,-.76],[-.91,-.59],[-.72,.2]]);
const skirtSide=contour([[-.37,.92],[-.20,1],[.22,1],[.42,.85],[.66,-.59],[.38,-.77],[.08,-.79],[-.23,-.86],[-.52,-.73],[-.69,-.55],[-.47,.12]]);
const elong=contour([[-.67,.82],[-.38,.99],[.33,1],[.70,.76],[.85,.38],[.82,-.28],[.48,-.87],[0,-1],[-.49,-.85],[-.88,-.32],[-.87,.31]]);
const patch=(id:PartId,front:readonly XY[],sideC:readonly XY[],back:readonly XY[],shifts:readonly XY[]=[[0,0],[0,0],[0,0]],vis:number[]=[1,1,1]):[KeyArt,KeyArt,KeyArt,KeyArt]=>{
 const left=LEFT_CONTOURS[id],vdd=LEFT_VDD_SHIFT[id];
 if(!left||left.length!==front.length||!vdd)throw Error('Missing independent 270-degree key geometry: '+id);
 return [
  {yaw:0,contour:front,shift:shifts[0],visible:vis[0]},
  {yaw:90,contour:sideC,shift:shifts[1],visible:vis[1]},
  {yaw:180,contour:back,shift:shifts[2],visible:vis[2]},
  {yaw:270,contour:left,shift:vdd,visible:vis[1]}
 ];
};
const defs:Part[]=[
 {id:'backHair',role:'head',anchor:V(0,.05,-.21),size:[.57,.69],color:'#303b65',keys:patch('backHair',base,side,elong,[[0,0],[.08,.015],[0,0]])},
 {id:'torso',role:'body',anchor:V(0,1.96,0),size:[.48,.57],color:'#6488ab',keys:patch('torso',base,side,rear,[[0,0],[.09,0],[0,0]])},
 {id:'skirt',role:'body',anchor:V(0,1.29,0),size:[.53,.40],color:'#414a81',keys:patch('skirt',skirtFront,skirtSide,skirtFront)},
 {id:'face',role:'head',anchor:V(0,0,.13),size:[.42,.51],color:'#f8ceb5',keys:patch('face',base,side,rear,[[0,0],[.13,-.02],[0,-.01]],[1,1,0])},
 {id:'fringe',role:'head',anchor:V(0,.34,.28),size:[.49,.25],color:'#384369',keys:patch('fringe',skirtFront,skirtSide,skirtFront,[[0,0],[.11,.02],[0,0]],[1,.85,0])},
 {id:'eyes',role:'head',anchor:V(0,.04,.36),size:[.37,.155],color:'#e8f5fa',keys:patch('eyes',base,side,rear,[[0,0],[.10,0],[0,0]],[1,.5,0])},
 {id:'scarf',role:'body',anchor:V(0,2.38,.20),size:[.24,.18],color:'#d48b9a',keys:patch('scarf',skirtFront,skirtSide,skirtFront,[[0,0],[.05,0],[0,0]],[1,.75,.3])},
 {id:'emblem',role:'body',anchor:V(-.23,2.07,.30),size:[.105,.11],color:'#f7dca4',keys:patch('emblem',base,side,rear,[[0,0],[.015,0],[.0,0]],[1,.7,0])},
 {id:'leftArm',role:'arm',anchor:V(-.46,2.26,.08),size:[.17,.75],color:'#e9bba7',keys:patch('leftArm',base,side,rear)},
 {id:'rightArm',role:'arm',anchor:V(.46,2.26,.08),size:[.17,.75],color:'#e9bba7',keys:patch('rightArm',base,side,rear)},
 {id:'leftLeg',role:'leg',anchor:V(-.21,1.08,.02),size:[.20,.82],color:'#d8b6ab',keys:patch('leftLeg',base,side,rear)},
 {id:'rightLeg',role:'leg',anchor:V(.21,1.08,.02),size:[.20,.82],color:'#d8b6ab',keys:patch('rightLeg',base,side,rear)},
];
if(defs.length!==12 || defs.some(x=>x.keys.some(k=>k.contour.length!==x.keys[0].contour.length)))throw Error('Incompatible key topology');
function keyPair(yaw:number):{t:number;indices:readonly [number,number]} {
  const a=wrap(yaw),segment=Math.min(3,Math.floor(a/90));
  return {t:smooth((a-segment*90)/90),indices:[segment,(segment+1)%4]};
}
function sample(part:Part,yaw:number):{shape:XY[];shift:XY;visible:number;baseVisible:number;frontMask:number;keyIndex:number} {
 const {t,indices}=keyPair(yaw);
 const A=part.keys[indices[0]],B=part.keys[indices[1]];
 const s=part.keys[0].contour.map((_,i)=>{
   const a=A.contour[i],b=B.contour[i];
   return [lerp(a[0],b[0],t),lerp(a[1],b[1],t)] as XY;
 });
 // Front-only facial drawings must disappear before reaching rear
 // three-quarter angles; otherwise render-order compositing leaves a
 // translucent gray "ghost face" over the back hair at 135°/225°.
 // Smooth windows avoid the former one-frame z-order snap at 90°/270°.
 let frontVisibility=1;
 const observerYaw=wrap(yaw);
 if(['face','eyes','fringe'].includes(part.id)&&observerYaw>90&&observerYaw<270){
   if(observerYaw<110)frontVisibility=1-smooth((observerYaw-90)/20);
   else if(observerYaw>250)frontVisibility=smooth((observerYaw-250)/20);
   else frontVisibility=0;
 }
 const baseVisible=lerp(A.visible,B.visible,t);
 return {shape:s,shift:[lerp(A.shift[0],B.shift[0],t),lerp(A.shift[1],B.shift[1],t)],
         visible:baseVisible*frontVisibility,baseVisible,frontMask:frontVisibility,
         keyIndex:indices[0]};
}
function registeredMaterial(part:Part,yaw:number,opacity:number,frontMask=1):THREE.ShaderMaterial {
 const pair=keyPair(yaw);
 const angles:[View,View,View,View]=[0,90,180,270];
 return new THREE.ShaderMaterial({
  uniforms:{
   artA:{value:createRegisteredArt(part,angles[pair.indices[0]])},
   artB:{value:createRegisteredArt(part,angles[pair.indices[1]])},
   transition:{value:pair.t},
   strength:{value:opacity},
   frontMask:{value:frontMask},
   faceWipe:{value:['face','eyes','fringe'].includes(part.id)?1:0},
   // Exit/re-entry must reveal pixels from the hair-adjacent UV edge.
   // Revealing the outer cheek first on 250→270° creates a disconnected
   // line at frames 130-131 before the rest of the face becomes visible.
   wipeDirection:{value:1}
  },
  // Face/eyes/fringe are an authored art-compositing stack, not generic 3D
  // transparent planes. Their visibility fades across rear-key transitions.
  // If these layers use z-test, a side-on equal-z tie flips a whole face in
  // one frame at 90°/270°. This view-aware draw order is deliberate.
  transparent:true,depthTest:!['face','eyes','fringe'].includes(part.id),
  depthWrite:!['face','eyes','fringe'].includes(part.id),
  side:THREE.DoubleSide,
  vertexShader:[
   'varying vec2 registeredUV;',
   'void main(){ registeredUV=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }'
  ].join('\n'),
  fragmentShader:[
   'uniform sampler2D artA;',
   'uniform sampler2D artB;',
   'uniform float transition;',
   'uniform float strength;',
   'uniform float frontMask, faceWipe, wipeDirection;',
   'varying vec2 registeredUV;',
   'void main(){',
   '  vec4 a=texture2D(artA,registeredUV);',
   '  vec4 b=texture2D(artB,registeredUV);',
   '  float coverage=mix(a.a,b.a,transition);',
   '  float alpha=coverage*strength;',
   '  if(faceWipe>0.5 && frontMask<0.999){',
   '    float side=wipeDirection>0.0?registeredUV.x:1.0-registeredUV.x;',
   '    if(side<1.0-frontMask)discard;',
   '  }',
   '  if(alpha < 0.08) discard;',
   '  vec3 premultiplied=mix(a.rgb*a.a,b.rgb*b.a,transition);',
   '  vec3 color=premultiplied/max(coverage,0.001);',
   '  gl_FragColor=vec4(color,alpha);',
   '  #include <tonemapping_fragment>',
   '  #include <colorspace_fragment>',
   '}'
  ].join('\n')
 });
}
function emitGeometry(vertices:THREE.Vector3[],uvs:XY[],indices:number[],material:THREE.Material,partId?:PartId):void {
 const g=new THREE.BufferGeometry(),positions=new Float32Array(vertices.flatMap(p=>[p.x,p.y,p.z]));
 const u=new Float32Array(uvs.flatMap(p=>[p[0],p[1]]));
 g.setAttribute('position',new THREE.BufferAttribute(positions,3));
 g.setAttribute('uv',new THREE.BufferAttribute(u,2));g.setIndex(indices);
 g.computeVertexNormals();
 const mesh=new THREE.Mesh(g,material);
 mesh.userData.partId=partId??null;
 mesh.renderOrder=partId==='face'?100:partId==='fringe'?110:partId==='eyes'?120:0;
 root.add(mesh);drawn.push(mesh);
}
function artMesh(part:Part,center:THREE.Vector3,yaw:number,alpha=1,scale=1,squashY=1):void {
 const f=sample(part,yaw),n=f.shape.length,amount=f.visible*alpha;
 if(amount<.025)return;
 // p(theta) = projected(R*A) + per-keyview 2D VDD shift. The UV vertices
 // correspond across views; the author-shape contours deform non-rigidly.
 const vertices=[V(center.x+f.shift[0],center.y+f.shift[1],center.z)];
 const uvs:XY[]=[[.5,.5]];
 for(const [x,y] of f.shape){
   vertices.push(V(center.x+f.shift[0]+x*part.size[0]*scale,
                   center.y+f.shift[1]+y*part.size[1]*scale*squashY,center.z));
   // The registered UV belongs to the stable semantic vertex ID,
   // not its deformed intermediate screen position.
   const canonical=part.keys[0].contour[uvs.length-1];
   uvs.push([(canonical[0]+1)/2,(canonical[1]+1)/2]);
 }
 const indices:number[]=[];for(let i=1;i<=n;i++)indices.push(0,i,i%n+1);
 // An exiting face should be *occluded by a directional local mask*,
 // not alpha-faded over the rear hair (which creates a gray ghost wedge).
 const materialAlpha=['face','eyes','fringe'].includes(part.id)?
   f.baseVisible*alpha:amount;
 emitGeometry(vertices,uvs,indices,
   registeredMaterial(part,yaw,materialAlpha,f.frontMask),part.id);
 if(qaRecorder.active){
   const key=keyPair(yaw),angles:[View,View,View,View]=[0,90,180,270];
   const binding=qaBindings.get(part.id);
   if(!binding)throw Error('Missing actual rig binding for '+part.id);
   qaRecorder.record({
     id:part.id,center,vddOffset:f.shift,vertices,uv:uvs,triangles:indices,
     keyA:angles[key.indices[0]],keyB:angles[key.indices[1]],weight:key.t,
     visible:amount,parent:binding.boneId,
     sourceIsDerived:false,authoredKeys:part.keys,
     localAnchor:binding.local,boneWorld:binding.world,camera
   });
 }
}
function polygon(points:THREE.Vector3[],color:string,opacity=1,partId?:PartId):void {
 const ctr=new THREE.Vector3();
 for(const p of points)ctr.add(p);ctr.multiplyScalar(1/points.length);
 const geo=[ctr,...points],uvs:XY[]=geo.map(p=>[(p.x+4)/8,(p.y+1)/5]),index:number[]=[];
 for(let i=1;i<=points.length;i++)index.push(0,i,i%points.length+1);
 emitGeometry(geo,uvs,index,new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide,
   transparent:opacity<.999,opacity,depthWrite:opacity===1,depthTest:true}),partId);
}
function limb(from:THREE.Vector3,to:THREE.Vector3,r:number,color:string,partId?:PartId):void{
 // 3D-joint-driven billboard with independently interpolated depth from
 // source and destination. Per-pixel depth test handles torso crossing.
 const tangent=to.clone().sub(from),flat=V(-tangent.y,tangent.x,0).normalize().multiplyScalar(r);
 if(flat.lengthSq()<.0001)flat.set(r,0,0);
 polygon([from.clone().add(flat),to.clone().add(flat),
          to.clone().sub(flat),from.clone().sub(flat)],color,1,partId);
}
function transform(anchor:THREE.Vector3,rootYaw:number):THREE.Vector3 {
 const y=rootYaw*DEG;return V(anchor.x*Math.cos(y)+anchor.z*Math.sin(y),anchor.y,
                                      anchor.z*Math.cos(y)-anchor.x*Math.sin(y));
}
function inverseViewingYaw(worldYaw:number):number {return wrap(worldYaw);}
function solveIK(shoulder:THREE.Vector3,target:THREE.Vector3,L1:number,L2:number,pole:THREE.Vector3):{
 elbow:THREE.Vector3;hand:THREE.Vector3;error:number;
}{
 const delta=target.clone().sub(shoulder),raw=delta.length(),distance=Math.min(raw,L1+L2-1e-4);
 const axis=delta.normalize(),a=(L1*L1-L2*L2+distance*distance)/(2*distance),
 h=Math.sqrt(Math.max(0,L1*L1-a*a));
 const pd=pole.clone().addScaledVector(axis,-pole.dot(axis)).normalize();
 const elbow=shoulder.clone().addScaledVector(axis,a).addScaledVector(pd,h);
 const hand=shoulder.clone().addScaledVector(axis,distance);
 return {elbow,hand,error:hand.distanceTo(target)};
}
function cleanup():void{
 for(const obj of drawn){root.remove(obj);if(obj instanceof THREE.Mesh){obj.geometry.dispose();if(Array.isArray(obj.material))obj.material.forEach(m=>m.dispose());else obj.material.dispose();}}
 drawn.length=0;
}
function canvasLight(x:number,y:number,z:number,shift:number,opacity:number):void {
 polygon([V(x+shift-.30,y+.35,z),V(x+shift+.05,y+.37,z),
          V(x+shift+.30,y-.35,z),V(x+shift-.1,y-.37,z)],'#b67d97',opacity);
}
function glint(t:number):void{
 for(let i=0;i<16;i++){
  const x=1.35*Math.sin(i*7.91+t*.7),y=2+.75*Math.cos(i*1.73+t*.8),
  z=.82+Math.sin(i*3)*.12,sz=.015+(i%4)*.007;
  polygon([V(x-sz,y,z),V(x,y+sz*1.8,z),V(x+sz,y,z),V(x,y-sz*1.8,z)],
    i%3===0?'#ffd5df':'#9dcced',.7);
 }
}
let lastDynamicPose:{
 reach:number;fore:number;headLocalYaw:number;shoulderXYZ:number[];elbowXYZ:number[];
 handXYZ:number[];targetXYZ:number[];handDistance:number;footLXYZ:number[];footRXYZ:number[];
 poseTime:number;handTorsoLocalZ:number
}|null=null;
export function evaluate(frame:number,total:number,turnYaw?:number,dynamicMode=false):FrameStats {
 if(!Number.isInteger(frame)||frame<0||frame>total)throw Error('Invalid frame');
 cleanup();
 const t=dynamicMode||turnYaw===undefined?frame/24:0;
 const isTurnOnly=turnYaw!==undefined;
 // First 2 seconds perform complete 0°→360° rotation. Next the same
 // character raises a hand across the torso from behind to in front.
 const yaw=isTurnOnly?turnYaw!:t<=2?360*smooth(t/2):360;
 const reach=dynamicMode?smooth((t-.45)/1.8):smooth((t-2)/1.4);
 const fore=dynamicMode?smooth((t-3.0)/1.8):smooth((t-3.1)/1.1);
 const rootYaw=wrap(yaw),headLocalYaw=dynamicMode?26*Math.sin(t*1.24):
   (!isTurnOnly&&t>2)?38*Math.sin((t-2)*.85):0;
 // Real close-up of the *same character in the same take* exposes eye, face and hair quality.
 const closeup=dynamicMode?0:smooth((t-4.05)/1.08);
 const cameraScale=1-.67*closeup;
 camera.left=-4.7*cameraScale;camera.right=4.7*cameraScale;
 camera.top=2.64*cameraScale;camera.bottom=-2.64*cameraScale;
 const eyeLevel=lerp(1.95,3.02,closeup);
 camera.position.set(0,eyeLevel,15);camera.lookAt(0,eyeLevel,0);
 camera.updateProjectionMatrix();
 const headYaw=rootYaw+headLocalYaw;
 const lightAngle=dynamicMode?-1.3:-1.3+t*.7,shadowShift=Math.sin(lightAngle)*.18;
 const blink=Math.exp(-Math.pow((t-4.83)*11,2));
 const rootChest=transform(V(0,1.96,0),rootYaw),rootHead=transform(V(0,3.02,.0),rootYaw);
 const lookHead=(p:THREE.Vector3)=>rootHead.clone().add(transform(p,headYaw));
 // These are the matrices actually used for rigid head/root attachment.
 // IK-generated forearm receives its own bone transform below.
 const bodyMatrix=new THREE.Matrix4().makeRotationY(rootYaw*DEG);
 const headMatrix=new THREE.Matrix4().makeTranslation(rootHead.x,rootHead.y,rootHead.z)
   .multiply(new THREE.Matrix4().makeRotationY(headYaw*DEG));
 qaBindings.clear();
 for(const part of defs){
   if(part.role==='body')qaBindings.set(part.id,{local:part.anchor,world:bodyMatrix,boneId:'pelvisBone'});
   else if(part.role==='head')qaBindings.set(part.id,{local:part.anchor,world:headMatrix,boneId:'headBone'});
 }
 qaBindings.set('leftArm',{local:V(-.57,1.75,.03),world:bodyMatrix,boneId:'leftArmElbow'});
 qaBindings.set('leftLeg',{local:V(-.22,.47,.09),world:bodyMatrix,boneId:'leftLegRoot'});
 qaBindings.set('rightLeg',{local:V(.22,.47,.09),world:bodyMatrix,boneId:'rightLegRoot'});
 camera.updateMatrixWorld();
 // Back hair and legs behind the body, based on actual 3D anchor.
 artMesh(defs[0],lookHead(defs[0].anchor),headYaw);
 const steps=dynamicMode?.055*Math.sin(t*2.5):
   !isTurnOnly&&t>2?Math.sin(t*5)*.07:0;
 const dynamicFeet:{left:number[];right:number[]}={left:[],right:[]};
 for(const [i,id] of [[10,'leftLeg'],[11,'rightLeg']] as const){
  const x=i===10?-.22:.22,hip=transform(V(x,1.1,0),rootYaw);
  const knee=transform(V(x+steps*(i===10?1:-1),.62,.01),rootYaw);
  const foot=transform(V(x,.12,.18),rootYaw);
  if(i===10)dynamicFeet.left=foot.toArray();
  else dynamicFeet.right=foot.toArray();
  limb(hip,knee,.12,'#465c8a',defs[i].id);limb(knee,foot,.108,'#dcbeb2',defs[i].id);
  artMesh(defs[i],V((hip.x+foot.x)/2,.47,(hip.z+foot.z)/2),rootYaw,.78,.65);
 }
 artMesh(defs[1],rootChest,rootYaw);
 artMesh(defs[2],transform(defs[2].anchor,rootYaw),rootYaw);
 artMesh(defs[6],transform(defs[6].anchor,rootYaw),rootYaw);
 artMesh(defs[7],transform(defs[7].anchor,rootYaw),rootYaw);
 // Left arm always follows a world-space joint chain.
 const leftShoulder=transform(defs[8].anchor,rootYaw),
 leftElbow=transform(V(-.57,1.75,.03),rootYaw),
 leftHand=transform(V(-.54,1.35,.09),rootYaw);
 limb(leftShoulder,leftElbow,.133,'#526f9d','leftArm');limb(leftElbow,leftHand,.10,'#e4b9a6','leftArm');
 artMesh(defs[8],V(leftElbow.x,leftElbow.y,leftElbow.z),rootYaw,.85,.6);
 // Right arm uses full 3D IK. Its hand moves across the body *and* through
 // both sides of the torso depth plane.
 const shoulder=transform(defs[9].anchor,rootYaw);
 const resting=transform(V(.58,1.33,.11),rootYaw);
 const behind=transform(V(-.18,2.07,-.60),rootYaw);
 const ahead=transform(V(-.18,2.07,.68),rootYaw);
 const target=resting.clone().lerp(behind,reach).lerp(ahead,fore);
 const rig=solveIK(shoulder,target,.63,.63,transform(V(.10,-.15,.90),rootYaw));
 lastDynamicPose=dynamicMode?{
   reach,fore,headLocalYaw,shoulderXYZ:shoulder.toArray(),elbowXYZ:rig.elbow.toArray(),
   handXYZ:rig.hand.toArray(),targetXYZ:target.toArray(),
   handDistance:rig.hand.distanceTo(target),
   footLXYZ:dynamicFeet.left,footRXYZ:dynamicFeet.right,
   poseTime:t,
   handTorsoLocalZ:(rig.hand.z-rootChest.z)*Math.cos(rootYaw*DEG)+(rig.hand.x-rootChest.x)*Math.sin(rootYaw*DEG)
 }:null;
 const forearm=rig.hand.clone().sub(rig.elbow);
 const armLocalYaw=wrap(Math.atan2(forearm.x,forearm.z)/DEG);
 limb(shoulder,rig.elbow,.145,'#526f9d','rightArm');
 limb(rig.elbow,rig.hand,.102,'#eec3ac','rightArm');
 const forearmCenter=rig.elbow.clone().add(rig.hand).multiplyScalar(.5);
 const forearmAxis=rig.hand.clone().sub(rig.elbow).normalize();
 const forearmQuat=new THREE.Quaternion().setFromUnitVectors(V(0,-1,0),forearmAxis);
 const forearmBone=new THREE.Matrix4().compose(forearmCenter,forearmQuat,V(1,1,1));
 qaBindings.set('rightArm',{local:V(0,0,0),world:forearmBone,boneId:'rightForearmIK'});
 artMesh(defs[9],forearmCenter,armLocalYaw,.90,.39);
 // Character neck and face use head-local view, *not* world body yaw.
 artMesh(defs[3],lookHead(defs[3].anchor),headYaw);
 const face=lookHead(defs[3].anchor);
 const faceVisibility=sample(defs[3],headYaw).visible;
 const faceShadowOpacity=.27*Math.pow(faceVisibility,3);
 // Face paint, face-specific shadow and hair-cast shadow MUST share the
 // same view-visibility envelope. Otherwise a fading side face leaves a
 // full-opacity gray shadow "ghost" around ~80° while the head turns.
 if(faceVisibility>.001){
   canvasLight(face.x,face.y,face.z+.12,shadowShift,faceShadowOpacity);
   polygon([V(face.x-.29,face.y+.29,face.z+.16),V(face.x+.22,face.y+.30,face.z+.16),
      V(face.x+.13+shadowShift,face.y+.08,face.z+.16)],'#584968',.17*faceVisibility);
 }
 const eyes=lookHead(defs[5].anchor);
 artMesh(defs[5],eyes,headYaw,1,1,1-.95*blink);
 // The eyes and eyeliner are painted into the transparent eye ArtMesh layer.
 // Vertex compression above produces blink; avoid duplicated procedural eyes.
 artMesh(defs[4],lookHead(defs[4].anchor),headYaw);
 // Occasional light streak crosses face. Arm-cast shadow only while in front.
 if(rig.hand.z>rootChest.z+.15 && reach>.2){
  const x=(rig.hand.x+rootChest.x)/2;
  polygon([V(x-.20,2.30,.52),V(x+.07,2.30,.52),
    V(x+.30,1.60,.52),V(x,1.60,.52)],'#273758',.17);
 }
 if(!isTurnOnly&&t>3.5&&!dynamicMode)glint(t);
 // Floor/horizon is a scene effect, not a body part.
 polygon([V(-4.7,.03,-4),V(4.7,.03,-4),V(4.7,0,-4),V(-4.7,0,-4)],'#60718a');
 renderer.render(scene,camera);
 if(isTurnOnly){
   const bounds:[number,number,number,number]=[0,0,960,540]; // replaced by pixel readback bounds when available
   qaRecorder.finish({
     camera,timeSeconds:frame/24,yaw,bounds,rendererCommit:'runtime-main-qa-instrumented',
     poseHash:dynamicMode?'dynamic-pose:'+frame+':'+headLocalYaw.toFixed(5)+':'+reach.toFixed(5)+':'+fore.toFixed(5):'static-neutral-pose'
   });
 }
 const result:FrameStats={
   frame,time:t,yaw,headLocalYaw,partCount:defs.length,keyViewCount:4,
   artMeshCount:drawn.filter(o=>o instanceof THREE.Mesh).length,
   ikError:rig.error,handMinusTorsoDepth:rig.hand.z-rootChest.z,
   armLocalYaw,lightAngle,shadowOffset:shadowShift,blink,
   targetX:target.x,handX:rig.hand.x,faceVisibility,faceShadowOpacity
 };
 return result;
}
window.renderIntegrated=evaluate;
window.renderTurn360=(yaw,frameIndex)=>{
 if(!Number.isFinite(yaw))throw Error('Invalid yaw');
 qaRecorder.start(yaw,frameIndex);
 const stats=evaluate(Math.min(frameIndex,192),192,yaw);
 if(!qaRecorder.lastFrame)throw Error('No real frame evidence');
 return {stats,trace:qaRecorder.lastFrame};
};
window.renderDynamic360=(yaw,frameIndex)=>{
 if(!Number.isFinite(yaw)||frameIndex<0||frameIndex>192)throw Error('Invalid dynamic turn frame');
 qaRecorder.start(yaw,frameIndex);
 const stats=evaluate(frameIndex,192,yaw,true);
 if(!qaRecorder.lastFrame||!lastDynamicPose)throw Error('No dynamic frame evidence');
 return {stats,trace:qaRecorder.lastFrame,pose:lastDynamicPose};
};
window.auditTurnOcclusion=()=>auditLocalOcclusion(renderer,scene,camera,drawn,qaRecorder.yaw);
window.turnSourceViews={
 angles:[0,90,180,270],
 independent270:PART_IDS.every(id=>LEFT_CONTOURS[id]?.length===11),
 derivedPartIds:PART_IDS.filter(id=>!LEFT_CONTOURS[id]),
 authoredGeometry:defs.map(p=>({
   id:p.id,
   right:p.keys[1].contour,
   left:p.keys[3].contour,
   rightVDD:p.keys[1].shift,
   leftVDD:p.keys[3].shift
 }))
};
window.captureTurnPass=(pass,includeImage)=>{
 if(!qaRecorder.lastFrame)throw Error('Must render a real turn frame first');
 const width=includeImage?480:240,height=includeImage?270:135;
 const target=new THREE.WebGLRenderTarget(width,height,{depthBuffer:true,stencilBuffer:false});
 const color=pass==='mask'?[255,255,255] as const:undefined;
 const restore:{mesh:THREE.Mesh;mat:THREE.Material;visible:boolean}[]=[];
 for(const obj of drawn)if(obj instanceof THREE.Mesh){
   const pid=obj.userData.partId as PartId|null;
   if(Array.isArray(obj.material))continue;
   const original=obj.material;
   restore.push({mesh:obj,mat:original,visible:obj.visible});
   if(pid&&PART_IDS.includes(pid)){
     const rgb=color??qaPalette[PART_IDS.indexOf(pid)];
     obj.material=idShader(original,rgb,pass==='depth');
   }else obj.visible=false;
 }
 const oldColor=renderer.getClearColor(new THREE.Color()).clone();
 const oldAlpha=renderer.getClearAlpha();
 const pixels=new Uint8Array(width*height*4);
 let measuredBounds:readonly [number,number,number,number]|undefined;
 let result:{counts:Record<string,number>;dataUrl?:string;bounds?:readonly [number,number,number,number]};
 try{
   renderer.setRenderTarget(target);
   renderer.setClearColor(0x000000,1);
   renderer.render(scene,camera);
   renderer.readRenderTargetPixels(target,0,0,width,height,pixels);
   const counts=countIdPixels(pixels,PART_IDS,(960*540)/(width*height));
   if(pass==='id'){
     let x0=width,y0=height,x1=-1,y1=-1;
     for(let y=0;y<height;y++)for(let x=0;x<width;x++){
       const p=(y*width+x)*4;
       if(pixels[p]!==0||pixels[p+1]!==0||pixels[p+2]!==0){
         x0=Math.min(x0,x);x1=Math.max(x1,x);
         y0=Math.min(y0,y);y1=Math.max(y1,y);
       }
     }
     const bounds:[number,number,number,number]=x1<0?[0,0,0,0]:
       [x0*960/width,(height-1-y1)*540/height,
        (x1+1)*960/width,(height-y0)*540/height];
     qaRecorder.updateVisible(counts,bounds);
     measuredBounds=bounds;
   }
   result={counts:Object.fromEntries(counts),bounds:measuredBounds};
   if(includeImage){
     const cv=document.createElement('canvas');cv.width=width;cv.height=height;
     const ctx=cv.getContext('2d');if(!ctx)throw Error('QA pass canvas unavailable');
     const corrected=new Uint8ClampedArray(pixels.length);
     for(let y=0;y<height;y++){
       corrected.set(pixels.subarray((height-y-1)*width*4,(height-y)*width*4),y*width*4);
     }
     ctx.putImageData(new ImageData(corrected,width,height),0,0);
     result.dataUrl=cv.toDataURL('image/png');
   }
 }finally{
   renderer.setRenderTarget(null);renderer.setClearColor(oldColor,oldAlpha);
   for(const saved of restore){
     if(saved.mesh.material!==saved.mat){const m=saved.mesh.material;if(Array.isArray(m))m.forEach(x=>x.dispose());else m.dispose();}
     saved.mesh.material=saved.mat;saved.mesh.visible=saved.visible;
   }
   target.dispose();
   renderer.render(scene,camera);
 }
 return result;
};
window.integratedInfo={parts:defs.length,views:4,method:'4 registered transparent RGBA key images / part + fixed UV ArtMesh + VDD + 3D IK + occlusion + animated art shadow'};
window.integratedArtProof=artTextureProof(defs[3]);
window.exportArtPNG=(partId,angle)=>{
 const part=defs.find(p=>p.id===partId);if(!part)throw Error('unknown part '+partId);
 return artTexturePNG(part,angle);
};
evaluate(0,144);
