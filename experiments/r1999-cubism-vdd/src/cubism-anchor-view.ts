import * as THREE from 'three';
import {proxyLayerForPart,runtimeFacePivot,createProxyControls} from './view-proxy';

/** Native Cubism Drawable -> Three.js render-pass adapter; private model data stay in browser memory. */
type CubismModel = any;
type Source = {
  renderer: THREE.WebGLRenderer;
  mesh: THREE.Mesh;
  material: THREE.ShaderMaterial;
  geometry: THREE.BufferGeometry;
  index: number;
  proxy: ReturnType<typeof proxyLayerForPart>;
  maskIndices: number[];
  key: string;
};
const viewSize = 640;
const roots = {native: null as HTMLCanvasElement | null, adapter: null as HTMLCanvasElement | null};
const objects: Source[] = [];
let diagnosticFault: "none" | "mask" | "order" | "uv" = "none";
let cameraYawDeg=0;
let headPivot:readonly [number,number]=[0,0];
let activePartFilter:Set<number>|null=null;
function setYaw(value:number){if(!Number.isFinite(value)||value<0||value>90)throw Error('Yaw 0..90 required');cameraYawDeg=value;return cameraYawDeg;}
let app: THREE.WebGLRenderer;
let model: CubismModel;
let textures: THREE.Texture[] = [];
const screenScene = new THREE.Scene();
const unitCamera = new THREE.Camera();
unitCamera.projectionMatrix.identity();
unitCamera.matrixWorldInverse.identity();
unitCamera.matrixWorld.identity();
const maskCache = new Map<string,{target: THREE.WebGLRenderTarget,scene:THREE.Scene}>();
const vs = `
precision highp float;
uniform mat4 uMvp;
uniform float uYaw;
uniform float uDepth;
uniform float uInfluence;
uniform vec2 uPivot;
varying vec2 vUv;
void main(){
 vUv=uv;
 vec2 p=position.xy;
 if(abs(uYaw)>0.000001 && uInfluence>0.000001){
   float targetX=uPivot.x+(p.x-uPivot.x)*cos(uYaw)+uDepth*sin(uYaw);
   p.x=mix(p.x,targetX,uInfluence);
 }
 gl_Position=uMvp*vec4(p.xy,0.0,1.0);
}
`;
const fs = `
precision highp float;
uniform sampler2D uImage;
uniform sampler2D uMask;
uniform vec2 uResolution;
uniform float uOpacity;
uniform float uHasMask;
uniform float uInverted;
uniform float uMaskPass;
varying vec2 vUv;
void main(){
 vec4 tex=texture2D(uImage, vUv);
 float alpha=tex.a*uOpacity;
 if(uMaskPass>0.5) {
   gl_FragColor=vec4(0.0,0.0,0.0,alpha);
   return;
 }
 float cover=1.0;
 if(uHasMask>0.5) {
   cover=texture2D(uMask,gl_FragCoord.xy/uResolution).a;
   if(uInverted>0.5)cover=1.0-cover;
 }
 gl_FragColor=vec4(tex.rgb*(uOpacity*cover),alpha*cover);
}
`;

