/**
 * CORE-005: use explicit UVs + Three.MeshBasicMaterial. Earlier custom
 * ShaderMaterial rendered BLACK despite silhouette geometry QA passing.
 * This approach reuses the renderer's proven normal texture sampling path.
 *
 * The glTF geometry here is generated ONLY from 2D image silhouettes.
 */
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

function mapUVsPerTriangle(geometry){
  const nonindexed=geometry.index?geometry.toNonIndexed():geometry.clone();
  const pos=nonindexed.getAttribute('position');
  if(!pos || pos.count%3!==0)throw Error('Invalid triangle surface');
  const coords=new Float32Array(pos.count*2);
  const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
  const n=new THREE.Vector3();
  const x1=new THREE.Vector3(),x2=new THREE.Vector3();
  const faceTypes=[0,0,0];
  for(let i=0;i<pos.count;i+=3){
    a.fromBufferAttribute(pos,i);
    b.fromBufferAttribute(pos,i+1);
    c.fromBufferAttribute(pos,i+2);
    n.copy(x1.subVectors(b,a).cross(x2.subVectors(c,a))).normalize();
    // Source cameras: front at -Z; side at +X; back at +Z.
    let slot;
    if(Math.abs(n.x)>Math.abs(n.z)*0.75)slot=1;
    else slot=n.z<=0?0:2;
    faceTypes[slot]++;
    for(let k=0;k<3;k++){
      const x=pos.getX(i+k),y=pos.getY(i+k),z=pos.getZ(i+k);
      const originalU=slot===0?0.5-x*0.5:slot===1?0.5-z*0.5:0.5+x*0.5;
      const originalV=0.5+y*0.5;
      const u=0.002+0.996*THREE.MathUtils.clamp(originalU,0,1);
      const v=0.002+0.996*THREE.MathUtils.clamp(originalV,0,1);
      coords[(i+k)*2]=(slot+u)/3;
      coords[(i+k)*2+1]=v;
    }
  }
  nonindexed.setAttribute('uv',new THREE.BufferAttribute(coords,2));
  return {geometry:nonindexed,facesByProjection:faceTypes};
}

async function setup(){
 const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
 renderer.setPixelRatio(1);
 renderer.setSize(640,640);
 renderer.setClearColor('#eff1f5');
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.toneMapping=THREE.NoToneMapping;
 document.body.appendChild(renderer.domElement);
 const camera=new THREE.OrthographicCamera(-1,1,1,-1,0.05,100);
 const [atlas,meta]=await Promise.all([
  new THREE.TextureLoader().loadAsync('/asset/atlas.png'),
  fetch('/asset/hull_meta.json').then(r=>{if(!r.ok)throw Error('missing 2D-hull metadata');return r.json()})
 ]);
 if(meta.source_reconstruction_uses_original_3d_mesh!==false ||
    meta.input_kind!=='RENDERED_2D_IMAGE_VIEWS_ONLY')throw Error('Provenance mismatch');
 atlas.colorSpace=THREE.SRGBColorSpace;
 atlas.wrapS=THREE.ClampToEdgeWrapping;
 atlas.wrapT=THREE.ClampToEdgeWrapping;
 atlas.magFilter=THREE.LinearFilter;
 atlas.minFilter=THREE.LinearMipmapLinearFilter;
 if(atlas.image?.width!==1920 || atlas.image?.height!==640)
    throw Error('Invalid 3-view texture atlas');
 const material=new THREE.MeshBasicMaterial({
  map:atlas,side:THREE.DoubleSide,depthTest:true,depthWrite:true
 });
 const matteMaterial=new THREE.MeshBasicMaterial({color:0x000000,side:THREE.DoubleSide});
 const loader=new GLTFLoader();
 const models={},stats={};
 for(const name of ['visual_hull','fixed_extrusion']){
  const gltf=await loader.loadAsync('/asset/'+name+'.glb');
  const m=gltf.scene;
  let totalFaces=0,projection=[0,0,0];
  m.traverse(o=>{
    if(o.isMesh){
      const mapped=mapUVsPerTriangle(o.geometry);
      o.geometry.dispose();
      o.geometry=mapped.geometry;
      o.material=material;
      o.frustumCulled=false;
      totalFaces+=mapped.geometry.getAttribute('position').count/3;
      projection=projection.map((x,i)=>x+mapped.facesByProjection[i]);
    }
  });
  if(totalFaces<150 || !projection.every(Number.isFinite))
    throw Error('Empty projection/geometry for '+name);
  stats[name]={triangles:totalFaces,projections:projection};
  models[name]=m;
 }
 const scene=new THREE.Scene();
 scene.background=new THREE.Color('#eff1f5');
 scene.add(models.visual_hull);
 scene.add(models.fixed_extrusion);
 models.fixed_extrusion.visible=false;
 window.__hullSetPose=({name='visual_hull',yaw=0,matte=false}={})=>{
  if(!models[name])throw Error('Unknown geometry '+name);
  for(const [key,mesh] of Object.entries(models)){
    mesh.visible=key===name;
    if(mesh.visible)mesh.traverse(o=>{if(o.isMesh)o.material=matte?matteMaterial:material;});
  }
  const angle=THREE.MathUtils.degToRad(yaw);
  camera.position.set(4*Math.sin(angle),0,-4*Math.cos(angle));
  camera.lookAt(0,0,0);
  camera.updateProjectionMatrix();
  renderer.render(scene,camera);
  return {name,yaw,matte};
 };
 window.__hullInfo={
  algorithm:meta.geometry_algorithm,grid:meta.grid_yxz,modelData:meta.assets,
  source3DMeshUsed:meta.source_reconstruction_uses_original_3d_mesh,
  original2DArt:meta.source_art_is_original_layered_live2d,
  atlasSize:[atlas.image.width,atlas.image.height],
  shader:'STANDARD_MESH_BASIC_WITH_PER_TRIANGLE_VIEW_UV',
  projections:stats,rig:meta.rig
 };
 window.__hullSetPose({name:'visual_hull',yaw:0});
 window.__hullReady=true;
}
setup().catch(e=>{console.error(e);window.__hullError=e.message;});
