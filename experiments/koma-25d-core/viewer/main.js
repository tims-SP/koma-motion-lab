import * as THREE from 'three';
const canvasW=960,canvasH=540;
let camera,renderer,model,angle=0,pose=0;
const SOURCE_SCALE=0.012;
const query=new URLSearchParams(location.search);
const initialAngle=Number(query.get('angle')||0);
const initialPose=Number(query.get('pose')||0);
const $=(id)=>document.getElementById(id);

async function setup(){
  const [doc,tex]=await Promise.all([
    fetch('/asset/character.json').then(r=>{if(!r.ok)throw Error('missing Koma JSON');return r.json()}),
    new THREE.TextureLoader().loadAsync('/asset/gBot.png')
  ]);
  const appearance=await fetch('/asset/appearance.json').then(r=>{if(!r.ok)throw Error('appearance manifest missing');return r.json();});
  if(appearance.production_accepted!==false)throw Error('Diagnostic canary provenance must be non-production');
  const loadCanary=async (record)=>{
    if(!['SYNTHETIC_DIAGNOSTIC_ONLY','REGISTERED_UNREVIEWED'].includes(record.provenance))
      throw Error('Unverified view registration: '+record.provenance);
    const image=await new THREE.TextureLoader().loadAsync('/asset/'+record.texture);
    image.colorSpace=THREE.SRGBColorSpace;
    image.magFilter=THREE.LinearFilter;
    image.minFilter=THREE.LinearMipmapLinearFilter;
    return image;
  };
  const [sideTexture,backTexture]=await Promise.all([
    loadCanary(appearance.side),loadCanary(appearance.back)
  ]);
  tex.colorSpace=THREE.SRGBColorSpace;
  tex.magFilter=THREE.LinearFilter; tex.minFilter=THREE.LinearMipmapLinearFilter;
  const scene=new THREE.Scene();
  scene.background=new THREE.Color('#f2f4f8');
  const bones=doc.bones.map(b=>{
    const bone=new THREE.Bone();
    bone.name=b.path;
    bone.position.set(...b.local);
    bone.rotation.z=-Number(b.restRotation||0);
    return bone;
  });
  for(let i=0;i<bones.length;i++){
    const parent=doc.bones[i].parent;
    if(parent>=0)bones[parent].add(bones[i]);
    else scene.add(bones[i]);
  }
  scene.updateMatrixWorld(true);
  const skeleton=new THREE.Skeleton(bones);
  const mat=new THREE.MeshBasicMaterial({map:tex,transparent:true,alphaTest:0.02,
    depthWrite:true,side:THREE.DoubleSide});
  const diagnosticMaterials={
    side:new THREE.MeshBasicMaterial({map:sideTexture,side:THREE.DoubleSide,depthWrite:true}),
    back:new THREE.MeshBasicMaterial({map:backTexture,side:THREE.DoubleSide,depthWrite:true})
  };
  const proxyMeshes=[];
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
      for(const role of ['side','back']){
        const shell=m.shell;
        const attr=role==='side'?'sideUv':'backUv';
        const index=role==='side'?'sideIndices':'rearIndices';
        if(!shell[attr] || !shell[index])throw Error('Missing '+role+' view geometry');
        const g=new THREE.BufferGeometry();
        g.setAttribute('position',new THREE.Float32BufferAttribute(flat(shell.vertices),3));
        g.setAttribute('uv',new THREE.Float32BufferAttribute(flat(shell[attr]),2));
        g.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(flat(shell.skinIndex),4));
        g.setAttribute('skinWeight',new THREE.Float32BufferAttribute(flat(shell.skinWeight),4));
        g.setIndex(shell[index]);
        g.computeVertexNormals();
        const proxy=new THREE.SkinnedMesh(g,diagnosticMaterials[role]);
        proxy.frustumCulled=false;
        proxy.renderOrder=m.layer*2;
        scene.add(proxy);
        proxy.bind(skeleton,new THREE.Matrix4());
        proxy.normalizeSkinWeights();
        proxyMeshes.push(proxy);
      }
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
  model={scene,bones,center:new THREE.Vector3(midx,midy,0),doc,verts,proxyMeshes,appearance};
  window.__komaViewMode='diagnostic';
  $('status').textContent='Koma CORE-001 · MIT source mesh';
  $('detail').textContent=doc.meshes.length+' meshes / '+bones.length+
    ' bones / '+verts+' vertices · original UV';
  window.__komaDiagnostics={meshes:doc.meshes.length,bones:bones.length,verts,
    source:doc.source,sourceAnimationParity:'RAW_CLIPS_ONLY',
    newViews:appearance.side.provenance,appearanceProvenance:appearance.side.provenance,
    clips:Object.keys(doc.clips||{})};
  const lerpKeys=(track,t)=>{
    const {times,values}=track;
    if(t<=times[0])return values[0];
    for(let i=1;i<times.length;i++){
      if(t<=times[i]){
        const f=(t-times[i-1])/(times[i]-times[i-1]||1);
        const a=values[i-1],b=values[i];
        if(Array.isArray(a))return a.map((v,k)=>v+(b[k]-v)*f);
        return a+(b-a)*f;
      }
    }
    return values[values.length-1];
  };
  window.__komaSetMotion=({yaw=0,clip=null,time=0,reach=0}={})=>{
    angle=Number(yaw);pose=Number(reach);
    for(let i=0;i<bones.length;i++){
      bones[i].position.set(...doc.bones[i].local);
      bones[i].rotation.set(0,0,-Number(doc.bones[i].restRotation||0));
    }
    if(clip){
      const act=doc.clips?.[clip];
      if(!act)throw Error('Source clip missing: '+clip);
      const localT=((Number(time)%act.duration)+act.duration)%act.duration;
      for(const track of act.tracks){
        const b=bones[track.bone];
        const value=lerpKeys(track,localT);
        if(track.property==='rotation_degrees')b.rotation.z=THREE.MathUtils.degToRad(-value);
        if(track.property==='position')b.position.set(value[0]*SOURCE_SCALE,-value[1]*SOURCE_SCALE,0);
      }
    }
    // Spatial-axis test, intentionally outside the original 2D Godot controls.
    // This does NOT claim original animation equivalence.
    const upper=bones.find(b=>b.name.endsWith('/RightArm'));
    const lower=bones.find(b=>b.name.endsWith('/RightForearm'));
    if(upper&&reach)upper.rotation.y=THREE.MathUtils.degToRad(34)*reach;
    if(lower&&reach)lower.rotation.x=THREE.MathUtils.degToRad(51)*reach;
    model.scene.updateMatrixWorld(true);
    const rad=THREE.MathUtils.degToRad(angle),distance=14;
    camera.position.copy(model.center).add(new THREE.Vector3(
      Math.sin(rad)*distance,0,Math.cos(rad)*distance));
    camera.lookAt(model.center);
    camera.updateProjectionMatrix();
    renderer.render(model.scene,camera);
    $('angle').textContent='Camera '+angle.toFixed(1)+'° · '+(clip||'spatial')+
      ' · '+Number(time).toFixed(2)+'s · Reach '+reach.toFixed(2);
    return {yaw,clip,time,reach};
  };
  window.__komaSetAngle=(a,p=pose)=>window.__komaSetMotion({yaw:a,reach:p});
  window.__komaSetViewMode=(mode)=>{
    if(!['diagnostic','source-front'].includes(mode))throw Error('Unknown view mode');
    window.__komaViewMode=mode;
    for(const mesh of model.proxyMeshes)mesh.visible=(mode==='diagnostic');
  };
  window.__komaClipNames=Object.keys(doc.clips||{});
  window.__komaSetMotion({yaw:initialAngle,reach:initialPose});
  window.__komaReady=true;
}
setup().catch(err=>{console.error(err);$('status').textContent='FAILED · '+err.message;
  window.__komaError=String(err);});