function sourceGeometry(i:number):THREE.BufferGeometry {
  const vertices=model.getDrawableVertexPositions(i);
  const uvs=model.getDrawableVertexUvs(i);
  const positions=new Float32Array(vertices.length/2*3);
  for(let k=0;k<vertices.length/2;k++){positions[k*3]=vertices[k*2];positions[k*3+1]=vertices[k*2+1];}
  const geom=new THREE.BufferGeometry();
  geom.setAttribute('position',new THREE.BufferAttribute(positions,3));
  geom.setAttribute('uv',new THREE.BufferAttribute(new Float32Array(uvs),2));
  geom.setIndex(Array.from(model.getDrawableVertexIndices(i)));
  return geom;
}
function material(texture:THREE.Texture,hasMask:boolean,inverted:boolean,maskPass:boolean){
 return new THREE.ShaderMaterial({
  vertexShader:vs,fragmentShader:fs,
  uniforms:{uMvp:{value:new THREE.Matrix4()},uImage:{value:texture},
    uYaw:{value:0},uDepth:{value:0},uInfluence:{value:0},uPivot:{value:new THREE.Vector2()},
    uMask:{value:null},uResolution:{value:new THREE.Vector2(viewSize,viewSize)},
    uOpacity:{value:1},uHasMask:{value:hasMask?1:0},
    uInverted:{value:inverted?1:0},uMaskPass:{value:maskPass?1:0}},
  transparent:true,depthTest:false,depthWrite:false,side:THREE.DoubleSide,
  blending:THREE.CustomBlending,blendSrc:THREE.OneFactor,
  blendDst:THREE.OneMinusSrcAlphaFactor,blendEquation:THREE.AddEquation,
  blendSrcAlpha:THREE.OneFactor,blendDstAlpha:THREE.OneMinusSrcAlphaFactor,
  toneMapped:false
 });
}
function updateGeo(geom:THREE.BufferGeometry,i:number) {
  const verts=model.getDrawableVertexPositions(i);
  const pos=geom.getAttribute('position') as THREE.BufferAttribute;
  for(let j=0;j<verts.length/2;j++) {
   pos.setXYZ(j,verts[j*2],verts[j*2+1],0);
  }
  pos.needsUpdate=true;
}
function inspect(){
 const mvp=model && window && (window as any).__R1999_MODEL?.getRenderer?.()?.getMvpMatrix?.()?.getArray?.();
 return {ready:!!model,drawables:objects.length,masks:maskCache.size,diagnosticFault,
   cameraYawDeg,provenance:cameraYawDeg===0?'NATIVE_ART':'ESTIMATED_GEOMETRIC_PROXY',
   authored45:false,authored90:false,headPivot,
   filteredPartIndices:activePartFilter?[...activePartFilter]:null,
   mvp:mvp?Array.from(mvp):null};
}
async function begin(){
 const privateModel=(window as any).__R1999_MODEL;
 if(!privateModel?.getModel?.()) return;
 model=privateModel.getModel();
 headPivot=runtimeFacePivot(model);
 const original=document.querySelector<HTMLCanvasElement>('canvas');
 if(!original) return;
 roots.native=original;
 const wrapper=document.createElement('section');
 wrapper.id='r1999-comparison';
 wrapper.innerHTML='<div class="r1999-heads"><span>Cubism Core · Native</span><span>Three.js · Adapter</span></div>';
 document.body.appendChild(wrapper);
 const canvas=document.createElement('canvas');
 canvas.id='r1999-three';
 roots.adapter=canvas;
 wrapper.appendChild(canvas);
 original.style.cssText='position:fixed;z-index:1;top:45px;left:0;width:640px;height:640px;object-fit:fill;';
 canvas.style.cssText='position:fixed;z-index:1;top:45px;left:640px;width:640px;height:640px;';
 const controls=document.querySelector<HTMLElement>('#r1999-panel');
 if(controls) controls.style.cssText='left:10px;top:700px;z-index:30;max-width:370px;width:370px;';
 const style=document.createElement('style');
 style.textContent=`body{margin:0;background:#202531;}#r1999-comparison{position:static}
 #r1999-comparison .r1999-heads{position:fixed;left:0;top:0;display:flex;width:1280px;height:45px;
 align-items:center;justify-content:space-around;color:#fff;background:#111925;
 font:600 15px/1.3 system-ui;z-index:3}
 @media(max-width:750px){#r1999-comparison .r1999-heads{font-size:12px}}`;
 document.head.appendChild(style);

 app=new THREE.WebGLRenderer({canvas,alpha:true,antialias:false,premultipliedAlpha:true,preserveDrawingBuffer:true});
 app.setPixelRatio(1);app.setSize(viewSize,viewSize,false);
 app.autoClear=false;
 app.outputColorSpace=THREE.LinearSRGBColorSpace;
 app.setClearColor(0x000000,0);
 const base='/Resources/302301_shisihangshi/textures/';
 const loader=new THREE.TextureLoader();
 const files=['302301_shisihangshi_00.png','302301_shisihangshi_01.png'];
 textures=await Promise.all(files.map(name=>new Promise<THREE.Texture>((resolve,reject)=>
   loader.load(base+name,t=>{t.flipY=true;t.premultiplyAlpha=true;t.colorSpace=THREE.NoColorSpace;
    t.minFilter=THREE.LinearMipmapLinearFilter;t.magFilter=THREE.LinearFilter;t.generateMipmaps=true;resolve(t);},undefined,reject))));
 const count=model.getDrawableCount(),maskCounts=model.getDrawableMaskCounts(),masks=model.getDrawableMasks();
 for(let i=0;i<count;i++){
  const geom=sourceGeometry(i),ids=Array.from(masks[i]??[]).slice(0,maskCounts[i]??0) as number[];
  const key=ids.join(',');
  const parentIndex=model.getDrawableParentPartIndex(i);
  const partId=parentIndex<0?'__UNPARENTED_DRAWABLES__':model.getPartId(parentIndex).getString().s;
  const drawableId=model.getDrawableId(i).getString().s;
  const proxy=proxyLayerForPart(partId,drawableId);
  const mat=material(textures[model.getDrawableTextureIndex(i)],ids.length>0,model.getDrawableInvertedMaskBit(i),false);
  mat.uniforms.uDepth.value=proxy.depth;
  mat.uniforms.uInfluence.value=proxy.influence;
  const mesh=new THREE.Mesh(geom,mat);
  mesh.frustumCulled=false;
  screenScene.add(mesh);
  objects.push({renderer:app,mesh,geometry:geom,material:mat,index:i,proxy,maskIndices:ids,key});
 }
 for(const source of objects.filter(o=>o.maskIndices.length)){
  if(maskCache.has(source.key))continue;
  const scene=new THREE.Scene();
  for(const idx of source.maskIndices){
   const original=objects[idx];
   const maskingMaterial=material(textures[model.getDrawableTextureIndex(idx)],false,false,true);
   maskingMaterial.uniforms.uDepth.value=original.proxy.depth;
   maskingMaterial.uniforms.uInfluence.value=original.proxy.influence;
   const maskingMesh=new THREE.Mesh(original.geometry,maskingMaterial);
   maskingMesh.frustumCulled=false;
   scene.add(maskingMesh);
  }
  const target=new THREE.WebGLRenderTarget(viewSize,viewSize,{format:THREE.RGBAFormat,
    type:THREE.UnsignedByteType,depthBuffer:false,stencilBuffer:false});
  target.texture.colorSpace=THREE.NoColorSpace;
  maskCache.set(source.key,{target,scene});
 }
 (window as any).__R1999_ADAPTER={inspect,getCanvases:()=>roots,renderOnce:render,setYaw,
  capturePart:(partIndex:number)=>{
   if(!Number.isInteger(partIndex)||partIndex<-1||partIndex>=model.getPartCount())throw Error('Invalid Part index');
   const previousYaw=cameraYawDeg,previousFilter=activePartFilter;
   cameraYawDeg=0;activePartFilter=new Set([partIndex]);
   try{
    render();
    const canvas=roots.adapter!;
    const ctx=document.createElement('canvas');ctx.width=canvas.width;ctx.height=canvas.height;
    const draw=ctx.getContext('2d',{willReadFrequently:true})!;draw.drawImage(canvas,0,0);
    const rgba=draw.getImageData(0,0,canvas.width,canvas.height).data;
    let nonzeroAlpha=0,opaquePixels=0,alphaMin=255,alphaMax=0;
    for(let i=3;i<rgba.length;i+=4){const a=rgba[i];if(a>0){nonzeroAlpha++;alphaMin=Math.min(alphaMin,a);alphaMax=Math.max(alphaMax,a);if(a===255)opaquePixels++;}}
    return {partIndex,nonzeroAlpha,opaquePixels,alphaMin:nonzeroAlpha?alphaMin:0,
      alphaMax,dataUrl:canvas.toDataURL('image/png'),provenance:'CUBISM_NATIVE_FRONT_PART_SNAPSHOT'};
   }finally{cameraYawDeg=previousYaw;activePartFilter=previousFilter;render();}
  },setFault:(mode: "none" | "mask" | "order" | "uv")=>{ diagnosticFault=mode;
  textures.forEach(t=>{t.flipY=mode==="uv"?false:true;t.needsUpdate=true;}); }};
 createProxyControls(()=>cameraYawDeg,setYaw);
 requestAnimationFrame(tick);
}
function render(){
 const native=(window as any).__R1999_MODEL;
 if(!native?.getModel?.() || !native?.getRenderer?.())return;
 const mvpArray=native.getRenderer().getMvpMatrix().getArray();
 const matrix=new THREE.Matrix4().fromArray(Array.from(mvpArray));
 for(const o of objects){
  updateGeo(o.geometry,o.index);
  o.material.uniforms.uMvp.value.copy(matrix);
  o.material.uniforms.uYaw.value=cameraYawDeg*Math.PI/180;
  o.material.uniforms.uPivot.value.set(...headPivot);
  o.material.uniforms.uOpacity.value=model.getDrawableOpacity(o.index);
  o.material.uniforms.uHasMask.value=o.maskIndices.length>0 && diagnosticFault!=="mask"?1:0;
  o.mesh.visible=model.getDrawableDynamicFlagIsVisible(o.index);
 }
 for(const {target,scene} of maskCache.values()){
  for(const mesh of scene.children as THREE.Mesh[]){
   const m=mesh.material as THREE.ShaderMaterial;
   const idx=objects.find(o=>o.geometry===mesh.geometry)?.index ?? -1;
   m.uniforms.uMvp.value.copy(matrix);
   m.uniforms.uYaw.value=cameraYawDeg*Math.PI/180;
   m.uniforms.uPivot.value.set(...headPivot);
   m.uniforms.uOpacity.value=idx>=0?model.getDrawableOpacity(idx):1;
  }
  app.setRenderTarget(target);
  app.clear();
  app.render(scene,unitCamera);
 }
 app.setRenderTarget(null);
 app.clear();
 const sorted=objects.slice().sort((a,b)=>
   diagnosticFault==="order"? b.index-a.index :
   model.getDrawableRenderOrders()[a.index]-model.getDrawableRenderOrders()[b.index]);
 // Render one at a time to preserve Cubism's dynamically evaluated ordering.
 for(const o of sorted){
  if(!o.mesh.visible)continue;
  if(activePartFilter && !activePartFilter.has(model.getDrawableParentPartIndex(o.index)))continue;
  const group=maskCache.get(o.key);
  o.material.uniforms.uMask.value=group?.target.texture ?? null;
  app.render(o.mesh,unitCamera);
 }
}
function tick(){
 try{render();}catch(e){console.error('C03 Three adapter',e);(window as any).__R1999_ADAPTER_ERROR=String(e);return;}
 requestAnimationFrame(tick);
}
const boot=()=>{if((window as any).__R1999_MODEL?.getModel?.())begin();
 else setTimeout(boot,300);};
boot();
