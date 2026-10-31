import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {VRMLoaderPlugin} from '@pixiv/three-vrm';
const contract = await (await fetch('/contract.json')).json();
const renderer = new THREE.WebGLRenderer({antialias:false, alpha:false, preserveDrawingBuffer:true});
renderer.setSize(contract.camera.width,contract.camera.height);
renderer.setPixelRatio(1);renderer.setClearColor(0x000000,1);
renderer.toneMapping=THREE.NoToneMapping;
document.body.append(renderer.domElement);
const scene=new THREE.Scene();
const loader=new GLTFLoader();loader.register(parser=>new VRMLoaderPlugin(parser));
const gltf=await loader.loadAsync('/out/source/reference.vrm');
const vrm=gltf.userData.vrm;
scene.add(vrm.scene);vrm.update(0);vrm.scene.updateMatrixWorld(true);
const head=vrm.humanoid.getRawBoneNode('head');
if(!head)throw new Error('No genuine source humanoid head joint');
const headJoint=head.getWorldPosition(new THREE.Vector3());
const target=headJoint.clone().add(new THREE.Vector3(...contract.camera.target_offset_m));
const pivot=new THREE.Group();scene.remove(vrm.scene);scene.add(pivot);pivot.add(vrm.scene);
pivot.position.copy(target);vrm.scene.position.sub(target);
const span=contract.camera.vertical_span_m;
const camera=new THREE.OrthographicCamera(-span/2,span/2,span/2,-span/2,contract.camera.near_m,contract.camera.far_m);
camera.position.copy(target).add(new THREE.Vector3(0,0,2));camera.lookAt(target);camera.updateMatrixWorld(true);
scene.add(new THREE.HemisphereLight(0xffffff,0x777777,2));
const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(0,2,3);scene.add(light);
const sources=[];
vrm.scene.traverse(o=>{if(o.isMesh){sources.push({mesh:o,materials:o.material});o.frustumCulled=false;}});
const categories=['Body','Face','Hair'];
function category(o){return categories.find(x=>o.name.toLowerCase().includes(x.toLowerCase()))||'Unknown';}
if(sources.some(o=>category(o.mesh)==='Unknown'))throw new Error('Unmapped source mesh');
// HEAD_ONLY source selection; source body and rest-pose arms are not head structure.
for(const {mesh} of sources)mesh.visible=category(mesh)!=='Body';
const mats={};
for(const {mesh} of sources){
  const colors={Body:0xff0000,Face:0x00ff00,Hair:0x0000ff};
  mats[mesh.uuid]={};
  for(const pass of ['silhouette','depth','normal','part_id']){
    const originals=Array.isArray(mesh.material)?mesh.material:[mesh.material];
    mats[mesh.uuid][pass]=originals.map(original=>{
      // Match alpha cutouts and sides of the actual source, including hair cards.
      const m=pass==='normal'?new THREE.MeshNormalMaterial():new THREE.MeshBasicMaterial({color:pass==='part_id'?colors[category(mesh)]:0xffffff});
      m.side=original.side;m.map=original.map;m.alphaMap=original.alphaMap;m.alphaTest=original.alphaTest;
      m.transparent=false;m.depthWrite=true;m.toneMapped=false;
      // onBeforeCompile closures have the same function text; include compiled constants.
      m.customProgramCacheKey=()=>`koma-${pass}-${category(mesh)}`;
      if(pass==='silhouette'||pass==='part_id'){
        const c=new THREE.Color(pass==='silhouette'?0xffffff:colors[category(mesh)]);
        m.onBeforeCompile=shader=>{
          shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',`#include <opaque_fragment>\ngl_FragColor.rgb = vec3(${c.r.toFixed(8)},${c.g.toFixed(8)},${c.b.toFixed(8)});`);
        };
      }
      if(pass==='depth'){
        m.onBeforeCompile=shader=>{
          shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying float komaDepth;').replace('#include <project_vertex>','#include <project_vertex>\nkomaDepth = -mvPosition.z;');
          shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying float komaDepth;').replace('#include <opaque_fragment>',`#include <opaque_fragment>\ngl_FragColor.rgb = vec3(1.0 - clamp((komaDepth - ${camera.near.toFixed(6)}) / ${(camera.far-camera.near).toFixed(6)}, 0.0, 1.0));`);
        };
      }
      return m;
    });
  }
}
const gl=renderer.getContext();const debug=gl.getExtension('WEBGL_debug_renderer_info');
window.factory={
  contract, metadata:{three:THREE.REVISION,renderer:debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),headJoint:headJoint.toArray(),cameraTarget:target.toArray(),selection:'Face and Hair source meshes; Body excluded for HEAD_ONLY',meshCount:sources.length,sourceMeshes:sources.map(s=>({name:s.mesh.name,category:category(s.mesh),visible:s.mesh.visible,vertices:s.mesh.geometry.attributes.position.count})),cameraMatrix:camera.matrixWorld.toArray(),projectionMatrix:camera.projectionMatrix.toArray()},
  render(yaw,pass){
    if(!['beauty','silhouette','depth','normal','part_id'].includes(pass))throw new Error('Unknown pass');
    pivot.rotation.y=THREE.MathUtils.degToRad(yaw);pivot.updateMatrixWorld(true);
    for(const s of sources)s.mesh.material=pass==='beauty'?s.materials:(Array.isArray(s.materials)?mats[s.mesh.uuid][pass]:mats[s.mesh.uuid][pass][0]);
    renderer.outputColorSpace=pass==='beauty'?THREE.SRGBColorSpace:THREE.LinearSRGBColorSpace;
    renderer.render(scene,camera);
    const landmarks={};
    for(const name of ['head','neck','leftEye','rightEye']){
      const node=vrm.humanoid.getRawBoneNode(name);if(!node)continue;
      const world=node.getWorldPosition(new THREE.Vector3());const ndc=world.clone().project(camera);
      // Projection is recorded; these joint anchors are NOT visibility-tested surface landmarks.
      landmarks[name]={world:world.toArray(),pixel:[(ndc.x+1)*256,(1-ndc.y)*256],visibility:'NOT_TESTED'};
    }
    return {yaw_deg:yaw,pass,characterMatrix:pivot.matrixWorld.toArray(),landmarks};
  }
};
window.factoryReady=true;
