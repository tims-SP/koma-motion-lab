import * as THREE from 'three';

/**
 * MVP-002: a single, deliberately tiny 2.75D character.
 * Original authored vector "key art", NOT a textured commercial anime model.
 * Four keyed view-shapes -> per-part interpolation -> anchor projection + VDD
 * -> articulated arm/leg IK -> local visibility -> stylized light/FX.
 */
type Shot = 'turn' | 'action' | 'fx';
type Form = { width: number; shift: number; depth: number; visible: number };
type KeyForm = [Form, Form, Form, Form];
type Vec = { x: number; y: number };
type Vec3 = { x: number; y: number; z: number };
const canvas = document.querySelector<HTMLCanvasElement>('#viewport');
if (!canvas) throw new Error('Missing canvas');
const size = { width: 960, height: 540 };
const renderer = new THREE.WebGLRenderer({ canvas, antialias:true, alpha:false, preserveDrawingBuffer:true });
renderer.setPixelRatio(1);
renderer.setSize(size.width,size.height,false);
renderer.setClearColor(0x11192b);
renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-4.8,4.8,2.7,-2.7,0.1,40);
camera.position.set(0,2.0,12);
camera.lookAt(0,2.0,0);
const layer = new THREE.Group();
scene.add(layer);
const ink = new THREE.LineBasicMaterial({ color:'#273049', transparent:true, opacity:.9, depthTest:false });
const materials=new Map<string,THREE.MeshBasicMaterial>();
const key=yaw => (Math.floor((((yaw%360)+360)%360)/90) % 4);
const clamp=(v:number,a:number,b:number)=>Math.min(b,Math.max(a,v));
const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const mod=(x:number)=>(x%360+360)%360;
const sin=(x:number)=>Math.sin(x);
const cos=(x:number)=>Math.cos(x);
const v=(x:number,y:number):Vec=>({x,y});
const WIDTHS:Record<string,number[]> = {
  face:[1,.58,0,.58], backHair:[1,.79,1.1,.79], fringe:[1,.73,0,.73],
  torso:[1,.64,1,.64], skirt:[1,.69,1,.69], collar:[1,.6,0,.6],
  eye:[1,.62,0,.62], shoe:[1,.75,1,.75], arm:[1,.77,1,.77],
  leg:[1,.76,1,.76], default:[1,.8,1,.8]
};
const DEPTH:Record<string,number[]> = {
 face:[0.28,0.2,-.4,0.2], backHair:[-.15,.3,.58,.3],
 fringe:[.45,.36,-.3,.36], torso:[0,.08,.18,.08], skirt:[.1,.08,.16,.08],
 collar:[.2,.11,-.2,.11],eye:[.55,.40,-.3,.40],
 default:[0,0,0,0]
};
const SHOW:Record<string,number[]> = {
 face:[1,1,0,1],fringe:[1,1,0,1],eye:[1,1,0,1],
 collar:[1,.75,0,.75],default:[1,1,1,1]
};
const SHIFT:Record<string,number[]> = {
  face:[0,.10,0,-.10], fringe:[0,.1,0,-.1],
  eye:[0,.11,0,-.11],collar:[0,.07,0,-.07],default:[0,0,0,0]
};
function form(type:string,yaw:number):Form {
  const y=mod(yaw), a=Math.floor(y/90)%4, b=(a+1)%4, t=(y%90)/90;
  const arr=(rec:Record<string,number[]>)=>rec[type]??rec.default;
  const get=(rec:Record<string,number[]>)=>{const r=arr(rec);return lerp(r[a],r[b],t);};
  return {width:get(WIDTHS),shift:get(SHIFT),depth:get(DEPTH),visible:get(SHOW)};
}
function project(anchor:Vec3,yaw:number):Vec {
  const r=yaw*Math.PI/180;
  return v(anchor.x*cos(r)+anchor.z*sin(r),anchor.y);
}
function paint(color:string,opacity=1):THREE.MeshBasicMaterial {
  const k=color+':'+Math.round(opacity*100);
  let m=materials.get(k);
  if(!m){m=new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide,transparent:opacity<.999,opacity,depthWrite:false,depthTest:false});materials.set(k,m);}
  return m;
}
function shape(points:Vec[],color:string,z:number,opacity=1,outline=true):void {
  if(opacity<.015||points.length<3)return;
  const outlineShape=new THREE.Shape();
  outlineShape.moveTo(points[0].x,points[0].y);
  for(let i=1;i<points.length;i++)outlineShape.lineTo(points[i].x,points[i].y);
  outlineShape.closePath();
  const geo=new THREE.ShapeGeometry(outlineShape);
  const mesh=new THREE.Mesh(geo,paint(color,opacity));
  mesh.position.z=z;mesh.renderOrder=Math.round(z*100);
  layer.add(mesh);
  if(outline){
    const lineGeo=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(p.x,p.y,0)));
    const line=new THREE.LineLoop(lineGeo,ink);
    line.position.z=z+.002;line.renderOrder=Math.round(z*100)+1;
    layer.add(line);
  }
}
function ellipse(x:number,y:number,w:number,h:number,color:string,z:number,opacity=1,outline=true,chin=0):void {
  const pts:Vec[]=[];
  for(let i=0;i<20;i++){const a=(i/20)*Math.PI*2; const lower=sin(a)<0;
    pts.push(v(x+w*cos(a)*(lower?(1-chin*.2):1),y+h*sin(a)- (lower?chin*(1-Math.abs(cos(a)))*.12:0)));
  }
  shape(pts,color,z,opacity,outline);
}
function polygonRaw(coords:number[][],color:string,z:number,opacity=1,outline=true):void {
 shape(coords.map(p=>v(p[0],p[1])),color,z,opacity,outline);
}
function bone(from:Vec,to:Vec,width:number,color:string,z:number,outline=true):void {
 const dx=to.x-from.x,dy=to.y-from.y,len=Math.hypot(dx,dy)||.001;
 const nx=dy/len*width/2,ny=-dx/len*width/2;
 shape([v(from.x+nx,from.y+ny),v(to.x+nx,to.y+ny),v(to.x-nx,to.y-ny),v(from.x-nx,from.y-ny)],color,z,1,outline);
 ellipse(to.x,to.y,width*.55,width*.55,color,z+.003,1,false);
}
function ik(shoulder:Vec,target:Vec,len1:number,len2:number,side=1):{elbow:Vec;hand:Vec}{
 const vx=target.x-shoulder.x,vy=target.y-shoulder.y;
 const len=clamp(Math.hypot(vx,vy),.01,len1+len2-.001);
 const nx=vx/(Math.hypot(vx,vy)||1), ny=vy/(Math.hypot(vx,vy)||1);
 const d=(len1*len1-len2*len2+len*len)/(2*len);
 const h=Math.sqrt(Math.max(0,len1*len1-d*d));
 const elbow=v(shoulder.x+nx*d-side*ny*h,shoulder.y+ny*d+side*nx*h);
 return {elbow, hand:v(shoulder.x+nx*len,shoulder.y+ny*len)};
}
function clearFrame():void {
  for(const child of [...layer.children]){
    layer.remove(child);
    if(child instanceof THREE.Mesh||child instanceof THREE.Line)child.geometry.dispose();
  }
}
function part(type:string,anchor:Vec3,sizeXY:Vec,yaw:number,color:string,baseZ:number,opacity=1,chin=0):Vec {
 const f=form(type,yaw),p=project(anchor,yaw);
 p.x+=f.shift;ellipse(p.x,p.y,sizeXY.x*f.width,sizeXY.y,color,baseZ+f.depth,opacity*f.visible,true,chin);
 return p;
}
function sparkle(x:number,y:number,r:number,z:number,color:string):void{
 polygonRaw([[x-r,y],[x,y+r*.5],[x+r,y],[x,y-r*.5]],color,z,.8,false);
 polygonRaw([[x-r*.3,y-r*.3],[x+r*.3,y+r*.3],[x+r*.3,y-r*.3],[x-r*.3,y+r*.3]],color,z,.35,false);
}
function actor(yaw:number,walk:number,reach:number,expr:number,light:number):Record<string,number>{
 const a=yaw*Math.PI/180, sx=sin(a), cz=cos(a), front=clamp((cz+.2)/.6,0,1);
 const pelvis=v(0,.98),neck=v(.035*sx,2.45+walk*.018);
 const torso=part('torso',{x:0,y:1.88,z:0},v(.47,.61),yaw,'#50628d',.16,1);
 // Back hair must appear behind the face, but ahead of neck in the rear.
 const backHead=part('backHair',{x:0,y:2.99,z:-.15},v(.52,.7),yaw,'#2f3459',.30);
 for(let side of [-1,1]) {
   const hip=project({x:.22*side,y:.99,z:0},yaw);
   const knee=v(hip.x+walk*.12*side,.58+Math.max(0,walk*side)*.19);
   const foot=v(hip.x+walk*.21*side,.13+Math.max(0,walk*side)*.10);
   bone(hip,knee,.29*form('leg',yaw).width,'#56618a',.25);
   bone(knee,foot,.23*form('leg',yaw).width,'#eac4b2',.26);
   ellipse(foot.x+.075*sx,foot.y,.27*form('shoe',yaw).width,.125,'#2a2f50',.3);
 }
 // Torso volumes and jacket panels are independent of all limbs.
 part('torso',{x:-.17,y:1.93,z:.15},v(.26,.49),yaw,'#718ab8',.35);
 part('torso',{x:.17,y:1.93,z:.15},v(.26,.49),yaw,'#718ab8',.35);
 part('collar',{x:0,y:2.24,z:.21},v(.20,.23),yaw,'#f7eadc',.50);
 const chest=project({x:0,y:2.15,z:.3},yaw);
 if(front>.1){
   polygonRaw([[chest.x-.16*front,2.18],[chest.x+.16*front,2.18],[chest.x,1.94]],'#eac8d2',.59,front);
   polygonRaw([[chest.x-.10*front,2.16],[chest.x+.10*front,2.16],[chest.x+.03,1.98],[chest.x-.03,1.98]],'#ad5366',.62,front);
 }
 const skirt=part('skirt',{x:0,y:1.22,z:0},v(.54,.35),yaw,'#333e6e',.32);
 for(let s=-2;s<=2;s++){
   const x=skirt.x+s*.17*form('skirt',yaw).width;
   bone(v(x,1.37),v(x+s*.025,1.08),.014,'#7991bd',.52,false);
 }
 const target=v(1.31+.15*sin(reach*Math.PI),2.10+.06*cos(reach*Math.PI));
 let reachError=0;
 for(let side of [-1,1]){
   const shoulder=project({x:side*.47,y:2.31,z:.02},yaw);
   const hanging=v(shoulder.x+side*.08,1.35);
   const armTarget=(side===1&&reach>.1)?v(lerp(hanging.x,target.x,reach),lerp(hanging.y,target.y,reach)):hanging;
   const joints=ik(shoulder,armTarget,.54,.53,side===1?-1:1);
   bone(shoulder,joints.elbow,.26*form('arm',yaw).width,'#536998',.48);
   bone(joints.elbow,joints.hand,.205*form('arm',yaw).width,'#f1c7b0',.50);
   ellipse(joints.hand.x,joints.hand.y,.125,.145,'#f4cfbb',.61);
   if(side===1&&reach>.9)reachError=Math.hypot(joints.hand.x-target.x,joints.hand.y-target.y);
 }
 // Hair, face and features use per-part cyclic view keys and VDD offsets.
 const headY=3.03+.07*sin(walk*2);
 const faceAnchor={x:0,y:headY,z:.16};
 const fp=part('face',faceAnchor,v(.44,.53),yaw,'#f6cdb9',.67,1,.6);
 // Vector "face shadow mask": explicit art-directed 2D shape, not physical PBR.
 if(front>.08 && light>0){
    const edge=fp.x+lerp(-.36,.32,light)*form('face',yaw).width;
    polygonRaw([[edge,headY+.32],[fp.x+.38*form('face',yaw).width,headY+.30],
      [fp.x+.29*form('face',yaw).width,headY-.36],[edge-.05,headY-.37]],
      '#d8a8ad',.696,front*.43,false);
 }
 // Nose, eyes, brows, mouth are their own drawables, not baked into a face sprite.
 const profile=Math.sign(sx||1);
 for(const side of [-1,1]){
   const lateral=side*.18*form('face',yaw).width;
   let vis=front*(side*sx>.65?.35:1);
   const eyeX=fp.x+lateral+.02*profile*Math.abs(sx);
   ellipse(eyeX,headY+.06,.066*form('eye',yaw).width,.115,'#edf0ff',.73,vis);
   ellipse(eyeX+.008,headY+.048,.037*form('eye',yaw).width,.085,'#426b92',.745,vis);
   ellipse(eyeX+.019,headY+.087,.013,.025,'#ffffff',.76,vis,false);
   bone(v(eyeX-.055,headY+.213),v(eyeX+.052,headY+.225-expr*.03),.027,'#333c5d',.75,false);
 }
 if(front>.02){
   const blink=clamp(1-expr,0,1);
   if(blink>.01){
     bone(v(fp.x-.26*form('face',yaw).width,headY+.10),
          v(fp.x-.10*form('face',yaw).width,headY+.11),.03*blink,'#283653',.764,false);
   }
   ellipse(fp.x+.03*sx,headY-.19,.10+expr*.018,.024+expr*.041,'#aa566d',.75,front,false);
 }
 const hairY=headY+.34;
 const fringeCenter=part('fringe',{x:0,y:hairY,z:.22},v(.47,.255),yaw,'#373c68',.86);
 for(let i=-2;i<=2;i++){
   const x=fringeCenter.x+i*.15*form('fringe',yaw).width;
   polygonRaw([[x-.12,hairY+.07],[x+.06,hairY+.10],[x-.09+i*.012,hairY-.30-.035*(i%2)]],
     '#32385f',.90,form('fringe',yaw).visible);
 }
 for(let side of [-1,1]){
   const x=fringeCenter.x+side*.44*form('fringe',yaw).width;
   polygonRaw([[x-.09,hairY+.1],[x+.10,hairY+.1],[x+.12*side,headY-.42]],'#313858',.82,Math.max(.1,form('fringe',yaw).visible));
 }
 // Hair highlights and a deliberately asymmetric accessory prove no mirroring shortcut.
 bone(v(fringeCenter.x-.25,hairY+.16),v(fringeCenter.x+.22,hairY+.18),.018,'#7a84b8',.97,false);
 const ribbonX=project({x:-.45,y:headY+.35,z:.20},yaw).x;
 ellipse(ribbonX,headY+.36,.11,.075,'#e38a9d',1.02,clamp((1+cz)/2,.1,1));
 sparkle(ribbonX,headY+.37,.055,1.03,'#ffe4e9');
 return {reachError, yaw};
}
function effects(time:number,shot:Shot):void {
 if(shot==='turn') return;
 const n=shot==='fx'?28:10;
 for(let i=0;i<n;i++){
   const x=(sin(i*41.23+time*(shot==='fx'?1.2:.8))*1.7);
   const y=1.35+((i*.38+time*.55)%2.2);
   const radius=.025+.035*(.5+.5*sin(i*2+time));
   sparkle(x,y,radius,2.2,i%3===0?'#f1c0da':'#9ddff4');
 }
 if(shot==='action'){
   ellipse(1.36,2.10,.12+.07*sin(time*5),.12+.07*sin(time*5),'#88e0f2',2.0,.6,false);
 }
}
function backdrop(time:number,shot:Shot):void {
 // Simple proof of scene compositing and per-shot camera/state, not final scenery.
 for(let i=0;i<14;i++){
   const x=-4.8+i*.7, h=.2+.3*(.5+.5*sin(i*2.1));
   polygonRaw([[x,0.0],[x+.7,0],[x+.7,h],[x,h]],'#1b2a41',-5,1,false);
 }
 bone(v(-4.8,.03),v(4.8,.03),.024,'#3c526e',-3,false);
 if(shot==='fx'){
   const theta=.6+time*.8;
   const lx=2.5*cos(theta),ly=2.7+sin(theta);
   ellipse(lx,ly,.37,.37,'#aac8e8',-4,.3,false);
 }
}
function renderFrame(shot:Shot,frame:number,frames:number):Record<string,unknown>{
 if(!(['turn','action','fx'] as string[]).includes(shot)||!Number.isInteger(frame)||frame<0||frame>frames)throw Error('bad frame request');
 clearFrame();
 const progress=frame/frames, time=progress*4;
 const yaw=shot==='turn'?progress*360:shot==='action'?lerp(0,85,progress):lerp(-22,28,progress);
 const walking=shot==='action'?sin(progress*Math.PI*2)*.8:0;
 const reaching=shot==='action'?clamp((progress-.18)*2.5,0,1):0;
 const expression=shot==='fx'?(Math.exp(-Math.pow((progress-.37)*14,2))*.95):0;
 const light=shot==='fx'?.5+.5*sin(time*2):0;
 if(shot==='fx'){
   camera.left=-2.40;camera.right=2.40;camera.top=1.35;camera.bottom=-1.35;
   camera.position.set(0,3.02,12);camera.lookAt(0,3.02,0);camera.updateProjectionMatrix();
 }else{
   camera.left=-4.8;camera.right=4.8;camera.top=2.7;camera.bottom=-2.7;
   camera.position.set(0,2.0,12);camera.lookAt(0,2.0,0);camera.updateProjectionMatrix();
 }
 backdrop(time,shot);
 const data=actor(yaw,walking,reaching,expression,light);
 effects(time,shot);
 renderer.render(scene,camera);
 return {shot,frame,frames,yaw,partCount:layer.children.length,reachError:data.reachError,
         core:'part-level-keyviews+anchor-vdd+IK+visibility+art-shadow'};
}
window.demoRender=renderFrame;
window.demoInfo={quality:'technical stylized vector proxy, not licensed or photoreal final anime art',
                keyViewDegrees:[0,90,180,270],renderWidth:size.width,renderHeight:size.height};
renderFrame('turn',0,72);
declare global {interface Window {
 demoRender:(shot:Shot,frame:number,frames:number)=>Record<string,unknown>;
 demoInfo:Record<string,unknown>;
}}
