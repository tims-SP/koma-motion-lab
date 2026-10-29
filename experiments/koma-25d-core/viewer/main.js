import * as THREE from 'three';
const canvasW=960,canvasH=540;
let camera,renderer,model,angle=0,pose=0;
const query=new URLSearchParams(location.search);
const initialAngle=Number(query.get('angle')||0);
const initialPose=Number(query.get('pose')||0);
const $=(id)=>document.getElementById(id);

async function setup(){
  const [doc,tex]=await Promise.all([
    fetch('/asset/character.json').then(r=>{if(!r.ok)throw Error('missing Koma JSON');return r.json()}),
    new THREE.TextureLoader().loadAsync('/asset/gBot.png')
  ]);
  tex.colorSpace=THREE.SRGBColorSpace;
  tex.magFilter=THREE.LinearFilter; tex.minFilter=THREE.LinearMipmapLinearFilter;
  const scene=new THREE.Scene();
  scene.background=new THREE.Color('#f2f4f8');
  const bones=doc.bones.map(b=>{const bone=new THREE.Bone(); bone.name=b.path;bone.position.set(...b.local);return bone});
  for(let i=0;i<bones.length;i++){
    const parent=doc.bones[i].parent;
    if(parent>=0)bones[parent].add(bones[i]);
    else scene.add(bones[i]);
  }
  scene.updateMatrixWorld(true);
  const skeleton=new THREE.Skeleton(bones);
  const mat=new THREE.MeshBasicMaterial({map:tex,transparent:true,alphaTest:0.02,
    depthWrite:true,side:THREE.DoubleSide});
  const proxyMaterial=new THREE.MeshBasicMaterial({color:0x8190a8,
    side:THREE.DoubleSide,depthWrite:true});
  let verts=0;
  for(const m of doc.meshes){
    const geometry=new THREE.BufferGeometry();
    const flat=a=>a.flat();
    geometry.setAttribute('position',new THREE.Float32BufferAttribute(flat(m.vertices),3));
    geometry.setAttribute('uv',new THREE.Float32BufferAttribute(flat(m.uv),2));
    geometry.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(flat(m.skinIndex),4));
    geometry.setAttribute('skinWeight',new THREE.Float32BufferAttribute(flat(m.skinWeight),4));
    geometry.setIndex(m.indices);
    geometry.computeVertexNormals();
    const skinned=new THREE.SkinnedMesh(geometry,mat);
    skinned.frustumCulled=false;
    skinned.renderOrder=m.layer*2+1;
    scene.add(skinned);
    skinned.bind(skeleton,new THREE.Matrix4());
    skinned.normalizeSkinWeights();
    if(m.shell){
      const g=new THREE.BufferGeometry();
      g.setAttribute('position',new THREE.Float32BufferAttribute(flat(m.shell.vertices),3));
      g.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(flat(m.shell.skinIndex),4));
      g.setAttribute('skinWeight',new THREE.Float32BufferAttribute(flat(m.shell.skinWeight),4));
      g.setIndex(m.shell.indices);
      g.computeVertexNormals();
      const proxy=new THREE.SkinnedMesh(g,proxyMaterial);
      proxy.frustumCulled=false;
      proxy.renderOrder=m.layer*2;
      scene.add(proxy);
      proxy.bind(skeleton,new THREE.Matrix4());
      proxy.normalizeSkinWeights();
    }
    verts+=m.vertices.length;
  }
  const [xb,yb]=doc.bounds;
  const midx=(xb[0]+xb[1])/2,midy=(yb[0]+yb[1])/2;
  const height=Math.max((yb[1]-yb[0])*1.35,(xb[1]-xb[0])*1.35*canvasH/canvasW,1);
  const width=height*canvasW/canvasH;
  camera=new THREE.OrthographicCamera(-width/2,width/2,height/2,-height/2,.1,100);
  renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
  renderer.setSize(canvasW,canvasH);
  renderer.setPixelRatio(1);
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  document.body.appendChild(renderer.domElement);
  model={scene,bones,center:new THREE.Vector3(midx,midy,0),doc,verts};
  $('status').textContent='Koma CORE-001 · MIT source mesh';
  $('detail').textContent=doc.meshes.length+' meshes / '+bones.length+
    ' bones / '+verts+' vertices · original UV';
  window.__komaDiagnostics={meshes:doc.meshes.length,bones:bones.length,verts,
    source:doc.source,sourceAnimationParity:'NOT_TESTED',newViews:'NOT_AVAILABLE'};
  window.__komaSetAngle=(a,p=pose)=>{
    angle=Number(a); pose=Number(p);
    for(const b of bones)b.rotation.set(0,0,0);
    const forearm=bones.find(b=>b.name.endsWith('/LeftForearm'));
    if(forearm && pose)forearm.rotation.x=THREE.MathUtils.degToRad(30)*pose;
    const rad=THREE.MathUtils.degToRad(angle);
    const distance=14;
    camera.position.copy(model.center).add(new THREE.Vector3(
      Math.sin(rad)*distance,0,Math.cos(rad)*distance));
    camera.lookAt(model.center);
    camera.updateProjectionMatrix();
    renderer.render(model.scene,camera);
    $('angle').textContent='Camera yaw '+angle.toFixed(1)+'° · Pose '+pose.toFixed(1);
    return true;
  };
  window.__komaSetAngle(initialAngle,initialPose);
  window.__komaReady=true;
}
setup().catch(err=>{console.error(err);$('status').textContent='FAILED · '+err.message;
  window.__komaError=String(err);});
