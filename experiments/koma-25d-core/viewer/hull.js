/**
 * CORE-005 viewer: real curved 3D mesh constructed from exactly two 2D PNG
 * silhouettes. Source front/side/back PNG images are projected from world
 * space. A matching naive 2D silhouette extrusion is the geometry control.
 *
 * Source full 3D VRM is NEVER loaded into this viewer.
 */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

async function setup(){
 const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
 renderer.setPixelRatio(1);
 renderer.setSize(640,640);
 renderer.setClearColor('#eff1f5');
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.toneMapping=THREE.NoToneMapping;
 document.body.appendChild(renderer.domElement);
 const camera=new THREE.OrthographicCamera(-1,1,1,-1,0.05,100);
 const loader=new THREE.TextureLoader();
 const [front,side,back,meta]=await Promise.all([
   loader.loadAsync('/asset/front.png'),
   loader.loadAsync('/asset/side.png'),
   loader.loadAsync('/asset/back.png'),
   fetch('/asset/hull_meta.json').then(r=>{if(!r.ok)throw Error('missing 2D-hull metadata');return r.json()})
 ]);
 if(meta.source_reconstruction_uses_original_3d_mesh!==false ||
    meta.input_kind!=='RENDERED_2D_IMAGE_VIEWS_ONLY')throw Error('Provenance mismatch');
 for(const tex of [front,side,back]){
  tex.colorSpace=THREE.SRGBColorSpace;
  tex.wrapS=THREE.ClampToEdgeWrapping;
  tex.wrapT=THREE.ClampToEdgeWrapping;
  tex.magFilter=THREE.LinearFilter;
  tex.minFilter=THREE.LinearMipmapLinearFilter;
 }
 const material=new THREE.ShaderMaterial({
  uniforms:{frontTex:{value:front},sideTex:{value:side},backTex:{value:back}},
  vertexShader:`
    varying vec3 vObj;
    varying vec3 vNorm;
    void main(){
      vObj=position;
      vNorm=normalize(normalMatrix*normal);
      gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);
    }
  `,
  fragmentShader:`
    uniform sampler2D frontTex;
    uniform sampler2D sideTex;
    uniform sampler2D backTex;
    varying vec3 vObj;
    varying vec3 vNorm;
    void main(){
      vec2 uvF=clamp(vec2(0.5-vObj.x*0.5,0.5+vObj.y*0.5),0.001,0.999);
      vec2 uvS=clamp(vec2(0.5-vObj.z*0.5,0.5+vObj.y*0.5),0.001,0.999);
      vec2 uvB=clamp(vec2(0.5+vObj.x*0.5,0.5+vObj.y*0.5),0.001,0.999);
      vec3 a=texture2D(frontTex,uvF).rgb;
      vec3 b=texture2D(sideTex,uvS).rgb;
      vec3 c=texture2D(backTex,uvB).rgb;
      vec3 n=normalize(vNorm);
      // Surface-based projection, NOT whole-image crossfade.
      float wf=pow(max(-n.z,0.0),3.0)+0.002;
      float ws=pow(abs(n.x),3.0)+0.002;
      float wb=pow(max(n.z,0.0),3.0)+0.002;
      vec3 col=(wf*a+ws*b+wb*c)/(wf+ws+wb);
      gl_FragColor=vec4(col,1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }
  `,
  side:THREE.DoubleSide,depthTest:true,depthWrite:true
 });
 const l=new GLTFLoader();
 const models={};
 for(const name of ['visual_hull','fixed_extrusion']){
  const gltf=await l.loadAsync('/asset/'+name+'.glb');
  const m=gltf.scene;
  m.traverse(n=>{
   if(n.isMesh){
    n.material=material;
    n.frustumCulled=false;
   }
  });
  models[name]=m;
 }
 const scene=new THREE.Scene();
 scene.background=new THREE.Color('#eff1f5');
 scene.add(models.visual_hull);
 scene.add(models.fixed_extrusion);
 models.fixed_extrusion.visible=false;
 window.__hullSetPose=({name='visual_hull',yaw=0}={})=>{
  if(!models[name])throw Error('Unknown geometry '+name);
  for(const [key,mesh] of Object.entries(models))mesh.visible=key===name;
  const a=THREE.MathUtils.degToRad(yaw);
  camera.position.set(4*Math.sin(a),0,-4*Math.cos(a));
  camera.lookAt(0,0,0);
  camera.updateProjectionMatrix();
  renderer.render(scene,camera);
  return {name,yaw};
 };
 window.__hullInfo={
  algorithm:meta.geometry_algorithm,
  grid:meta.grid_yxz,
  modelData:meta.assets,
  original2DArt:meta.source_art_is_original_layered_live2d,
  source3DMeshUsed:meta.source_reconstruction_uses_original_3d_mesh,
  rig:meta.rig
 };
 window.__hullSetPose({name:'visual_hull',yaw:0});
 window.__hullReady=true;
}
setup().catch(e=>{console.error(e);window.__hullError=e.message});
