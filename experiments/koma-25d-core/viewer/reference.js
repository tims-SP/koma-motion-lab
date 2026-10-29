/**
 * CORE-004: image-backed multi-view ground truth from a separately licensed
 * CC0 anime VRM. This is a REFERENCE generator, not a reconstructed 2D rig.
 * GLTFLoader reads the VRM 0.x glTF container without reusing its specialized
 * native VRM extensions. Record that material rendering isn't VRM-runtime parity.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

async function setup(){
  const scene=new THREE.Scene();
  scene.background=new THREE.Color('#eff1f5');
  const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
  renderer.setSize(640,640);
  renderer.setPixelRatio(1);
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.NoToneMapping;
  document.body.appendChild(renderer.domElement);
  scene.add(new THREE.AmbientLight(0xffffff,2.0));
  const sun=new THREE.DirectionalLight(0xffffff,2.2);
  sun.position.set(2,4,6);
  scene.add(sun);
  const model=await new GLTFLoader().loadAsync('/asset/reference.vrm');
  scene.add(model.scene);
  const group=model.scene;
  group.updateMatrixWorld(true);
  const box=new THREE.Box3().setFromObject(group);
  const size=box.getSize(new THREE.Vector3());
  const center=box.getCenter(new THREE.Vector3());
  if(![size.x,size.y,size.z].every(Number.isFinite)||size.y<0.2)
    throw Error('Invalid CC0 model bounds '+JSON.stringify(size));
  const height=Math.max(size.y*1.25,size.x*1.4,1.0),aspect=1;
  const camera=new THREE.OrthographicCamera(-height*aspect/2,height*aspect/2,height/2,-height/2,.01,100);
  const radius=Math.max(3,size.length()*2);
  let meshes=0,triangles=0;
  group.traverse(o=>{
    if(o.isMesh||o.isSkinnedMesh){
      meshes++;
      if(o.geometry)triangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;
    }
  });
  if(meshes<2||triangles<100)throw Error('Model is not fully loaded');
  window.__referenceInfo={license:'CC0 VRoid Studio beta sample Sendagaya_Shino',
    source:'madjin/vrm-samples pinned GitHub revision',
    meshes,triangles:Math.round(triangles),bounds:size.toArray(),
    modelType:'REAL_3D_REFERENCE_NOT_2D_CONVERSION',
    loader:'GLTFLoader_NOT_FULL_VRM_MTOON'};
  window.__renderReference=(angle)=>{
    // Model's canonical -Z face is toward viewer at yaw=0.
    const rad=THREE.MathUtils.degToRad(angle+180);
    camera.position.set(center.x+radius*Math.sin(rad),center.y,center.z+radius*Math.cos(rad));
    camera.lookAt(center);
    camera.updateProjectionMatrix();
    renderer.render(scene,camera);
  };
  window.__renderReference(0);
  window.__referenceReady=true;
}
setup().catch(e=>{console.error(e);window.__referenceError=e.message;});
